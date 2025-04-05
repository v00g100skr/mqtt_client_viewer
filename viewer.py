from bottle import route, run, response

import logging, os, requests

from pymemcache.client import base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

ha_token = os.environ.get('HA_TOKEN') or 'token'
ha_host = os.environ.get('HA_HOST') or 'ha.host'
port = os.environ.get('PORT') or 8080


@route('/radiation')
def radiation():
    r = requests.get(
        "http://%s:8123/api/states/sensor.geiger_counter_radiation_dose_per_hour" % ha_host,
        headers={"Authorization": "Bearer %s" % ha_token}
    )
    logging.info('get radiation data')
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
    logging.info('get electricity data')
    response.content_type = 'application/json'
    return r or {'error': 'no data'}

@route('/weather')
def weather():
    r = requests.get(
        "http://%s:8123/api/states/sensor.sensor_outdoor_temperature" % ha_host,
        headers={"Authorization": "Bearer %s" % ha_token}
    )
    logging.info('get weather data')
    response.content_type = 'application/json'
    return r or {'error': 'no data'}


@route('/')
def hello():
    logging.info('Hello World!')
    return "Hello World!"


logging.info('start viewer')
run(host='0.0.0.0', port=int(port), debug=True)
