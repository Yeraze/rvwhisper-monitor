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

    with open(outFile, 'w') as F:
        F.write("""<html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.5.0"></script>
        <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.1.1"></script>
        <title>RVWhisper Solar Graph</title>
    </head>
    <body>""");
        F.write(analyze(inFile, inWeather))
        F.write("</body></html>")


def analyze(inFile, inWeather):

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


    lstLabels = list()
    lstDaylight = list()
    lstPeak = list()
    lstSustained = list()

    for day in rows:

        secDaylight = 0
        secPeak = 0
        secSustained = 0

        sunrise = int(day[1])
        sunset = int(day[2])

        secDaylight = sunset - sunrise
        # So for the daylight period of the day, find the following.
        # The battery will rise up to just over 14V as the charging begins.  I'm calling this "Peak Charge", peak charging efficiency.
        # Once the battery has hit a certain point of charge, the voltage will drop and plateau in teh 13V range and hold there. I call this 
        #  "sustained" charge, as it's really just keeping the battery voltage high and offsetting any continuous drain (like the RVWhisper)
        # As the sun sets & the solar panel loses efficiency, it drops down to "normal battery levels, under 13V        

        # OVer multiple days, you'll see "Peak Charge" time drop (as the battery starts the day at a higher charge every day), and the "Sustained" 
        # charge time grow, as it's just holding the battery in a good state.

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
            secPeak = voltsOver14[0][1] - voltsOver14[0][0]

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
                secSustained = voltsOver13[0][1] - voltsOver13[0][0]
        
        lstLabels.append("'%s'" % day[0])
        lstDaylight.append(str(secDaylight))
        lstPeak.append(str(secPeak))
        lstSustained.append(str(secSustained))

    chartDaylight = """
        { type: 'bar',
          label: 'Hours of Daylight',
          stack: 'Stack 0',
          backgroundColor: 'rgba(255,0,0,0.25)',
          data: [""" + ','.join(lstDaylight) + "]}"
    chartPeak = """
        { type: 'bar',
          label: 'Peak Charge',
          stack: 'Stack 1',
          backgroundColor: 'green',
          data: [""" + ','.join(lstPeak) + "]}"
    chartSustained = """
        { type: 'bar',
          label: 'Sustained Charge',
          stack: 'Stack 1',
          backgroundColor: 'blue',
          data: [""" + ','.join(lstSustained) + "]}"

    result = """<canvas id="solarChart"></canvas>
        <script>
        solarData = {
            labels: [""" + ','.join(lstLabels) + "],"
    result = result + "datasets: [" \
            + chartDaylight + ","  \
            + chartPeak + ","  \
            + chartSustained + "]};"

    result = result + """
         function SecToTime(time) {
                totalSeconds = parseInt(time);
                _sec = totalSeconds % 60;
                _min = parseInt(totalSeconds / 60) % 60;
                _hour = parseInt(totalSeconds / 3600);
                var S =  _hour;
                if (_min < 10) {
                    S = S + ":0" +  _min;
                } else {
                    S = S + ":" + _min;
                }
                if (_sec < 10) {
                    S = S + ":0" + _sec;
                } else {
                    S = S + ":" + _sec;
                }
                return S;
         }
         const solarConfig = {
            type: 'bar',
            data: solarData,
            options: {
                scales: {
                    x: { stacked: true }, 
                    y: { stacked: true,
                        ticks: {
                            callback: function(label, index, labels) {
                                return SecToTime(label);
                            }
                        }
                    }
                },
                plugins: {
                    tooltip:  {
                        callbacks: {
                            label: function(context) {
                                var label = context.dataset.label || '';
                                label += ": " + SecToTime(context.parsed.y);
                                return label;
                            }
                        }
                    }
                }
            }
          };
          var chartSolar = new Chart(
            document.getElementById('solarChart'),
            solarConfig);
        </script>"""


    return result


if __name__ == "__main__":
    main(sys.argv[1:])
