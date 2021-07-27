import configparser


config = configparser.ConfigParser()
config.read('rvwhisper.ini')

print("Reading parameters for %s" % config['DEFAULT']['id'])

bt_basic_ajax = 'https://access.rvwhisper.com/%s/wp-admin/admin-ajax.php'
ajax_nonce = config['DEFAULT']['nonce']
