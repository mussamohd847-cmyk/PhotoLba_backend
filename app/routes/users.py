from flask import Blueprint,request,jsonify
from werkzeug.security import generate_password_hash
from ..db import get_connection
from ..utils import auth_required
users_bp=Blueprint("users",__name__)

@users_bp.get("")
@auth_required(["SUPERADMIN"])
def list_users():
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("SELECT id,full_name,email,phone,role,status,created_at FROM users ORDER BY created_at DESC"); rows=cur.fetchall()
        return jsonify(success=True,users=rows)
    finally: c.close()

@users_bp.patch("/<int:uid>/status")
@auth_required(["SUPERADMIN"])
def status(uid):
    s=(request.get_json(silent=True) or {}).get("status")
    if s not in ("ACTIVE","BLOCKED"): return jsonify(success=False,message="Invalid status"),400
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("UPDATE users SET status=%s WHERE id=%s",(s,uid))
        c.commit(); return jsonify(success=True,message="User status updated")
    finally: c.close()

@users_bp.delete("/<int:uid>")
@auth_required(["SUPERADMIN"])
def delete(uid):
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("DELETE FROM users WHERE id=%s",(uid,))
        c.commit(); return jsonify(success=True,message="User deleted")
    finally: c.close()
