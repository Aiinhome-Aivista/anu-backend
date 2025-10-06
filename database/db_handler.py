import mysql.connector
from config import MYSQL_CONFIG

def get_db_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except mysql.connector.Error as err:
        raise Exception(f"Database connection error: {err}")

