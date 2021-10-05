#!/usr/bin/python3

import sys, getopt
import numpy
import sqlite3

def usage():
    print('solar.py -i <input SQLite DB> -o <output HTML file> -w <weather.db>')



def main(argv):
    inFile = ''
    inWeather = ''
    outFile = ''

    if len(argv) < 1:
        usage()
        sys.exit(2)

    try:
        opts, args = getopt.getopt(argv, "i:o:w:", ["input=", "output=", "weather="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)


    for opt, arg in opts:
        print("%s -> %s" % (opt,arg))
        if opt in ("-i", "--input"):
            inFile = arg
        elif opt in ("-o", "--output"):
            outFile = arg
        elif opt in ("-w", "--weather"):
            inWeather = arg


    # First off load the weather data to collect Sunrise & Sunset for every day
    print("Reading weather data from '%s'..." % inWeather)
    try:
        conn = sqlite3.connect(inWeather)
        c = conn.cursor()
        c.execute("select strftime('%Y-%m-%d', datetime(timestamp, 'unixepoch', 'localtime')) day, avg(sunrise), avg(sunset) from weather group by day order by day desc limit 60")
        rows = c.fetchall() 
        rows.reverse()
        conn.close()
    except sqlite3.Error as e:
        print(e)
        sys.exit(2)

    print("-> Loaded %i rows of weather data" % len(rows))

    for day in rows:
        print("Day %s : " % day[0])

if __name__ == "__main__":
    main(sys.argv[1:])
