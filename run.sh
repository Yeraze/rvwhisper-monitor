#!/bin/sh
cd /home/pi/rvwhisper-monitor
python3 sensors.py
python3 weather.py
python3 graph.py

# Perform Analysis
cd analysis
./slope.py -i ../Engine\ battery.db -f Volts -w 10 -o /var/www/html/graph/volts.html
./delta.py -i ../Indoor.db -w ../weather.db -o /var/www/html/graph/temp.html
