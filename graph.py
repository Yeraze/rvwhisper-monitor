import sqlite3
import configparser
from datetime import datetime


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
""")

config = configparser.ConfigParser()
config.read('rvwhisper.ini')
for db in config['GRAPH']['db'].split(','):
	title = config.get('GRAPH', db, fallback = db)
	print("Reading %s (%s)" % (db, title))



# Write out the HTML Footer
output.write("""
  const config = {
    type: 'line',
    data,
    options: {}
  };
  var myChart = new Chart(
    document.getElementById('myChart'),
    config
  );
</script>
</body>
</html>""")
output.close()
