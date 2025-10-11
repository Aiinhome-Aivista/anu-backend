from flask import Flask
from flask_cors import CORS
from controllers.JobServices.get_jobs import match_jobs
from controllers.ProfileMicroservices.cv_upload import upload_cv
from controllers.JobServices.job_description import job_description
from controllers.AssessmentMicroservices.evaluate_mcq import evaluate_mcq
from controllers.JobServices.update_status import update_assessment_status
from controllers.AssessmentMicroservices.GetAIMCQByJob import GetAIMCQByJob
from controllers.ProfileMicroservices.login_candidate import login_candidate
from controllers.RecruiterMicroservices.login_recruiter import login_recruiter
from controllers.ProfileMicroservices.candidate_details import candidate_details
from controllers.JobServices.get_interview_schedule import get_interview_schedule
from controllers.JobServices.applied_job_by_candidate import applied_job_by_candidate
from controllers.RecruiterMicroservices.Recruiter_cv_upload import recruiter_upload_cv
from controllers.ProfileMicroservices.candidate_profile_update import update_candidate
from controllers.ProfileMicroservices.login_hiring_manager import login_hiring_manager
from controllers.JobServices.get_jobs_by_hiring_manager import get_jobs_by_hiring_manager
from controllers.AssessmentMicroservices.GetByJobAndCandidate import GetByJobAndCandidate
from controllers.JobServices.get_jobs_candidate_applied import get_jobs_candidate_applied
from controllers.RecruiterMicroservices.GetJobDetails import get_job_details, get_job_search
from controllers.JobServices.get_latest_statuses_by_job_id import get_latest_statuses_by_job_id
from controllers.JobServices.get_details_candidate_applied import get_details_candidate_applied
from controllers.SmartMicroservices.GetJobDescription import generate_job_description, create_job
from controllers.JobServices.get_candidate_by_job_and_hiring_manager import get_candidate_by_job_and_hiring_manager
from controllers.AssessmentMicroservices.call_update_profile_journey_status import call_update_profile_journey_status



app = Flask(__name__)
CORS(app)

JOB_SERVICES_URL = '/JobServices'
SMART_MICROSERVICES_URL = '/SmartMicroservices'
PROFILE_MICROSERVICES_URL = '/ProfileMicroservices'
RECRUITER_MICROSERVICES_URL = '/RecruiterMicroservices'
ASSESSMENT_MICROSERVICES_URL = '/AssessmentMicroservices'

@app.route('/', methods=['GET'])
def health():
    return "hello world"
    


# Upload candidate CV
@app.route(PROFILE_MICROSERVICES_URL+'/upload_cv', methods=['POST'])
def upload_cv_():
    return upload_cv()

# Login candidate
@app.route(PROFILE_MICROSERVICES_URL+'/login/candidate', methods=['POST'])
def route_login_candidate():
    return login_candidate()

#Candidate profile update
@app.route(PROFILE_MICROSERVICES_URL + '/candidate/edit', methods=['PUT'])
def route_update_candidate_route():
    return update_candidate()        

# Candidate details
@app.route(PROFILE_MICROSERVICES_URL+'/candidate/details', methods=['POST'])
def route_candidate_details():
    return candidate_details()       

# Login hiring manager
@app.route(PROFILE_MICROSERVICES_URL+'/login/hiringManager', methods=['POST'])
def route_login_hiring_manager():
    return login_hiring_manager()   
      


# Candidate Job Description
@app.route(JOB_SERVICES_URL + "/job_description/<int:candidate_id>", methods=["GET"])
def route_jobs_description(candidate_id):
    return job_description(candidate_id)

# Status Updating
@app.route(JOB_SERVICES_URL + '/update_status', methods=['POST'])
def updating_assessment_status():
    return update_assessment_status()

# Job Apply
@app.route(JOB_SERVICES_URL + '/applyJob', methods=['POST'])
def route_applied_job_by_candidate():
    return applied_job_by_candidate()

# Get interview schedule for a candidate (POST)
@app.route(JOB_SERVICES_URL + '/getInterViewSechdule', methods=['POST'])
def route_get_interview_schedule():
    return get_interview_schedule()

