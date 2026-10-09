from flask import Blueprint,request,jsonify
from ..db import get_connection
from ..utils import auth_required,save_upload
activities_bp=Blueprint("activities",__name__)

@activities_bp.get("")
def list_activities():
    q=request.args.get("search",""); cat=request.args.get("category","")
    sql="""SELECT a.*,s.name school_name FROM activities a JOIN schools s ON s.id=a.school_id
           WHERE s.publication_status='PUBLISHED'"""
    p=[]
    if q: sql+=" AND (a.title LIKE %s OR a.description LIKE %s)"; p += [f"%{q}%",f"%{q}%"]
    if cat and cat!="All Activities": sql+=" AND a.category=%s"; p.append(cat)
    sql+=" ORDER BY a.activity_date DESC,a.created_at DESC"
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute(sql,p); rows=cur.fetchall()
        return jsonify(success=True,activities=rows,count=len(rows))
    finally: c.close()

@activities_bp.post("")
@auth_required(["SUPERADMIN","ADMIN"])
def create():
    d=request.form.to_dict()
    if not d.get("school_id") or not d.get("title"): return jsonify(success=False,message="school_id and title are required"),400
    img=save_upload(request.files.get("image")) if request.files.get("image") else None
    c=get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("""INSERT INTO activities(school_id,title,category,description,activity_date,image)
            VALUES(%s,%s,%s,%s,%s,%s)""",(d["school_id"],d["title"],d.get("category",""),d.get("description",""),d.get("activity_date") or None,img))
            i=cur.lastrowid
        c.commit(); return jsonify(success=True,activity_id=i),201
    finally: c.close()

@activities_bp.delete("/<int:iid>")
@auth_required(["SUPERADMIN","ADMIN"])
def delete(iid):
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("DELETE FROM activities WHERE id=%s",(iid,))
        c.commit(); return jsonify(success=True,message="Activity deleted")
    finally: c.close()
