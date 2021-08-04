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
		try:
			output.write("""{ type: 'scatter',
					  label: '%s - %s', 
					  data: [""" % (title, field))
	
			c.execute('SELECT timestamp,value FROM data WHERE timestamp > strftime("%%s", datetime("now", "%s")) AND fieldname = "%s"' % (graphPeriod, field))
			rows = c.fetchall()
			dataString = []
			for row in rows:
				dataString.append('{x: %s, y: %s}' % (row[0], row[1]))
			output.write(','.join(dataString))
			output.write("""],
				borderColor: '%s',
				backgroundColor: '%s',
				}, """ % (color[chartCount], color[chartCount]))
			chartCount += 1
		except sqlite3.Error as e:
			print(e)

	# Close the database, if it was opened successfully
	if(conn):
		conn.close()



# Write out the HTML Footer
output.write("""
  {} ] };
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
					var label = [d];
					label.push(context.dataset.label + " = " + context.parsed.y);
					
					return label;
				}
			}
		}
	},
	scales: {
		x: {
			ticks: {
				callback: function(value, index, values) {
					var d = new Date(0);
					d.setUTCSeconds(value);
					return d;
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
