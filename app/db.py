import os
import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "4000")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "shulebora_db"),
        cursorclass=DictCursor,
        autocommit=False,
        ssl={"ssl": {}},
        connect_timeout=15
    )
