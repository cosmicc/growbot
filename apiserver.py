import numpy as np
import psycopg2
import configparser
from flask import Flask, jsonify, request, abort
import datetime
import pytz

DEBUG = True

config = configparser.ConfigParser()
config.read('/etc/growbot.ini')

app = Flask(__name__)
API_PORT = config['api']['port']
ALLOWED_USER_AGENT = config['api']['allowed_user_agent']
ALLOWED_HOST = config['api']['allowed_host']
POSTGRESQL_HOST = config['postgresql']['host']
POSTGRESQL_ADMIN_DATABASE = config['postgresql']['admin_database']
POSTGRESQL_ADMIN_USERNAME = config['postgresql']['admin_user']
POSTGRESQL_ADMIN_PASSWORD = config['postgresql']['admin_password']
POSTGRESQL_DATABASE = config['postgresql']['database']
POSTGRESQL_USERNAME = config['postgresql']['user']
POSTGRESQL_PASSWORD = config['postgresql']['password']

SENSOR_LOW = 1100  # Wet
SENSOR_HIGH = 2400 # Dry

# Connect to the PostgreSQL database
conn = psycopg2.connect(host=POSTGRESQL_HOST,database=POSTGRESQL_ADMIN_DATABASE,user=POSTGRESQL_ADMIN_USERNAME,password=POSTGRESQL_ADMIN_PASSWORD)
cur = conn.cursor()

# Create the database if it doesn't exist
cur.execute("GRANT CREATE ON DATABASE garden_data TO endpoint")
conn.commit()
cur.close()
conn.close()

# Connect to the database
conn2 =psycopg2.connect(host=POSTGRESQL_HOST,database=POSTGRESQL_DATABASE, user=POSTGRESQL_USERNAME, password=POSTGRESQL_PASSWORD)
conn3 = psycopg2.connect(host=POSTGRESQL_HOST,database=POSTGRESQL_DATABASE, user=POSTGRESQL_USERNAME, password=POSTGRESQL_PASSWORD)

# Create the table if it doesn't exist
cur2 = conn2.cursor()
cur2.execute("SELECT to_regclass('sensor_data')")
exists = cur2.fetchone()[0]
if not exists:
    print("(!) Sensor_data table is missing, creating table")
    cur2.execute("CREATE TABLE sensor_data (id SERIAL PRIMARY KEY, device_id VARCHAR(4), sensor_id INTEGER, sensor_name VARCHAR(255), soil_value INTEGER, soil_pct INTEGER, status_bit VARCHAR(1), batt_volt NUMERIC(3,2), batt_pct INTEGER, timestamp TIMESTAMP, arrived TIMESTAMP, version INTEGER, sys_error VARCHAR(32))")

conn2.commit()
cur2.close()

def convert_timezone(time_str):
    # Convert string to datetime object
    time_utc = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    # Set the timezone for the datetime object
    timezone_utc = pytz.timezone('UTC')
    time_utc = timezone_utc.localize(time_utc)
    # Convert UTC datetime to ETC timezone datetime
    timezone_etc = pytz.timezone('US/Eastern')
    time_etc = time_utc.astimezone(timezone_etc)
    # Convert datetime object back to string
    time_str_etc = time_etc.strftime('%Y-%m-%d %H:%M:%S')
    return time_str_etc

def update_sensor_name(name, device_id, sensor_id):
    cur3 = conn3.cursor()
    cur3.execute(f"UPDATE sensor_names SET sensor_name = '{name}' WHERE device_id = 'device_id' AND sensor_id = {sensor_id}")
    conn3.commit()
    cur3.close()

def get_sensor_name(device_id, sensor_id):
    cur3 = conn3.cursor()
    print(f"(+) Getting sensor name for device_id: {device_id} and sensor_id: {sensor_id}")
    cur3.execute(f"SELECT sensor_name FROM sensor_names WHERE device_id = '{device_id}' AND sensor_id = {sensor_id}")
    data = cur3.fetchone()
    if (data is not None):
        data = data[0]
    else:
        data = "Unlabeled"
    print(f'(+) Sensor name retrieved for device_id: {device_id} and sensor_id: {sensor_id}: {data}')
    cur3.close()
    return data

@app.before_request
def check_user_agent():
    user_agent = request.headers.get("User-Agent")
    print(f"(+) Incoming request user_agent: {user_agent}")
    if user_agent != ALLOWED_USER_AGENT:
        return "You're not allowed to access this resource", 403
    if request.remote_addr != ALLOWED_HOST:
        return "You're not allowed to access this resource", 403

# Define a simple endpoint
@app.route('/ping', methods=['GET'])
def hello():
    return jsonify({'message': 'Pong'})

# Define an endpoint that accepts a POST request and inserts the data into a PostgreSQL table
@app.route('/sensor', methods=['POST'])
def insert_data():
    data = request.get_json()
    print(f"(+) Incoming Sensor Data: {data}")
    device_id = data.get('device_id')
    sensor_id = data.get('sensor_id')
    soil_value = data.get('soil_value')
    soil_pct = int(np.interp(soil_value, [SENSOR_LOW, SENSOR_HIGH], [100, 0]))
    status_bit = data.get('status_bit')
    batt_volt = data.get('batt_volt')
    batt_pct = data.get('batt_pct')
    timestamp = convert_timezone(data.get('timestamp'))
    reason = data.get('reason')
    version = data.get('version')
    #version = 2
    sensor_name = get_sensor_name(device_id, sensor_id)
    now = datetime.datetime.now()
    arrived = now.strftime('%Y-%m-%d %H:%M:%S')
    print(f"(+) INSERTING DATA: '{device_id}', {sensor_id}, '{sensor_name}', {soil_value}, {soil_pct}, '{status_bit}', '{batt_volt}', {batt_pct}, '{timestamp}', '{arrived}', {version}, '{reason}'")
    cur2 = conn2.cursor()
    cur2.execute(f"INSERT INTO sensor_data (device_id, sensor_id, sensor_name, soil_value, soil_pct, status_bit, batt_volt, batt_pct, timestamp, arrived, version, sys_error) VALUES ('{device_id}', {sensor_id}, '{sensor_name}', {soil_value}, {soil_pct}, '{status_bit}', '{batt_volt}', {batt_pct}, '{timestamp}', '{arrived}', {version}, '{reason}')")
    conn2.commit()
    cur2.close()
    return jsonify({'response': 'Sensor data accepted.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=API_PORT, debug=DEBUG)
    conn.close()
