import os,pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
load_dotenv()
c=pymysql.connect(host=os.getenv("DB_HOST","127.0.0.1"),port=int(os.getenv("DB_PORT","3306")),
 user=os.getenv("DB_USER","root"),password=os.getenv("DB_PASSWORD",""),database=os.getenv("DB_NAME","shulebora_db"))
with c.cursor() as cur:
    cur.execute("SELECT id FROM users WHERE email=%s",("admin@shulebora.co.tz",))
    if cur.fetchone():
        cur.execute("UPDATE users SET password_hash=%s,role='SUPERADMIN',status='ACTIVE' WHERE email=%s",
                    (generate_password_hash("Admin@123"),"admin@shulebora.co.tz"))
    else:
        cur.execute("INSERT INTO users(full_name,email,password_hash,role,status) VALUES(%s,%s,%s,'SUPERADMIN','ACTIVE')",
                    ("ShuleBora SuperAdmin","admin@shulebora.co.tz",generate_password_hash("Admin@123")))
c.commit(); c.close()
print("SuperAdmin: admin@shulebora.co.tz / Admin@123")
