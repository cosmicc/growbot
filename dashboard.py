import pandas as pd
import plotly.express as px
import configparser
from flask import Flask, request, render_template
import psycopg2
from datetime import datetime, timedelta

DEBUG = True

app = Flask(__name__)

# read config settings from /etc/growbot.ini
config = configparser.ConfigParser()
config.read('/etc/growbot.ini')
DASHBOARD_PORT = config['dashboard']['port']
ALLOWED_HOST = config['api']['allowed_host']
DB_HOST = config['postgresql']['host']
DB_NAME = config['postgresql']['database']
DB_USER = config['postgresql']['user']
DB_PASS = config['postgresql']['password']

def connect_database():
    conn = psycopg2.connect(host=DB_HOST,dbname=DB_NAME,user=DB_USER,password=DB_PASS)
    return conn

def update_sensor_name(name, device_id, sensor_id):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute(f"UPDATE sensor_names SET sensor_name = '{name}' WHERE device_id = 'device_id' AND sensor_id = {sensor_id}")
    conn.commit()
    cur.close()
    conn.close()

def get_sensor_name(device_id, sensor_id):
    conn = connect_database()
    cur = conn.cursor()
    cur.execute(f"SELECT sensor_name FROM sensor_names WHERE device_id = 'device_id' AND sensor_id = {sensor_id}")
    sensor_name = cur.fetchone()
    cur.close()
    conn.close()
    return sensor_name

from datetime import datetime, timedelta

def past_eight_hours(datetime_obj):
    # Get the current datetime
    current_datetime = datetime.now()
    # Calculate the difference between the input datetime and the current datetime
    time_diff = current_datetime - datetime_obj
    # Check if the time difference is more than 6 hours
    if time_diff > timedelta(hours=8):
        return True
    else:
        return False

def soil_under_30(soilpct):
    if (soilpct <= 30):
        return True
    else:
        return False

def soil_under_10(soilpct):
    if (soilpct <= 10):
        return True
    else:
        return False

# Retrieve the latest sensor data for each device/sensor combination
def get_sensor_data():
    conn = connect_database()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (device_id, sensor_id) *
        FROM sensor_data
        ORDER BY device_id, sensor_id, timestamp DESC;
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# Format the data for display
def format_data(data):
    formatted_data = []
    for row in data:
        formatted_row = []
        for i, item in enumerate(row):
            formatted_row.append(item)
        formatted_data.append(formatted_row)
    return formatted_data

@app.before_request
def limit_remote_addr():
    if request.remote_addr != ALLOWED_HOST:
        return "You're not allowed to access this resource", 403

# Route for the dashboard
@app.route('/')
def dashboard():
    data = get_sensor_data()
    formatted_data = format_data(data)
    conn = connect_database()
    # Load data from the PostgreSQL database
    df = pd.read_sql_query('SELECT * FROM sensor_data ORDER BY timestamp ASC', conn)

    # Create a line plot showing the soil moisture over time for each plant
    fig1 = px.line(df, x='timestamp', y='soil_pct', color='sensor_name',
                   title='Soil Moisture over Time')
    fig1.update_layout(yaxis=dict(range=[0, 100]))

    # Create a line plot showing the battery voltage over time for each plant
    fig2 = px.line(df, x='timestamp', y='batt_volt', color='sensor_name',
                   title='Battery Voltage over Time')
    fig2.update_layout(yaxis=dict(range=[3.0, 4.3]))

    # Convert the plots to HTML format
    plot1_html = fig1.to_html(full_html=False)
    plot2_html = fig2.to_html(full_html=False)

    # Render the HTML template with the plots
    return render_template('dashboard.html', data=formatted_data, soil_under_10=soil_under_10, soil_under_30=soil_under_30, past_eight_hours=past_eight_hours, plot1=plot1_html, plot2=plot2_html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=DEBUG)

