from flask import Flask, request, jsonify
from database.db_handler import get_db_connection


# ==========================================
# 🗃 Repository Layer
# ==========================================
class AssessmentRepository:

    @staticmethod
    def update_job_assessment(candidate_id: int, job_id: int):
        """Call stored procedure to update job assessment."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Call stored procedure (must exist in DB)
            cursor.callproc('sp_update_job_assessment', [candidate_id, job_id])
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to update job assessment: {e}")
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def upsert_job_application(candidate_id: int, job_id: int):
        """Call stored procedure to insert or update job application."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.callproc('sp_upsert_job_application', [candidate_id, job_id])
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to upsert job application: {e}")
        finally:
            cursor.close()
            conn.close()

# ==========================================
# API Endpoint
# ==========================================
def update_assessment_status():
    """POST endpoint to update assessment and job application status."""
    try:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)


        payload = request.get_json(force=True)

        candidate_id = payload.get('CandidateId')
        job_id = payload.get('JobId')

        # Input Validation
        if not candidate_id or not job_id:
            return jsonify({
                "status": "failed",
                "statusCode": 400,
                "message": "CandidateId and JobId are required."
            }), 400

        # Step 1: Update Job Assessment
        AssessmentRepository.update_job_assessment(candidate_id, job_id)

        # Step 2: Insert or Update Job Application
        AssessmentRepository.upsert_job_application(candidate_id, job_id)

        # Success Response
        return jsonify({
            "status": "success",
            "statusCode": 200,
            "message": "Assessment and job application status updated successfully."
        }), 200

    except Exception as e:
        # Error Response
        return jsonify({
            "status": "failed",
            "statusCode": 500,
            "message": str(e)
        }), 500


