#!/usr/bin/python3

import sys, getopt
import numpy
import sqlite3

def usage():
    print('delta.py -i <input SQLite DB> -w <weather.db file> -o <output HTML file> [-d <Duration, Default -30 days>]')

def loadData(dbFile, field, duration):
    rows=[]
    try:
        conn = sqlite3.connect(dbFile)
        c = conn.cursor()
        c.execute('SELECT timestamp,value FROM data WHERE timestamp > strftime("%%s", datetime("now", "%s")) AND fieldname = "%s" ORDER BY timestamp' % (duration, field))
        rows = c.fetchall()
        conn.close()

    except sqlite3.Error as e:
        print(e)
        sys.exit(2)
        
    return rows


def main(argv):
    inFile = ''
    weatherFile = 'weather.db'
    outFile = ''
    duration = "-30 days"

    if len(argv) < 1:
        usage()
        sys.exit(2)

    try:
        opts, args = getopt.getopt(argv, "i:w:o:f:d:", ["input=", "weather=", "output=", "duration="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)


    for opt, arg in opts:
        if opt in ("-i", "--input"):
            inFile = arg
        elif opt in ("-w", "--input2"):
            weatherFile = arg
        elif opt in ("-o", "--output"):
            outFile = arg
        elif opt in ("-d", "--duration"):
            duration = arg

    # Load requested database
    print("-> Loading from %s" % inFile)
    rowsTemp = []
    rowsHumidity = []
    try:
        conn = sqlite3.connect(inFile)
        c = conn.cursor()
        c.execute('SELECT timestamp,value FROM data WHERE timestamp > strftime("%%s", datetime("now", "%s")) AND fieldname = "DegreesF" ORDER BY timestamp' % (duration))
        rowsTemp = c.fetchall()

        c.execute('SELECT timestamp,value FROM data WHERE timestamp > strftime("%%s", datetime("now", "%s")) AND fieldname = "PercentHumidity" ORDER BY timestamp' % (duration))
        rowsHumidity = c.fetchall()

        conn.close()

    except sqlite3.Error as e:
        print(e)
        sys.exit(2)

    print("->  Retrieved %i Temperature values" % len(rowsTemp))
    print("->  Retrieved %i Humidity values" % len(rowsHumidity))

    # Load Weather
    print("-> Loading from %s" % weatherFile)
    rowsWeather = []
    try:
        conn = sqlite3.connect(weatherFile)
        c = conn.cursor()
        c.execute('SELECT timestamp,temp,humidity FROM weather WHERE timestamp > strftime("%%s", datetime("now", "%s"))' % (duration))
        rowsWeather = c.fetchall()

        conn.close()

    except sqlite3.Error as e:
        print(e)
        sys.exit(2)
    print("->  Retrieved %i Temp & Humidity weather values" % len(rowsWeather))


    # Now for the math part...
    # Timestamps on the Sensor & the Weather won't line up so we have to 
    # Interpolate one to the other.. Which one?
    # We almost certainly have 1-2 orders of magnitude more Sensor data than weather
    # So lets use the Sensor data as the true timeline and interpolate to that.

    # We'll need to do this twice.. One for Temp & once for Humidity
    
    # Start by separating the data out & converting to numeric types
    rtTimestamp = []
    rtData = []
    for data in rowsTemp:
        if int(data[0]) > int(rowsWeather[0][0]):
            rtTimestamp.append( int(data[0]) )
            rtData.append( float(data[1]) )

    rhTimestamp = []
    rhData = []
    for data in rowsHumidity:
        if int(data[0]) > int(rowsWeather[0][0]):
            rhTimestamp.append( int(data[0]) )
            rhData.append( float(data[1]) )
        

    wTimestamp = []
    wTemp = []
    wHumidity = []
    for data in rowsWeather:
        wTimestamp.append( int(data[0]) )
        wTemp.append( float(data[1]) )
        wHumidity.append( float(data[2]) )

    # Now interpolate the Weather data (wTemp/wHumidity) to the rh/rt Timestamps
    # thankfully numpy has oneliners for this
    interp_wTemp = numpy.interp( rtTimestamp, wTimestamp, wTemp)
    interp_wHumidity = numpy.interp( rhTimestamp, wTimestamp, wHumidity)

    # Again, numpy one-liners.. Compute the delta between the Sensor & the interpolated Weather
    deltaTemp = numpy.subtract(rtData, interp_wTemp)
    deltaHumidity = numpy.subtract(rhData, interp_wHumidity)


    output = open(outFile, 'w')
    output.write("""<html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.5.0"></script>
        <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.1.1"></script>
        <title>RVWhisper Graphs</title>
    </head>
    <body>
            <canvas id="myChart"></canvas>
    <script>
    chartData = {
        datasets: [
            { type: 'line',
                      label: 'Difference in Temperature',
                      yAxisID: 'DegreesF',
                      showLine: true,
                      cubicInterpolationMode: 'default',
                      tension: 0.2,
                      radius: 0,
                      data: [""")
    dataString = []
    for row in zip(rtTimestamp, deltaTemp):
        dataString.append('{x: %s, y: %s}' % (row[0], row[1]))
    output.write(','.join(dataString))
    output.write("],\n")
    output.write("borderColor: 'red',\n")
    output.write("backgroundColor: 'rgba(255, 0,0,0.5)',\n")
    output.write("fill: 'origin'")
    output.write("""},
            {type: 'line',  
                      label: 'Difference in Humidity',
                      yAxisID: 'PercentHumidity',
                      showLine: true,
                      cubicInterpolationMode: 'default',
                      tension: 0.2,
                      radius: 0,
                      data: [""")
    dataString = []
    for row in zip(rhTimestamp, deltaHumidity):
        dataString.append('{x: %s, y: %s}' % (row[0], row[1]))
    output.write(','.join(dataString))
    output.write("],")
    output.write("borderColor: 'blue',")
    output.write("backgroundColor: 'rgba(0, 0,255,0.5)',\n")
    output.write("fill: 'origin'")
    output.write("} ] };")

    output.write("""
  const config = {
    type: "line",
    data: chartData,
    options: {
        parsing: false,
        interaction: {
                mode: 'x',
                axis: 'x',
                intersect: false
        },
    plugins: {
        zoom: {
            pan: {
                enabled: true,
                mode: 'xy'
            },
            zoom: {
                wheel: {
                    enabled: true
                },
                pinch: {
                    enabled: true
                }
            }
        },
        tooltip: {
            callbacks: {
                label: function(context) {

                    var d = new Date(0);
                    d.setUTCSeconds(context.parsed.x);
                    var label = [d.toLocaleString()];
                    label.push(context.dataset.label + " = " + context.parsed.y);
                    
                    return label;
                }
            }
        }
    },
    scales: {
        DegreesF: {
            title: {
                display: true,
                text: 'Degrees F'
            },
            position: 'left'
        },
        PercentHumidity: {
            title: {
                display: true,
                text: '%% Humidity'
            },
            position: 'right'
        },
        x: {
            type: 'linear',
            ticks: {
                callback: function(value, index, values) {
                    var d = new Date(0);
                    d.setUTCSeconds(value);
                    return d.toLocaleString();
                }
            }
        }
    }
    }
  };
  var myChart = new Chart(
    document.getElementById('myChart'),
    config
  );
</script>
</body>
</html>""")
    output.close()









if __name__ == "__main__":
    main(sys.argv[1:])
