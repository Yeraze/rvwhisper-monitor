import configparser
import requests
import re


config = configparser.ConfigParser()
config.read('rvwhisper.ini')

print("Reading parameters for %s" % config['DEFAULT']['id'])

bt_basic_ajax = 'https://access.rvwhisper.com/%s/wp-admin/admin-ajax.php'
ajax_nonce = config['DEFAULT']['nonce']
userid = config['DEFAULT']['userid']

httpSession = requests.Session()
# First we have to login.
data = dict()
# First pull the initial login page and extract the required CSRF Tokens
r = httpSession.get('https://access.rvwhisper.com/')
p = re.compile('<input type="hidden" name="csrf_value" value="(\w+)"')
data['csrf_value'] = p.search(r.text).group(1)
p = re.compile('<input type="hidden" name="csrf_name" value="(\w+)"')
data['csrf_name'] = p.search(r.text).group(1)

# Now fetch our Authentication Info and login to generate the required cookies
data['user_name'] = config['AUTH']['username']
data['password'] = config['AUTH']['password']
data['rememberme'] = '0'
print(data)

r = httpSession.post('https://access.rvwhisper.com/account/login', data = data)
print(r)
print(r.headers)
print(r.text)
