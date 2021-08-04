import sqlite3
import configparser
from datetime import datetime


color=['red', 'green', 'blue', 'orange', 'yellow', 'purple']

output = open("graph.html", "w")
# Write out the HTML Header
output.write("""<html>
<head>
	<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
	<title>RVWhisper Graphs</title>
</head>
<body>
	<canvas id="myChart"></canvas>
<script>
chartData = {
	datasets: [
""")

config = configparser.ConfigParser()
config.read('rvwhisper.ini')

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
			output.write("""{ type: 'scatter',
					  label: '%s - %s', 
					  yAxisID: '%s',
					  showLine: true,
					  data: [""" % (title, field, field))
	
			c.execute('SELECT timestamp,value FROM data WHERE timestamp > strftime("%%s", datetime("now", "%s")) AND fieldname = "%s"' % (graphPeriod, field))
			rows = c.fetchall()
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
output.write(" {} ")

# Write out the HTML Footer
output.write("""
   ] };
  const config = {
    type: "scatter",
    data: chartData,
    options: {
	plugins: {
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
		%s: {"""% field)
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
