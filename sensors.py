#!/usr/bin/env python3
import configparser
import requests
import re
import json
from datetime import datetime
import sqlite3
import sys, getopt

def usage():
    print("sensor.py [-c <configFile>]")
    print("   configFile - Defalts to rvwhisper.ini")
   

def main(argv):

    configFile = 'rvwhisper.ini'
    try:
        opts, args = getopt.getopt(argv, "c", ["config="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-c", "--config"):
            configFile = arg
         
    print("Reading %s" % configFile)
    config = configparser.ConfigParser()
    config.read('rvwhisper.ini')

    print("Reading parameters for %s" % config['RVWHISPER']['id'])

    bt_basic_ajax = 'https://access.rvwhisper.com/%s/wp-admin/admin-ajax.php'

    httpSession = requests.Session()
    # First we have to login.
    data = dict()
    # First pull the initial login page and extract the required CSRF Tokens
    print("-> Fetching login page")
    r = httpSession.get('https://access.rvwhisper.com/')
    r.raise_for_status()

    p = re.compile('<input type="hidden" name="csrf_value" value="(\w+)"')
    data['csrf_value'] = p.search(r.text).group(1)
    p = re.compile('<input type="hidden" name="csrf_name" value="(\w+)"')
    data['csrf_name'] = p.search(r.text).group(1)

    # Now fetch our Authentication Info and login to generate the required cookies
    data['user_name'] = config['AUTH']['username']
    data['password'] = config['AUTH']['password']
    data['rememberme'] = '0'
    print("-> Logging in...")
    r = httpSession.post('https://access.rvwhisper.com/account/login', data = data)
    r.raise_for_status()

    # ok, now we are logged in.. Fetch the dashboard and retrieve the Nonce and UserID

    print("-> Fetching dashboard")
    r = httpSession.get('https://access.rvwhisper.com/%s' % config['RVWHISPER']['id'])
    try:
        r.raise_for_status()
    except:
        print(r.text)
        p = re.compile("<title>(.*)</title>")
        with open("status.sh", "w") as f:
            f.write('echo "%s"\n' % (p.search(r.text).group(1)))
            f.write("exit 2;")
        sys.exit(-2)

    with open("status.sh", "w") as f:
        f.write('echo "RVWhisper is online"\n')
        f.write("exit 0;")

    p = re.compile('"ajax_nonce":"(\w+)"')
    ajax_nonce = p.search(r.text).group(1)
    print("Nonce is %s" % ajax_nonce)

    # Also retrieve the basic list of sensors & ID's
    p = re.compile('sensor\?sensor_id=(\d+)" title="([\w\s]+)"')
    sensors = dict()
    iterator = p.finditer(r.text)
    for match in iterator:
        print("-> Found sensor: %s (ID: %s)" % (match.group(2), match.group(1)))
        sensors[match.group(2)] = match.group(1)

    for sensor in sensors.keys():
    # # retrieve data for a sensor
        data = dict()
        data['action'] = 'get_latest_data_by_date'
        data['sensor'] = sensors[sensor]
        data['date_interval'] = config.get('SENSORS', 'duration', fallback = 1)
        data['browser_gmt_offset'] = -4
        data['charting'] = 'false'
        data['bt_nonce'] = ajax_nonce

        db = None
        print("-> Creating DB for sensor %s" % sensors[sensor])
        try:
            db = sqlite3.connect("%s.db" % sensor)
        except sqlite3.Error as e:
            print(e)
        
        print("-> Fetching data for sensor '%s' (%s)" % (sensor, sensors[sensor]))
        r = httpSession.post('https://access.rvwhisper.com/%s/wp-admin/admin-ajax.php' % config['RVWHISPER']['id'], data = data)
        r.raise_for_status()
        data = json.loads(r.text)

        if (config['DEBUG']['printjson'] == '1'):
            json_str = json.dumps(data, indent=4)
            print(json_str)
        if (config['DEBUG']['savejson'] == '1'):
            filename = 'json/%s.json' % sensor
            print('---> Writing to %s' % filename)
            f = open(filename, 'w')
            json_str = json.dumps(data, indent=4)
            f.write(json_str)
            f.close()

        # These are the only fields we care about (Except for TimeStamp)
        ImportantFields = config.get("SENSORS", "fields", fallback="DegreesF,PercentHumidity,Volts,DoorState").split(',')
        print("Reading fields %s" % ImportantFields)

        # Start by finding how many of these "Important Fields" are in this dataset
        NumFields = int(data['num_fields'])
        FieldsRead = []
        for i in range(1,NumFields+1):
            fieldName = data['read_field']['read_field_%i' % i][0]
            if (fieldName in ImportantFields):
                print("[Field %i] = %s" % (i, fieldName))
                FieldsRead.append(fieldName)
            else:
                print("[Field %i] = %s (Skipped)" % (i, fieldName))
        
        # So if we found fields to read, verify the DB exists
        if ((db) and (len(FieldsRead) > 0)):
            try:
                c = db.cursor()
                c.execute("""CREATE TABLE IF NOT EXISTS data (
                                timestamp integer,
                                fieldname text,
                                value text,
                                PRIMARY KEY (timestamp, fieldname));""")
            except sqlite3.Error as e:
                print(e)

            # Now iterate over all the data in this fetch, and find the important fields    
            for row in data['latest_points']:
                for field in FieldsRead:
                    try:
                        c = db.cursor()
                        c.execute("""INSERT INTO data(timestamp, fieldname, value) 
                                        VALUES(?,?,?)""", 
                                    (row['TimeStamp'], field, row[field]))
                        db.commit()
                    except sqlite3.Error as e:
                        print(e)
        else:
            print("*** No valid data fields found!")

        # if the DB was opened, make sure to close it.
        if(db):
            db.close()



if __name__ == "__main__":
    main(sys.argv[1:])

