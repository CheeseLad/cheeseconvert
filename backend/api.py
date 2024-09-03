
import json
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime


app = Flask(__name__)

files_to_convert_folder = 'files-to-convert'
converted_files_folder = 'converted-files'

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/upload-file', methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'message': 'No file part in the request'}), 400
        
        file = request.files['file']

        if file.filename == '':
            return jsonify({'message': 'No file selected for uploading'}), 400

        filename = secure_filename(file.filename)
        upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        extension = filename.split('.')[-1]
        storage_size = os.path.getsize(f'{files_to_convert_folder}/{filename}') / 1024
        file.save(f'{files_to_convert_folder}/{filename}')

        conn = get_db_connection()
        conn.execute('INSERT INTO files (filename, extension, storage_size, upload_time) VALUES (?, ?, ?, ?)', (filename, extension, storage_size, upload_time))
        conn.commit()
        conn.close()

        return jsonify({'message': 'File uploaded successfully'})

    return jsonify({'message': 'Upload a file'})

@app.route('/convert-options', methods=['GET'])
def convert_options():
    options = request.args.get('file_type')
    convert_options = {
        'png': ['jpg', 'jpeg', 'webp', 'tiff'],
        'jpg': ['png', 'webp', 'tiff'],
        'jpeg': ['png', 'webp', 'tiff'],
        'webp': ['png', 'jpg', 'jpeg', 'tiff'],
        'tiff': ['png', 'jpg', 'jpeg', 'webp'],
        
        'mp4': ['webm', 'avi', 'mov', 'wmv'],
        'webm': ['mp4', 'avi', 'mov', 'wmv'],
        'avi': ['mp4', 'webm', 'mov', 'wmv'],
        'mov': ['mp4', 'webm', 'avi', 'wmv'],
        'wmv': ['mp4', 'webm', 'avi', 'mov']
    }
    if options:
        return jsonify({'message': 'Conversion options', 'options': convert_options[options]})
        
    return jsonify({'message': 'Conversion options'})

@app.route('/file-info', methods=['GET'])
def file_info():
    file_id = request.args.get('file_id')
    if file_id:
        conn = get_db_connection()
        file = conn.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
        conn.close()
        return jsonify({'message': 'File information', 'file': dict(file)})

@app.route('/total-uploads', methods=['GET'])
def total_uploads():
    conn = get_db_connection()
    total_uploads = conn.execute('SELECT COUNT(*) FROM files').fetchone()[0]
    conn.close()
    return jsonify({'message': 'Total uploads', 'total_uploads': total_uploads})

@app.route('/total-size', methods=['GET'])
def total_size():
    conn = get_db_connection()
    total_size = conn.execute('SELECT SUM(storage_size) FROM files').fetchone()[0]
    conn.close()
    return jsonify({'message': 'Total size', 'total_size': total_size})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()

    if user:
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Invalid credentials'})


if __name__ == '__main__':

    if not os.path.exists(files_to_convert_folder):
        os.makedirs(files_to_convert_folder)

    if not os.path.exists(converted_files_folder):
        os.makedirs(converted_files_folder)

    db = sqlite3.connect('database.db')
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, filename TEXT, extension TEXT, storage_size INTEGER, upload_time TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)')
    db.commit()
    app.run(port=5000)