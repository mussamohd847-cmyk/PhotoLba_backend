from flask import Blueprint,jsonify
from ..db import get_connection
from ..utils import auth_required,current_user
dashboard_bp=Blueprint("dashboard",__name__)

@dashboard_bp.get("/stats")
@auth_required(["SUPERADMIN","ADMIN","MEMBER"])
def stats():
    c=get_connection()
    try:
        with c.cursor() as cur:
            vals={}
            for key,sql in [("users","SELECT COUNT(*) n FROM users"),("schools","SELECT COUNT(*) n FROM schools"),
                            ("published_schools","SELECT COUNT(*) n FROM schools WHERE publication_status='PUBLISHED'"),
                            ("activities","SELECT COUNT(*) n FROM activities"),("images","SELECT COUNT(*) n FROM school_images"),
                            ("likes","SELECT COUNT(*) n FROM likes")]:
                cur.execute(sql); vals[key]=cur.fetchone()["n"]
        return jsonify(success=True,stats=vals)
    finally: c.close()

@dashboard_bp.post("/schools/<int:sid>/like")
@auth_required(["MEMBER","ADMIN","SUPERADMIN"])
def like(sid):
    uid=current_user()["user_id"]; c=get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT id FROM likes WHERE user_id=%s AND school_id=%s",(uid,sid)); row=cur.fetchone()
            if row: cur.execute("DELETE FROM likes WHERE id=%s",(row["id"],)); action="unliked"
            else: cur.execute("INSERT INTO likes(user_id,school_id) VALUES(%s,%s)",(uid,sid)); action="liked"
        c.commit(); return jsonify(success=True,action=action)
    finally: c.close()
