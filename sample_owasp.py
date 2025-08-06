import sqlite3
import os
import pickle
import jwt
from flask import Flask, request, make_response

app = Flask(__name__)

SECRET_KEY = "1234567890abcdef"
DB_PASSWORD = "password123"
AWS_SECRET = "AKIA_FAKE_SECRET"

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
conn.commit()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    if user:
        token = jwt.encode({"user": username}, SECRET_KEY, algorithm="HS256")
        return {"token": token}
    else:
        return "Invalid credentials", 401

@app.route('/admin', methods=['GET'])
def admin_panel():
    auth = request.headers.get('Authorization')
    if not auth:
        return "Unauthorized", 401
    token = auth.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return f"Welcome admin: {payload['user']}"
    except Exception as e:
        return f"Auth Failed: {str(e)}", 403

@app.route('/secrets')
def secrets():
    return {
        "db_password": DB_PASSWORD,
        "aws_secret": AWS_SECRET
    }

@app.route('/upload-xml', methods=['POST'])
def upload_xml():
    xml_data = request.data
    with open("temp.xml", "wb") as f:
        f.write(xml_data)
    import xml.etree.ElementTree as ET
    tree = ET.parse("temp.xml")
    return "XML Parsed"

@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    return f"<h1>Hello {name}!</h1>"

@app.route('/deserialize', methods=['POST'])
def deserialize():
    data = request.data
    obj = pickle.loads(data)
    return f"Received object: {str(obj)}"

@app.route('/get-user-data', methods=['GET'])
def get_user_data():
    user_id = request.args.get('id')
    cursor.execute(f"SELECT * FROM users WHERE rowid = {user_id}")
    user = cursor.fetchone()
    return {"user": user}

@app.route('/dangerous-action', methods=['POST'])
def dangerous_action():
    return "Dangerous action performed."

if __name__ == '__main__':
    app.run(debug=True)
