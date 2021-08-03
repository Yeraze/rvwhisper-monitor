import configparser
import requests
import re
import json
from datetime import datetime


config = configparser.ConfigParser()
config.read('rvwhisper.ini')

print("Reading parameters for %s" % config['DEFAULT']['id'])

bt_basic_ajax = 'https://access.rvwhisper.com/%s/wp-admin/admin-ajax.php'

httpSession = requests.Session()
# First we have to login.
data = dict()
# First pull the initial login page and extract the required CSRF Tokens
print("-> Fetching login page")
r = httpSession.get('https://access.rvwhisper.com/')
r.raise_for_status()

p = re.compile('<input type="hidden" name="csrf_value" value="(\w+)"')
data['csrf_value'] = p.search(r.text).group(1)
p = re.compile('<input type="hidden" name="csrf_name" value="(\w+)"')
data['csrf_name'] = p.search(r.text).group(1)

# Now fetch our Authentication Info and login to generate the required cookies
data['user_name'] = config['AUTH']['username']
data['password'] = config['AUTH']['password']
data['rememberme'] = '0'
print("-> Logging in...")
r = httpSession.post('https://access.rvwhisper.com/account/login', data = data)
r.raise_for_status()

# ok, now we are logged in.. Fetch the dashboard and retrieve the Nonce and UserID

print("-> Fetching dashboard")
r = httpSession.get('https://access.rvwhisper.com/%s' % config['DEFAULT']['id'])
r.raise_for_status()

p = re.compile('"ajax_nonce":"(\w+)"')
ajax_nonce = p.search(r.text).group(1)
print("Nonce is %s" % ajax_nonce)

# Also retrieve the basic list of sensors & ID's
p = re.compile('sensor\?sensor_id=(\d+)" title="([\w\s]+)"')
sensors = dict()
iterator = p.finditer(r.text)
for match in iterator:
	print("-> Found sensor: %s (ID: %s)" % (match.group(2), match.group(1)))
	sensors[match.group(2)] = match.group(1)

for sensor in sensors.keys():
# # retrieve data for a sensor
	data = dict()
	data['action'] = 'get_latest_data_by_date'
	data['sensor'] = sensors[sensor]
	data['date_interval'] = 1
	data['browser_gmt_offset'] = -4
	data['charting'] = 'false'
	data['bt_nonce'] = ajax_nonce
	print("-> Fetching data for sensor '%s' (%s)" % (sensor, sensors[sensor]))
	r = httpSession.post('https://access.rvwhisper.com/%s/wp-admin/admin-ajax.php' % config['DEFAULT']['id'], data = data)
	r.raise_for_status()
	data = json.loads(r.text)

	if (config['DEBUG']['printjson'] == '1'):
		json_str = json.dumps(data, indent=4)
		print(json_str)
	if (config['DEBUG']['savejson'] == '1'):
		filename = 'json/%s.json' % sensor
		print('---> Writing to %s' % filename)
		f = open(filename, 'w')
		json_str = json.dumps(data, indent=4)
		f.write(json_str)
		f.close()

	# These are the only fields we care about (Except for TimeStamp)
	ImportantFields = ['DegreesF', 'PercentHumidity', 'Volts', 'DoorState']

	# Start by finding how many of these "Important Fields" are in this dataset
	NumFields = int(data['num_fields'])
	FieldsRead = []
	for i in range(1,NumFields+1):
		fieldName = data['read_field']['read_field_%i' % i][0]
		if (fieldName in ImportantFields):
			print("[Field %i] = %s" % (i, fieldName))
			FieldsRead.append(fieldName)
		else:
			print("[Field %i] = %s (Skipped)" % (i, fieldName))

	# Now iterate over all the data in this fetch, and find the important fields	
	for row in data['latest_points']:
		dataRow = []
		# Timestamp is a  Unix Epoch (Seconds elapsed)
		dataRow.append("Timestamp %s [%s]" % (datetime.fromtimestamp(int(row['TimeStamp'])), row['TimeStamp']))
		for field in FieldsRead:
			dataRow.append("%s = %s" % (field, row[field]))
		print(','.join(dataRow))
