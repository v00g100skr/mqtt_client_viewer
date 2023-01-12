from bottle import route, run, response

import logging, os, requests

from pymemcache.client import base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        #logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

host = os.environ.get('MEMCHACHED_HOST') or 'memcached'
port = os.environ.get('MEMCHACHED_PORT') or 11211
ha_token = os.environ.get('HA_TOKEN') or 'token'
ha_host = os.environ.get('HA_HOST') or 'ha.host'

cache = base.Client((host, port))

# This is the Viewer


@route('/test')
def test():
    logging.info('Hello World!')
    return "Hello World!"


@route('/radiation')
def radiation():
    r = requests.get(
        "http://%s:8123/api/states/sensor.geiger_counter_radiation_dose_per_hour" % ha_host,
        headers={"Authorization": "Bearer %s" % ha_token}
    )
    logging.info('get water data')
    response.content_type = 'application/json'
    return r or {'error': 'no data'}


@route('/water')
def radiation():
    r = requests.get(
        "http://%s:8123/api/states/binary_sensor.water_pressure_sensor_contact" % ha_host,
        headers={"Authorization": "Bearer %s" % ha_token}
    )
    logging.info('get water data')
    response.content_type = 'application/json'
    return r or {'error': 'no data'}


@route('/electricity')
def radiation():
    r = requests.get(
        "http://%s:8123/api/states/binary_sensor.2233_ca1_zone_0_power" % ha_host,
        headers={"Authorization": "Bearer %s" % ha_token}
    )
    logging.info('get water data')
    response.content_type = 'application/json'
    return r or {'error': 'no data'}


@route('/')
def hello():
    cached_data = cache.get('geiger_counter')
    logging.info('caching data get: %s' % cached_data)
    response.content_type = 'application/json'
    return cached_data or {'error': 'no data in cache'}


logging.info('start viewer %s:%s' % (host, port))
run(host='0.0.0.0', port=8080, debug=True)