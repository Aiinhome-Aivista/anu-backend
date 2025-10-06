from flask import Flask, jsonify
from controllers.ProfileMicroservices.login_candidate import login_candidate
from controllers.ProfileMicroservices.candidate_details import candidate_details
from controllers.ProfileMicroservices.login_hiring_manager import login_hiring_manager

app = Flask(__name__)


JOB_SERVICES_URL = '/JobServices'
SMART_MICROSERVICES_URL = '/SmartMicroservices'
PROFILE_MICROSERVICES_URL = '/ProfileMicroservices'
ASSESSMENT_MICROSERVICES_URL = '/AssessmentMicroservices'

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "success",
        "statusCode": 200,
        "message": "Profile microservice is running."
    }), 200


# Login hiring manager
@app.route(PROFILE_MICROSERVICES_URL+'/login/hiringManager', methods=['POST'])
def route_login_hiring_manager():
    return login_hiring_manager()


# Login candidate
@app.route(PROFILE_MICROSERVICES_URL+'/login/candidate', methods=['POST'])
def route_login_candidate():
    return login_candidate()


# Candidate details
@app.route(PROFILE_MICROSERVICES_URL+'/candidate/details', methods=['POST'])
def route_candidate_details():
    return candidate_details()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