# Get details of candidates who applied for a specific JobId
@app.route(JOB_SERVICES_URL + '/appliedJobs/<int:jobId>', methods=['GET'])
def route_get_details_candidate_applied(jobId):
    return get_details_candidate_applied(jobId)    

# Get latest statuses by JobId
@app.route(JOB_SERVICES_URL + '/ShortListed/<int:jobId>', methods=['GET'])
def route_get_latest_statuses_by_job_id(jobId):
    return get_latest_statuses_by_job_id(jobId)    

# Get jobs by hiring manager ID
@app.route(JOB_SERVICES_URL+'/Jobs/<string:hiringManagerId>', methods=['GET'])
def route_get_jobs_by_hiring_manager(hiringManagerId):  
    return get_jobs_by_hiring_manager(hiringManagerId)    

# Get matching jobs based on c-id
@app.route(JOB_SERVICES_URL + "/match_all/<int:candidate_id>", methods=["GET"])
def matching_jobs(candidate_id):
    return match_jobs(candidate_id)   

# Get jobs applied by a candidate
@app.route(JOB_SERVICES_URL + '/appliedjobsByCandidate/<int:candidateID>', methods=['GET'])
def route_get_jobs_candidate_applied(candidateID):
    return get_jobs_candidate_applied(candidateID)    

# Get candidates by JobId and HiringManagerId for upcoming interviews
@app.route(JOB_SERVICES_URL + '/upcomingInterview/<int:jobId>/<string:hiringManagerId>', methods=['GET'])
def route_get_candidate_by_job_and_hiring_manager(jobId, hiringManagerId):
    return get_candidate_by_job_and_hiring_manager(jobId, hiringManagerId)     



# Evaluate MCQ
@app.route(ASSESSMENT_MICROSERVICES_URL + '/EvaluateMCQ', methods=['POST'])
def route_evaluate_mcq():
    return evaluate_mcq()

# Update profile journey status
@app.route(ASSESSMENT_MICROSERVICES_URL + '/CallUpdateProfileJourneyStatus', methods=['POST'])
def route_call_update_profile_journey_status():
    return call_update_profile_journey_status()

# Get assessments by JobId and CandidateId 
@app.route(ASSESSMENT_MICROSERVICES_URL + '/JOB/CANDIDATE/ASSESSMENTSTATE/<int:jobId>/<int:candidateId>', methods=['GET'])
def route_get_assessments_by_job_and_candidate(jobId, candidateId):
    return GetByJobAndCandidate(jobId, candidateId)    

# Get AI MCQ by AID, JobId and CID
@app.route(ASSESSMENT_MICROSERVICES_URL + '/ASSESSMENT/JOB/CANDIDATE/GETMCQ/<int:AID>/<int:jobId>/<int:CID>', methods=['GET'])
def route_get_aimcq_by_job(AID, jobId, CID):
    return GetAIMCQByJob(AID, jobId, CID)    



# Create Job 
@app.route(SMART_MICROSERVICES_URL + '/CreatedJob', methods=['POST'])
def create_job_():
    return create_job()

# Get Job Description 
@app.route(SMART_MICROSERVICES_URL + '/GetJobDescription', methods=['POST'])
def generate_job_description_():
    return generate_job_description()  



# get job details - Recruiter
@app.route(RECRUITER_MICROSERVICES_URL+'/GetJobDetais', methods=['GET'])
def get_job_details_():
    return get_job_details()

# get job search - Recruiter
@app.route(RECRUITER_MICROSERVICES_URL+'/getjobsearch', methods=['POST'])
def get_job_search_():
    return get_job_search()  

# cv upload - Recruiter
@app.route(RECRUITER_MICROSERVICES_URL+'/recruiter_upload_cv', methods=['POST'])
def recruiter_upload_cv_():
    return recruiter_upload_cv()

# Login - Recruiter
@app.route(RECRUITER_MICROSERVICES_URL+'/login/recruiter', methods=['POST'])
def login_recruiter_():
    return login_recruiter()



if __name__ == "__main__":  
    app.run(host="0.0.0.0", port=3008, debug=True)
