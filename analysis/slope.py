#!/usr/bin/python3

import sys, getopt
import numpy
import sqlite3
import solar

def usage():
    print('slope.py -i <input SQLite DB> -o <output HTML file> -f <Field Name> [-w <Width # (Default 10)>] [-d <Duration, Default -30 days>]')

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
    inField = ''
    outFile = ''
    width = 10
    duration = "-30 days"
    runSolar = False

    if len(argv) < 1:
        usage()
        sys.exit(2)

    try:
        opts, args = getopt.getopt(argv, "i:o:f:w:d:s", ["input=", "output=", "field=", "width=", "duration=", "solar"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)


    for opt, arg in opts:
        if opt in ("-i", "--input"):
            inFile = arg
        elif opt in ("-o", "--output"):
            outFile = arg
        elif opt in ("-f", "--field"):
            inField = arg
        elif opt in ("-w", "--width"):
            width = int(arg)
        elif opt in ("-d", "--duration"):
            duration = arg
        elif opt in ("-s", "--solar"):
            runSolar = True
        

    print("Reading '%s' from '%s" % (inField, inFile))
    print("Calculating over %i samples, and writing to  '%s'" % (width, outFile))


    data = loadData(inFile, inField, duration)
    print("-> Loaded %i rows of data" % len(data))

    outData = []
    outValues = []
    # First take the data from our query and convert it into numeric types
    for i in range(0, len(data)):
        # We want to do some basic smoothing, so take a region around our point of interest
        minData = max(i - width, 0)
        maxData = min(i + width, len(data))
        slice = data[minData:maxData+1]

        yVals = []
        xVals = []
        # We're going to do a simple Linear Fix (using NumPy)
        # But to make it make a bit more sense, we'll offset the X-axis back to 0
        # by subtracting the first time value
        for num in slice:
            xVals.append( int(num[0])  - int(slice[0][0]))
            yVals.append( float(num[1]) )
        model = numpy.polyfit(xVals,yVals,1)    
        # Now save the results of the Linear Fit, we really only care about the slope
        # *3600 = Converting from Seconds to Hours
        outData.append( (data[i][0], model[0] * 3600) )
        outValues.append(model[0] * 3600)
        

    # Now calculate a histogram of the fit values (Slope)
    # Make it symmetric by finding the max value and forcing the bounds to be +/- max
    absMax = max( abs(min(outValues)), max(outValues))
    histModel = numpy.histogram(outValues, bins = 50, range = (-absMax, absMax))


    # now start with the HTML 
    output = open(outFile, 'w')
    output.write("""<html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.5.0"></script>
        <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.1.1"></script>
        <title>RVWhisper Graphs</title>
    </head>
    <body>
        <div style="width: 49%%; float: left">
            <canvas id="myChart"></canvas>
            <canvas id="minmax"></canvas>
        </div>
        <div style="width: 49%%; float:right">
            <canvas id="histogram"></canvas>
    <script>
    chartData = {
        datasets: [
            { type: 'line',
                      label: 'Estimated Change of %s per Hour', 
                      yAxisID: 'SLOPE',
                      showLine: true,
                      cubicInterpolationMode: 'default',
                      tension: 0.2,
                      radius: 0,
                      data: [""" % (inField))
    dataString = []
    for row in outData:
        dataString.append('{x: %s, y: %s}' % (row[0], row[1]))
    output.write(','.join(dataString))
    output.write("],")
    output.write("borderColor: 'red',")
    output.write("backgroundColor: 'red'")
    output.write("} ] };")

    output.write("""
    dataHistogram = {
        labels: [""")
    histLabels = []
    for i in range(0, len(histModel[1])-1):
        histLabels.append("'{a:.3f} - {b:.3f}'".format(a = float(histModel[1][i]), b= float(histModel[1][i+1])))
    output.write(','.join(histLabels))
    output.write(""" 
        ],
        datasets: [
            { type: 'bar',
                      label: 'Histogram of Change in %s', 
                      data: [ %s ]
                } ] };""" % (inField, ','.join(map(str,histModel[0]))))

    # Now write out the larger min/max/average dataset.. This is a separate query but simple enough
    rows = []
    try:
        conn = sqlite3.connect(inFile)
        c = conn.cursor()
        c.execute("""select * from (
                        select date(datetime(timestamp, 'unixepoch')) as timestamp, 
                               min(cast(value as real)),
                               max(cast(value as real)),
                               avg(cast(value as real)) 
                               from data where fieldname='%s' 
                               group by date(datetime(timestamp, 'unixepoch')) 
                               order by timestamp desc limit 30
                        ) order by timestamp;""" % inField)
        rows = c.fetchall()
        conn.close()
    except sqlite3.Error as e:
        print(e)
        sys.exit(2)
        
    output.write("""
    dataMinmax = {
        labels: [""")
    dataString = []
    for row in rows:
        dataString.append("'%s'" % (row[0]) )
    output.write(",".join(dataString))
    output.write("""
        ],
        datasets: [
            { type: 'bar',
              label: 'Min/Max of %s',
              yAxisID: 'SLOPE',
              data: [""" % inField)
    dataString = []
    for row in rows:
        dataString.append("[%s, %s]" % (row[1], row[2]) )
    output.write(",".join(dataString))
    output.write("""
    ] },
    { type: 'line',
      label: 'Average of %s',
      yAxisID: 'SLOPE',
      data: [""" % inField)
    dataString = []
    for row in rows:
        dataString.append("%s" % row[3] )
    output.write(",".join(dataString))

    output.write("""
    ] 
    }] };
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
  );""")

    output.write("""
  const histConfig = {
    type: "bar",
    data: dataHistogram,
    options: {
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
        }
    }
    }};

  var chart2 = new Chart(
    document.getElementById('histogram'),
    histConfig
  );
  const minmaxConfig = {
    type: "bar",
    data: dataMinmax,
    options: {
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
        }
    },
    scales: {
        'SLOPE': {
            position: 'left',
            beginAtZero: false
        }
    }
    }};

  var chart3 = new Chart(
    document.getElementById('minmax'),
    minmaxConfig
  );
</script>
""")

    if (runSolar):
        print("Running solar analysis...")
        output.write(solar.analyze(inFile, "../weather.db"))
    output.write("""
</div>
</body>
</html>""")
    output.close()



# select date(datetime(timestamp, 'unixepoch')), min(value),max(value) from data where fieldname='Volts' group by date(datetime(timestamp, 'unixepoch'));
# select date(datetime(timestamp, 'unixepoch')), min(value),max(value),avg(value) from data where fieldname='Volts' group by date(datetime(timestamp, 'unixepoch'));








if __name__ == "__main__":
    main(sys.argv[1:])
