import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="garden_data",
    user="endpoint",
    password="Ifa6wasa9"
)

# Define a simple endpoint
@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello, world!'})

# Define an endpoint that accepts a POST request and returns a response
@app.route('/greet', methods=['POST'])
def greet():
    data = request.get_json()
    name = data.get('name')
    return jsonify({'message': f'Hello, {name}!'})

# Define an endpoint that accepts a POST request and inserts the data into a PostgreSQL table
@app.route('/data', methods=['POST'])
def insert_data():
    data = request.get_json()
    name = data.get('name')
    age = data.get('age')
    cur = conn.cursor()
    cur.execute("INSERT INTO mytable (name, age) VALUES (%s, %s)", (name, age))
    conn.commit()
    cur.close()
    return jsonify({'message': 'Data inserted successfully!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4505, debug=True)
