# Sample outputs 
Here are some sample outputs from the main script and some analysis,
as defined in the `run.sh` script in the toplevel.

# all.html
[all.html](all.html) - This is the result of the main `graph.py` script. It shows 
the last 7 days of all captured data.  This includes
* (from rvWhisper) Engine battery Voltage
* (from rvWhisper) House Battery Voltage
* (from rvWhisper) Indoor Temperature & Humidity
* (from rvWhisper) Front door opening (Yellow)
* (from `weather.py`) Exterior Temperature & Humidity
* (from `weather.py`) Night/Day cycle

# volts.html
[volts.html](volts.html) - Shows the result of the `slope.py` analysis tool, as executed
via:
```
./slope.py -i ../Engine\ battery.db -f Volts -w 10 -o /var/www/html/graph/volts.html
```
This looks at the Engine Battery state and shows the variance over the last 30 days in both 
a line chart and a histogram, with the histogram showing a slight drain on the battery over time.

# temp.html
[temp.html](temp.html) - Shows the result of the `delta.py` analysis tool, as executed via:
```
./delta.py -i ../Indoor.db -w ../weather.db -o /var/www/html/graph/temp.html
```

This shows the difference between the Exterior & Interior environment state, indicating that
I maintain a 10-20% lower humidity indoor, and a 10-20 degree F higher temperature inside.
