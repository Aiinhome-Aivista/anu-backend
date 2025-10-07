from flask import Flask, jsonify
from controllers.ProfileMicroservices.login_candidate import login_candidate
from controllers.ProfileMicroservices.candidate_details import candidate_details
from controllers.ProfileMicroservices.login_hiring_manager import login_hiring_manager
from controllers.JobServices.jobs import get_jobs_by_hiring_manager,get_latest_statuses_by_job_id,get_details_candidate_applied,get_candidate_by_job_and_hiring_manager,get_jobs_candidate_applied,get_interview_schedule
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

# Get jobs by hiring manager ID
@app.route(JOB_SERVICES_URL+'/Jobs/<string:hiringManagerId>', methods=['GET'])
def route_get_jobs_by_hiring_manager(hiringManagerId):  
    return get_jobs_by_hiring_manager(hiringManagerId)

# Get latest statuses by JobId
@app.route(JOB_SERVICES_URL + '/ShortListed/<int:jobId>', methods=['GET'])
def route_get_latest_statuses_by_job_id(jobId):
    return get_latest_statuses_by_job_id(jobId)


# Get details of candidates who applied for a specific JobId
@app.route(JOB_SERVICES_URL + '/appliedJobs/<int:jobId>', methods=['GET'])
def route_get_details_candidate_applied(jobId):
    return get_details_candidate_applied(jobId)

# Get candidates by JobId and HiringManagerId for upcoming interviews
@app.route(JOB_SERVICES_URL + '/upcomingInterview/<int:jobId>/<string:hiringManagerId>', methods=['GET'])
def route_get_candidate_by_job_and_hiring_manager(jobId, hiringManagerId):
    return get_candidate_by_job_and_hiring_manager(jobId, hiringManagerId)

# Get jobs applied by a candidate
@app.route(JOB_SERVICES_URL + '/appliedjobsByCandidate/<int:candidateID>', methods=['GET'])
def route_get_jobs_candidate_applied(candidateID):
    return get_jobs_candidate_applied(candidateID)

# Get interview schedule for a candidate (POST)
@app.route(JOB_SERVICES_URL + '/getInterViewSechdule', methods=['POST'])
def route_get_interview_schedule():
    return get_interview_schedule()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
