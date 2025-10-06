from flask import Flask, request, jsonify
from repositories.candidate_manager import CandidateManager

app = Flask(__name__)
cm = CandidateManager()


def create_candidate():
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"status":"failed",
                        "statusCode":400,
                        "message":"Invalid JSON"})

    username = payload.get('username')
    email = payload.get('email')
    password = payload.get('password')
    full_name = payload.get('full_name')

    if not username or not email or not password:
        return jsonify({"status":"failed",
                        "statusCode":400,
                        "message":"username, email, password required"})

    try:
        new_id = cm.create_candidate(username, email, password, full_name)
        return jsonify({"status":"success",
                        "statusCode":201,
                        "message":"Candidate created",
                        "data":{"id": new_id}})
    except Exception as e:
        return jsonify({"status":"failed",
                        "statusCode":500,
                        "message":str(e)})


def update_candidate(candidate_id):
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"status":"failed",
                        "statusCode":400,
                        "message":"Invalid JSON"})

    full_name = payload.get('full_name')
    email = payload.get('email')

    try:
        cm.update_candidate(candidate_id, full_name, email)
        return jsonify({"status":"success",
                        "statusCode":200,
                        "message":"Updated"})
    except Exception as e:
        return jsonify({"status":"failed",
                        "statusCode":500,
                        "message":str(e)})


def delete_candidate(candidate_id):
    try:
        cm.delete_candidate(candidate_id)
        return jsonify({"status":"success",
                        "statusCode":200,
                        "message":"Deleted"})
    except Exception as e:
        return jsonify({"status":"failed",
                        "statusCode":500,
                        "message":str(e)})

if __name__ == '__main__':
    app.run(debug=True)
