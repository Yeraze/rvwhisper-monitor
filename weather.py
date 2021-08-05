import sqlite3
import configparser
import requests
import json


config = configparser.ConfigParser()
config.read('rvwhisper.ini')


httpSession = requests.Session()

r = httpSession.get('http://api.openweathermap.org/data/2.5/weather?appid=%s&zip=%s'
	% (config['WEATHER']['apikey'], config['WEATHER']['zip'] ))
r.raise_for_status()

try:
	conn = sqlite3.connect('weather.db')
except sqlite3.Error as e:
	print(e)

c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS weather (
		timestamp integer PRIMARY KEY,
		temp real,
		humidity integer,
		weather text,
		sunrise integer,
		sunset integer,
		json text);""")

weather = json.loads(r.text)

print(json.dumps(weather, indent=4))

c = conn.cursor();
c.execute("""INSERT INTO weather(timestamp,temp,humidity,weather,sunrise,sunset,json) VALUES(?,?,?,?,?,?,?)""",
	(weather["dt"], (float(weather["main"]["temp"]) - 273.15) * 9.0/5.0 + 32.0, weather["main"]["humidity"], 
	weather["weather"][0]["main"], weather["sys"]["sunrise"], weather["sys"]["sunset"], r.text) )
conn.commit()

conn.close()
