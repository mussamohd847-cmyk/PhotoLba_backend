from flask import Blueprint,request,jsonify
from ..db import get_connection
from ..utils import auth_required
contact_bp=Blueprint("contact",__name__)

@contact_bp.post("")
def send():
    d=request.get_json(silent=True) or {}
    if any(not d.get(x) for x in ("name","email","subject","message")): return jsonify(success=False,message="All fields are required"),400
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("INSERT INTO contact_messages(name,email,subject,message) VALUES(%s,%s,%s,%s)",(d["name"],d["email"],d["subject"],d["message"]))
        c.commit(); return jsonify(success=True,message="Message received"),201
    finally: c.close()

@contact_bp.get("")
@auth_required(["SUPERADMIN"])
def list_messages():
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("SELECT * FROM contact_messages ORDER BY created_at DESC"); rows=cur.fetchall()
        return jsonify(success=True,messages=rows)
    finally: c.close()
