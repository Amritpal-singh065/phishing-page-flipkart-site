from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow your HTML to call the API

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        os.environ.get('DATABASE_URL'),  # Render provides this
        sslmode='require'
    )

# Create users table on startup
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

# Serve your HTML page
@app.route('/')
def home():
    return app.send_static_file('index.html')

# Handle login form submission
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if user exists
    cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', 
                (email, password))
    user = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if user:
        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'user': {'email': email}
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid email or password'
        }), 401

# Handle registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('INSERT INTO users (email, password) VALUES (%s, %s)', 
                    (email, password))
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Account created successfully!'
        })
    except psycopg2.IntegrityError:
        return jsonify({
            'success': False,
            'message': 'Email already exists'
        }), 400
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))