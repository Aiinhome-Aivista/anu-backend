from flask import jsonify
from database.db_handler import get_db_connection

def get_job_dropdowns():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        #  Use callproc again (mysql-connector safe way)
        cursor.callproc("sp_get_job_dropdowns")

        result_sets = []
        for result in cursor.stored_results():
            rows = result.fetchall()
            result_sets.append([row[0] for row in rows])

        # Map results
        job_titles = result_sets[0] if len(result_sets) > 0 else []
        experience_options = result_sets[1] if len(result_sets) > 1 else []
        location_options = result_sets[2] if len(result_sets) > 2 else []
        role_options = result_sets[3] if len(result_sets) > 3 else []
        primary_skills = result_sets[4] if len(result_sets) > 4 else []
        secondary_skills = result_sets[5] if len(result_sets) > 5 else []

        if not any([job_titles, experience_options, location_options, role_options, primary_skills, secondary_skills]):
            return jsonify({
                "isSuccess": False,
                "message": "No dropdown data found in the database.",
                "jobTitles": [],
                "experienceOptions": [],
                "locationOptions": [],
                "roleOptions": [],
                "primarySkills": [],
                "secondarySkills": [],
                "status": "failed",
                "statusCode": 404
            })

        return jsonify({
            "isSuccess": True,
            "message": "Job dropdowns fetched successfully.",
            "jobTitles": job_titles,
            "experienceOptions": experience_options,
            "locationOptions": location_options,
            "roleOptions": role_options,
            "primarySkills": primary_skills,
            "secondarySkills": secondary_skills,
            "status": "success",
            "statusCode": 200
        })

    except Exception as e:
        print("DEBUG ERROR:", e)
        return jsonify({
            "isSuccess": False,
            "message": str(e),
            "jobTitles": [],
            "experienceOptions": [],
            "locationOptions": [],
            "roleOptions": [],
            "primarySkills": [],
            "secondarySkills": [],
            "status": "failed",
            "statusCode": 500
        })

    finally:
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
        except:
            pass
