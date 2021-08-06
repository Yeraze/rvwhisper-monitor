#!/bin/sh
cd /home/pi/rvwhisper-monitor
python3 sensors.py
python3 weather.py
python3 graph.py
