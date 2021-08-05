import sqlite3
import configparser
from datetime import datetime


color=['red', 'green', 'blue', 'orange', 'yellow', 'purple']

config = configparser.ConfigParser()
config.read('rvwhisper.ini')

output = open(config.get('GRAPH', 'output', fallback='graph.html'), "w")
# Write out the HTML Header
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
""")


graphPeriod = config.get('GRAPH', 'period', fallback="-30 days")
print("Graphing data over period: %s" % graphPeriod)
chartCount = 0
foundFields = []

for db in config['GRAPH']['db'].split(','):
	title = config.get('GRAPH', db, fallback = db)
	print("Reading %s (%s)" % (db, title))

	# Open the Database
	conn = None
	try:
		conn = sqlite3.connect(db)
	except sqlite3.Error as e:
		print(e)


	# Retrieve the list of suitable fields for visualization
	fields = []
	c = conn.cursor();
	try:
		c.execute('SELECT fieldname,count(*) FROM data WHERE timestamp > strftime("%%s", datetime("now", "%s")) GROUP BY fieldname' % graphPeriod)
		rows = c.fetchall()
		for row in rows:
			fields.append(row[0])
	except sqlite3.Error as e:
		print(e)

	print("-> Found fields [%s]" % fields)	

	# For each field, retrieve the data for the last period
	for field in fields:
		if field in foundFields:
			print("Already used this field...")
		else:
			foundFields.append(field)

		try:
			output.write("""{ type: 'line',
					  label: '%s - %s', 
					  yAxisID: '%s',
					  showLine: true,
					  cubicInterpolationMode: 'default',
					  tension: 0.2,
					  radius: 0,
					  data: [""" % (title, field, field))
	
			c.execute('SELECT timestamp,value FROM data WHERE timestamp > strftime("%%s", datetime("now", "%s")) AND fieldname = "%s" ORDER BY timestamp' % (graphPeriod, field))
			rows = c.fetchall()

			delta = int(config.get('GRAPH', field+"smooth", fallback = 0))
			if delta > 0:
				# Smoothing of this datatype is enabled.
				print("Smoothing")
				smoothedRows = []
				for i in range(0,len(rows)):
					minData = max(i - delta, 0)
					maxData = min(i + delta, len(rows))
					slice = rows[minData:maxData+1]
					dataSum = 0
					for entry in slice:
						dataSum += float(entry[1])
					smoothedRows.append( (rows[i][0], dataSum / len(slice)) )
				rows = smoothedRows
			dataString = []
			if (field == "DoorState"):
				# Special handling for doors.. Doors have "Just Opened", "Just Closed", and "Still Closed" and "Still Open"
				# We'll convert that to a binary for easier rendering.
				for row in rows:
					if ("Closed" in row[1]):
						dataString.append('{x: %s, y: 0}' % (row[0]))
					else:
						dataString.append('{x: %s, y: 1}' % (row[0]))
			else:
				for row in rows:
					dataString.append('{x: %s, y: %s}' % (row[0], row[1]))
			output.write(','.join(dataString))
			output.write("],")
			if (field == "DoorState"):
				output.write("fill: 'origin',")
			output.write("borderColor: '%s'," % color[chartCount])
			output.write("backgroundColor: '%s'" % color[chartCount])
			output.write("},")
			chartCount += 1
		except sqlite3.Error as e:
			print(e)

	# Close the database, if it was opened successfully
	if(conn):
		conn.close()


# Now, write out the weather
try:
	conn = sqlite3.connect('weather.db')
	c = conn.cursor()

	c.execute('SELECT timestamp,temp,humidity,sunrise,sunset FROM weather WHERE timestamp > strftime("%%s", datetime("now", "%s")) ORDER BY timestamp' % (graphPeriod))
	rows = c.fetchall()
	
	# First write out the environmental temp
	output.write("""{ type: 'line',
			  label: 'Weather - Temperature', 
			  yAxisID: 'DegreesF',
			  showLine: true,
			  cubicInterpolationMode: 'default',
			  tension: 0.2,
			  radius: 0,
			  data: [""")
	dataString = []
	for row in rows:
		dataString.append('{x: %s, y: %s}' % (row[0], row[1]))
	
	output.write(','.join(dataString))
	output.write("],")
	output.write("borderColor: '#bbbbaa'," )
	output.write("backgroundColor: '#bbbbaa'" )
	output.write("},")
	
	# Now write out the environmental Humidity
	output.write("""{ type: 'line',
			  label: 'Weather - Humidity', 
			  yAxisID: 'PercentHumidity',
			  showLine: true,
			  cubicInterpolationMode: 'default',
			  tension: 0.2,
			  radius: 0,
			  data: [""")
	dataString = []
	for row in rows:
		dataString.append('{x: %s, y: %s}' % (row[0], row[2]))
	
	output.write(','.join(dataString))
	output.write("],")
	output.write("borderColor: '#bbbbee'," )
	output.write("backgroundColor: '#bbbbee'" )
	output.write("}, ")

	# Now write out the Sun state line

	output.write("""{ type: 'line',
			  label: 'Sun', 
			  yAxisID: 'DoorState',
			  showLine: true,
			  cubicInterpolationMode: 'default',
			  tension: 0.2,
			  radius: 0,
			  data: [""")
	dataString = []
	for row in rows:
		tNow = int(row[0])
		tSunrise = int(row[3])
		tSunset = int(row[4])
		# If the timestamp is between the Sunrise & Sunset times, assume the sun is up
		# Now, since we'll be coloring _under_ the line, we need to invert the result
		if tNow > tSunrise and tNow < tSunset:
			# Sun is UP
			dataString.append('{x: %s, y: 0}' % (row[0]))
		else:
			# Sun has SET
			dataString.append('{x: %s, y: 1}' % (row[0]))

	
	output.write(','.join(dataString))
	output.write("],")
	output.write("borderColor: 'rgba(64, 64, 64, 0.5)'," )
	output.write("backgroundColor: 'rgba(64,64,64,0.5)'," )
	output.write("fill: 'origin'" )
	output.write("}")
	

	conn.close()
except sqlite3.Error as e:
	print(e)

# Write out the HTML Footer
output.write("""
   ] };
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
				}
			}
		},
		decimation: {
			enabled: true,
			algorithm: 'lttb',
			samples: 200,
			threshold: 500,
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
	scales: {""")
side = "left"
for field in foundFields:
	output.write("""
		%s: {
			title: {
				display: true,
				text: '%s'
			},"""% (field, field))
	if (config.get(field, 'min', fallback = None)):
		output.write("min: %s," % config.get(field, 'min'))
	if (config.get(field, 'max', fallback = None)):
		output.write("max: %s," % config.get(field, 'max'))
	output.write('position: "%s"' % side)
	if (side == "left"):
		side = "right"
	else:
		side = "left"
	output.write("},")
output.write("""
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
