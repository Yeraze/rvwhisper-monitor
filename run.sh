#!/bin/sh
cd /home/pi/rvwhisper-monitor
date > logfile
python3 sensors.py >> logfile
chmod 755 status.sh
python3 weather.py >> logfile
python3 graph.py >> logfile

# Perform Analysis
cd analysis
./slope.py -i ../Engine\ battery.db -f Volts -w 10 -o /var/www/html/graph/volts.html -s >> ../logfile
./slope.py -i ../House\ battery.db -f Volts -w 10 -o /var/www/html/graph/house.html >> ../logfile
./delta.py -i ../Indoor.db -w ../weather.db -o /var/www/html/graph/temp.html >> ../logfile

