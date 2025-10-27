import os
from dotenv import load_dotenv

load_dotenv() 

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '116.193.134.6'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'lmysqluser'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', '')
}



