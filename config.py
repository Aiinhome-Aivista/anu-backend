from dotenv import load_dotenv
import os

load_dotenv()  # loads .env

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '116.193.134.6'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'lmysqluser'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', '')
}

JWT_SECRET = os.getenv('JWT_SECRET', 'change_me_now')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
