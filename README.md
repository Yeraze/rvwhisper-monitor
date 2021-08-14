# rvwhisper-monitor

This is a collection fo scripts to collect data from an RVWhisper system (available at https://rvwhisper.com/) and 
store it locally in a collection of SQLite3 databases.  It can also poll local weather information from OpenWeather. 

Once the data is collected, it can create dynamic graphs (thanks to Chart.js) and perform some rudimentary analysis.

# Getting Started
These scripts require Python3 and SQLite to be available.  IN addition, you will need to craft a configuration file
that looks something like this:

```ini
[RVWHISPER]
id = RVM2-<your id>

[WEATHER]
apikey=<openweather api key>
zip = 33076

[AUTH]
username = <rvwhisper username>
password = <rvwhisper password>

[GRAPH]
output=/var/www/html/graph/index.html
db=Indoor.db,Engine battery.db,House battery.db,Door.db
Indoor.db=Indoor
Engine battery.db=Engine Battery
House battery.db=House Battery
period=-7 days
Voltssmooth=5

[PercentHumidity]
min=0
max=100

[DegreesF]
min=50
max=120

[Volts]
min=11
max=15

[DEBUG]
printjson = 0
savejson = 0
```

This INI file (called `rvwhisper.ini` ) specifies your authentication details for RVwhisper & OpenWeather, your
local ID instance to monitor, and various parameters about what data to graph and how.

# Scripts
## sensors.py
This script logs into your RVWhisper account and retrieves a list of all sensors, and then downloads the last hour of all relevant
data into SQLite databases locally.  A database will be created for each sensor, named after the "friendly name" of the sensor.  

This script should be called once an hour via Cron.

## weather.py
This script downloads the local weather data (for the Zip code specified in `rvwhisper.ini` ) into a local `weather.db` database.  Some of 
the data is parsed into specific fields (Timestamp, Temperature, Humidity, etc) but the entire JSON result is also stored for future use.  

This script should be called regularly via Cron.

## Graph.py
This script uses all of the available databases and create a single HTML file containing an interactive chart of all the data.  Some basic data
processing is supported (Specifying min & max values of axes, specifying smoothing parameters, etc).

This script should be called regularly via Cron.

## run.sh
This is a sample shell script that calls all of the relevant scripts in order.  If added to your `crontab` for hourly execution, it will update
all of the data and generate a graph once an hour.

# Sample outputs 
Here are some sample outputs from the main script and some analysis,
as defined in the `run.sh` script in the toplevel.

# all.html
[all.html](https://yeraze.github.io/rvwhisper-monitor/samples/all.html) - This is the result of the main `graph.py` script. It shows 
the last 7 days of all captured data.  This includes
* (from rvWhisper) Engine battery Voltage
* (from rvWhisper) House Battery Voltage
* (from rvWhisper) Indoor Temperature & Humidity
* (from rvWhisper) Front door opening (Yellow)
* (from `weather.py`) Exterior Temperature & Humidity
* (from `weather.py`) Night/Day cycle

# volts.html
[volts.html](https://yeraze.github.io/rvwhisper-monitor/samples/volts.html) - Shows the result of the `slope.py` analysis tool, as executed
via:
```
./slope.py -i ../Engine\ battery.db -f Volts -w 10 -o /var/www/html/graph/volts.html
```
This looks at the Engine Battery state and shows the variance over the last 30 days in both 
a line chart and a histogram.  As you can see in the chart above, and in the delta line-chart, there
is a solar panel recharging the battery every day. However, the histogram proves that despite the recharging
I have a slight drain on the battery over time.

# temp.html
[temp.html](https://yeraze.github.io/rvwhisper-monitor/samples/temp.html) - Shows the result of the `delta.py` analysis tool, as executed via:
```
./delta.py -i ../Indoor.db -w ../weather.db -o /var/www/html/graph/temp.html
```

This shows the difference between the Exterior & Interior environment state, indicating that
I maintain a 10-20% lower humidity indoor, and a 10-20 degree F higher temperature inside.
