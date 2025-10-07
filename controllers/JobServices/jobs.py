from flask import request, jsonify
from database.db_handler import get_db_connection

def get_jobs_by_hiring_manager(hiringManagerId):
    try:
        if not hiringManagerId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "HiringManagerId is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM job WHERE HiringManagerId = %s", (hiringManagerId,))
        jobs = cursor.fetchall()

        if not jobs:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No jobs found for HiringManagerId {hiringManagerId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Jobs retrieved successfully for HiringManagerId {hiringManagerId}.",
            "isSuccess": True,
            "result": jobs
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass

def get_latest_statuses_by_job_id(jobId):
    try:
        if not jobId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "JobId is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch latest statuses for the given JobId
        cursor.execute("SELECT * FROM v_hm_candidate_shortlisted WHERE JobId = %s", (jobId,))
        statuses = cursor.fetchall()

        if not statuses:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No statuses found for JobId {jobId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Statuses retrieved successfully for JobId {jobId}.",
            "isSuccess": True,
            "result": statuses
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass

def get_details_candidate_applied(jobId):
    try:
        if not jobId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "JobId is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch candidate application details for the given JobId
        cursor.execute("SELECT * FROM v_hm_candidate_applied WHERE JobId = %s", (jobId,))
        details = cursor.fetchall()

        if not details:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No candidate details found for JobId {jobId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Candidate details retrieved successfully for JobId {jobId}.",
            "isSuccess": True,
            "result": details
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass  

def get_candidate_by_job_and_hiring_manager(jobId, hiringManagerId):
    try:
        if not jobId or not hiringManagerId:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Both JobId and HiringManagerId are required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch candidates with upcoming interviews for the given JobId and HiringManagerId
        cursor.execute("""
            SELECT * 
            FROM v_hm_candidate_meeting 
            WHERE JobId = %s AND HiringManagerId = %s
        """, (jobId, hiringManagerId))
        candidates = cursor.fetchall()

        if not candidates:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No upcoming interview data found for JobId {jobId} and HiringManagerId {hiringManagerId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Upcoming interview data retrieved successfully for JobId {jobId} and HiringManagerId {hiringManagerId}.",
            "isSuccess": True,
            "result": candidates
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass    

def get_jobs_candidate_applied(candidateID):
    try:
        if not candidateID:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "CandidateID is required.",
                "isSuccess": False
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch jobs applied by the candidate
        cursor.execute("SELECT * FROM v_hm_candidate_job_mapping WHERE CandidateId = %s", (candidateID,))
        applied_jobs = cursor.fetchall()

        if not applied_jobs:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No applied job details found for CandidateID {candidateID}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Applied jobs retrieved successfully for CandidateID {candidateID}.",
            "isSuccess": True,
            "result": applied_jobs
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass

def get_interview_schedule():
    try:
        data = request.get_json()
        if not data or "jobId" not in data or "CandidateId" not in data:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "Invalid input data. 'jobId' and 'CandidateId' are required.",
                "isSuccess": False
            }), 400

        jobId = data["jobId"]
        candidateId = data["CandidateId"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * 
            FROM v_hm_candidate_meeting 
            WHERE JobId = %s AND CandidateId = %s
        """, (jobId, candidateId))
        schedule = cursor.fetchall()

        if not schedule:
            return jsonify({
                "status": "failed",
                "statusCode": 404,
                "message": f"No interview schedule found for JobId {jobId} and CandidateId {candidateId}.",
                "isSuccess": False,
                "result": None
            }), 404

        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": f"Interview schedule retrieved successfully for JobId {jobId} and CandidateId {candidateId}.",
            "isSuccess": True,
            "result": schedule
        }), 200

    except Exception as e:
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e),
            "isSuccess": False
        }), 500

    finally:
        try:
            if conn.is_connected():
                cursor.close()
                conn.close()
        except:
            pass