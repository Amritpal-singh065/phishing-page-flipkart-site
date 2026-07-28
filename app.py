from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import bcrypt

app = Flask(__name__)
CORS(app)

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        raise Exception("❌ DATABASE_URL NOT SET")

    return psycopg2.connect(db_url, sslmode="require")


# -------------------------------
# INIT DATABASE
# -------------------------------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# Run once at startup
init_db()


# -------------------------------
# HEALTH CHECK
# -------------------------------
@app.route("/")
def home():
    return jsonify({"message": "Backend running ✅"})


# -------------------------------
# REGISTER API (STORE USER)
# -------------------------------
@app.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "No data"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "message": "Missing fields"}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed_password)
        )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "User stored in database ✅"
        })

    except psycopg2.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Email already exists"
        }), 400

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Server error"
        }), 500


# -------------------------------
# LOGIN API (OPTIONAL TEST)
# -------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            stored_password = user[0]

            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                return jsonify({
                    "success": True,
                    "message": "Login successful ✅"
                })

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Server error"
        }), 500


# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
