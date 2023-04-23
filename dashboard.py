from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

# Database connection configuration
DB_HOST = "localhost"
DB_NAME = "garden_data"
DB_USER = "enduser"
DB_PASS = "Ifa6wasa9"

# Retrieve sensor data from the database
def get_sensor_data():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM sensor_data
        ORDER BY timestamp DESC
        LIMIT 5;
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# Split the data for each device ID into its own table
def split_by_device_id(data):
    devices = {}
    for row in data:
        device_id = row[1]
        if device_id not in devices:
            devices[device_id] = []
        devices[device_id].append(row)
    return devices

# Format the data for display
def format_data(data):
    formatted_data = []
    for row in data:
        formatted_row = []
        for i, item in enumerate(row):
            if i == 3 or i == 4 or i == 6 or i == 7:
                if item < 20:
                    formatted_row.append('<span style="color: red;">{}</span>'.format(item))
                elif item < 40:
                    formatted_row.append('<span style="color: orange;">{}</span>'.format(item))
                else:
                    formatted_row.append('<span style="color: green;">{}</span>'.format(item))
            else:
                formatted_row.append(item)
        formatted_data.append(formatted_row)
    return formatted_data

# Route for the dashboard
@app.route('/')
def dashboard():
    data = get_sensor_data()
    devices = split_by_device_id(data)
    formatted_data = {}
    for device_id, device_data in devices.items():
        formatted_data[device_id] = format_data(device_data)
    return render_template('dashboard.html', data=formatted_data)

if __name__ == '__main__':
    app.run(debug=True)
