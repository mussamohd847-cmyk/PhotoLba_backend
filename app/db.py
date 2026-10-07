import os, pymysql
from pymysql.cursors import DictCursor
def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST","127.0.0.1"),
        port=int(os.getenv("DB_PORT","3306")),
        user=os.getenv("DB_USER","root"),
        password=os.getenv("DB_PASSWORD",""),
        database=os.getenv("DB_NAME","shulebora_db"),
        cursorclass=DictCursor,autocommit=False
    )
