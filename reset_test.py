import sys
sys.path.append('d:/ANU/anu-backend')
from database.db_handler import get_db_connection

def reset():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Reset slot booking
        cursor.execute("UPDATE hiringmanagerselectedslots SET isBooked = 0, candidateId = NULL WHERE candidateId = 1 AND jobid = 11")
        # Reset job application status
        cursor.execute("UPDATE jobapplication SET LatestStatus = 'Interview Schedule Pending' WHERE CandidateId = 1 AND JobId = 11")
        # Reset job assessments status ONLY for Teams Interview
        cursor.execute("UPDATE jobassessments SET status = 'Not Scheduled' WHERE candidateId = 1 AND jobId = 11 AND assessmentName = 'Teams Interview'")
        # Ensure MCQ assessment is marked as Completed so it doesn't ask to take it again
        cursor.execute("UPDATE jobassessments SET status = 'Completed' WHERE candidateId = 1 AND jobId = 11 AND assessmentName != 'Teams Interview'")
        
        conn.commit()
        print("✅ Database reset successfully! You can now book the slot again.")
    except Exception as e:
        print("Error resetting database:", str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reset()
