from flask import Flask, jsonify
from controllers.ProfileMicroservices.login import login_controller
from controllers.ProfileMicroservices.candidate import create_candidate, delete_candidate, update_candidate

app = Flask(__name__)

JOB_SERVICES_URL = '/JobServices'
SMART_MICROSERVICES_URL = '/SmartMicroservices'
PROFILE_MICROSERVICES_URL = '/ProfileMicroservices'
ASSESSMENT_MICROSERVICES_URL = '/AssessmentMicroservices'

@app.route(PROFILE_MICROSERVICES_URL+'/login', methods=['POST'])
def login():
    return login_controller()

@app.route(PROFILE_MICROSERVICES_URL+'/candidates', methods=['POST'])
def candidate():
    return create_candidate()

@app.route(PROFILE_MICROSERVICES_URL+'/candidates/<int:candidate_id>', methods=['PUT'])
def candidate_update():
    return update_candidate()

@app.route(PROFILE_MICROSERVICES_URL+'/candidates/<int:candidate_id>', methods=['DELETE'])
def candidate_delete():
    return delete_candidate()



@app.route('/')
def index():
    return jsonify({"status":"success",
                    "statusCode":200,
                    "message":"API running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
