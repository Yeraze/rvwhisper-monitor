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
        sunrise = int(day[1])
        sunset = int(day[2])

        secondsOfDaylight = sunset - sunrise

        print("Day %s : " % day[0])
        print("  Duration of daylight: %i:%02i:%02i" % (int(secondsOfDaylight / 3600), int(secondsOfDaylight / 60) % 60, secondsOfDaylight % 60))

        # So for the daylight period of the day, find the following.
        # The battery will rise up to just over 14V as the charging begins.
        # Once the battery has hit a certain point of charge, the voltage will drop and plateau in teh 13V range and hold there.
        # As the sun sets & the solar panel loses efficiency, it drops down to "normal battery levels, under 13V        


        try:
            conn = sqlite3.connect(inFile)
            c = conn.cursor()
            c.execute("""select min(timestamp), max(timestamp) from data where fieldname = 'Volts' 
                                                    and timestamp > %s 
                                                    and timestamp < %s 
                                                    and value > 14""" % (sunrise, sunset))
            voltsOver14 = c.fetchall()
            conn.close()

        except sqlite3.Error as e:
            print("Reading %s:" % inFile)
            print(e)
            sys.exit(2)

        if (len(voltsOver14) > 0) and (voltsOver14[0][1] is not None):
            secOver14 = voltsOver14[0][1] - voltsOver14[0][0]
            print("  Duration of Peak Charge: %i:%02i:%02i ( %i %%)" % (int(secOver14 / 3600), int(secOver14 / 60) % 60, secOver14 % 60, secOver14 * 100 / secondsOfDaylight))

            try:
                conn = sqlite3.connect(inFile)
                c = conn.cursor()
                c.execute("""select min(timestamp), max(timestamp) from data where fieldname = 'Volts' 
                                                        and timestamp > %s 
                                                        and timestamp < %s 
                                                        and value > 13""" % (voltsOver14[0][1], sunset))
                voltsOver13 = c.fetchall()
                conn.close()

            except sqlite3.Error as e:
                print("Reading %s:" % inFile)
                print(e)
                sys.exit(2)

            if (len(voltsOver13) > 0) and (voltsOver13[0][1] is not None):
                secOver13 = voltsOver13[0][1] - voltsOver13[0][0]
                print("  Duration of Sustained Charge: %i:%02i:%02i ( %i %%)" % (int(secOver13 / 3600), int(secOver13 / 60) % 60, secOver13 % 60, secOver13 * 100 / secondsOfDaylight))
            else:
                print("  Duration of Sustained Charge: 0:00:00 ( 0 %%)")
        else:
            print("  Duration of Peak Charge: 0:00:00 ( 0 %%)")




if __name__ == "__main__":
    main(sys.argv[1:])
