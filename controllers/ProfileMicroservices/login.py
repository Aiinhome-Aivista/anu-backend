import jwt
import bcrypt
import datetime
from flask import Flask, request, jsonify
from config import JWT_SECRET, JWT_ALGORITHM
from repositories.login_manager import LoginManager

app = Flask(__name__)


def login_controller():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"status": "failed", 
                        "statusCode": 400, 
                        "message": "Invalid JSON payload"})

    username = payload.get('username')
    password = payload.get('password')

    if not username or not password:
        return jsonify({"status": "failed", 
                        "statusCode": 400, 
                        "message": "username and password required"})

    try:
        lm = LoginManager()
        user = lm.get_candidate_by_username(username)
        if not user:
            return jsonify({"status": "failed", 
                            "statusCode": 401, 
                            "message": "Invalid credentials"})

        stored_hash = user.get('password_hash') or user.get('password') or ''
        if not stored_hash:
            return jsonify({"status": "failed", 
                            "statusCode": 500, 
                            "message": "No password hash stored for user"})

        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            user.pop('password_hash', None)
            user.pop('password', None)

            payload = {
                "sub": user.get('id'),
                "username": user.get('username'),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            return jsonify({
                "status": "success",
                "statusCode": 200,
                "message": "Login successful",
                "data": {"token": token, "user": user}
            })
        else:
            return jsonify({"status": "failed", 
                            "statusCode": 401, 
                            "message": "Invalid credentials"})

    except Exception as e:
        return jsonify({"status": "failed", 
                        "statusCode": 500, 
                        "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
