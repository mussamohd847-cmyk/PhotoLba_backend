from flask import Blueprint,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from ..db import get_connection
from ..utils import make_token,auth_required,current_user
auth_bp=Blueprint("auth",__name__)

@auth_bp.post("/register")
def register():
    d=request.get_json(silent=True) or {}
    name=d.get("name") or d.get("fullName"); email=(d.get("email") or "").strip().lower()
    phone=d.get("phone",""); password=d.get("password","")
    if not name or not email or not password: return jsonify(success=False,message="Name, email and password are required"),400
    if len(password)<6: return jsonify(success=False,message="Password must be at least 6 characters"),400
    c=get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email=%s",(email,))
            if cur.fetchone(): return jsonify(success=False,message="Email already registered"),409
            cur.execute("INSERT INTO users(full_name,email,phone,password_hash,role,status) VALUES(%s,%s,%s,%s,'MEMBER','ACTIVE')",
                        (name,email,phone,generate_password_hash(password)))
            uid=cur.lastrowid
        c.commit(); return jsonify(success=True,message="Account created successfully",user_id=uid),201
    finally: c.close()

@auth_bp.post("/login")
def login():
    d=request.get_json(silent=True) or {}; email=(d.get("email") or "").strip().lower(); password=d.get("password","")
    c=get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT id,full_name,email,phone,role,status,password_hash FROM users WHERE email=%s",(email,))
            u=cur.fetchone()
        if not u or not check_password_hash(u["password_hash"],password): return jsonify(success=False,message="Invalid email or password"),401
        if u["status"]!="ACTIVE": return jsonify(success=False,message="Account is blocked"),403
        token=make_token(u); u.pop("password_hash",None)
        return jsonify(success=True,token=token,user=u)
    finally: c.close()

@auth_bp.get("/me")
@auth_required()
def me():
    p=current_user(); c=get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT id,full_name,email,phone,role,status,created_at FROM users WHERE id=%s",(p["user_id"],))
            u=cur.fetchone()
        return jsonify(success=True,user=u) if u else (jsonify(success=False,message="User not found"),404)
    finally: c.close()
