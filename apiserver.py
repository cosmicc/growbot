import psycopg2
from flask import Flask, jsonify, request, abort
import datetime

app = Flask(__name__)
ALLOWED_USER_AGENT = "ESP32HTTPClient"

# Connect to the PostgreSQL database
conn = psycopg2.connect(host="localhost",database="postgres",user="postgres",password="Whatsthe411!!")
cur = conn.cursor()

# Create the database if it doesn't exist
cur.execute("GRANT CREATE ON DATABASE garden_data TO endpoint")
conn.commit()
cur.close()
conn.close()

# Connect to the database
conn = psycopg2.connect(host="localhost",database="garden_data", user="endpoint", password="Ifa6wasa9")

# Create the table if it doesn't exist
cur = conn.cursor()
cur.execute("SELECT to_regclass('sensor_data')")
exists = cur.fetchone()[0]
if not exists:
    print("sensor_data table is missing, creating table")
    cur.execute("CREATE TABLE sensor_data (id SERIAL PRIMARY KEY, device_id VARCHAR(4), sensor_id INTEGER, soil_value INTEGER, soil_pct INTEGER, status_bit VARCHAR(1), batt_volt NUMERIC(2,1), batt_pct INTEGER, timestamp TIMESTAMP, arrived TIMESTAMP, sys_error VARCHAR(32))")

conn.commit()
cur.close()

@app.before_request
def check_user_agent():
    user_agent = request.headers.get("User-Agent")
    print(f"Incoming request user_agent: {user_agent}")
    if user_agent != ALLOWED_USER_AGENT:
        abort(403)

# Define a simple endpoint
@app.route('/ping', methods=['GET'])
def hello():
    return jsonify({'message': 'Pong'})

# Define an endpoint that accepts a POST request and inserts the data into a PostgreSQL table
@app.route('/sensor', methods=['POST'])
def insert_data():
    data = request.get_json()
    print(f"Incoming Sensor Data: {data}")
    device_id = data.get('device_id')
    sensor_id = data.get('sensor_id')
    soil_value = data.get('soil_value')
    soil_pct = data.get('soil_pct')
    status_bit = data.get('status_bit')
    batt_volt = data.get('batt_volt')
    batt_pct = data.get('batt_pct')
    timestamp = data.get('timestamp')
    reason = data.get('reason')
    now = datetime.datetime.now()
    arrived = now.strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.cursor()
    cur.execute(f"INSERT INTO sensor_data (device_id, sensor_id, soil_value, soil_pct, status_bit, batt_volt, batt_pct, timestamp, arrived, sys_error) VALUES ('{device_id}', {sensor_id}, {soil_value}, {soil_pct}, '{status_bit}', '{batt_volt}', {batt_pct}, '{timestamp}', '{arrived}', '{reason}')")
    conn.commit()
    cur.close()
    return jsonify({'response': 'Sensor data accepted.'})

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=4505, debug=True)
    conn.close()
