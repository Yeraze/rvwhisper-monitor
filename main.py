import configparser
import requests
import re


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

# retrieve data for a sensor
data = dict()
data['action'] = 'get_latest_data_by_date'
data['sensor'] = config['DEFAULT']['sensorid']
data['date_interval'] = 4
data['browser_gmt_offset'] = -4
data['charting'] = 'false'
data['bt_nonce'] = ajax_nonce
print("-> Fetching data for sensor %s" % data['sensor'])
r = httpSession.post('https://access.rvwhisper.com/%s/wp-admin/admin-ajax.php' % config['DEFAULT']['id'], data = data)
r.raise_for_status()
print(r.text)
