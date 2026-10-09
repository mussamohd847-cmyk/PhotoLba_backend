from flask import Blueprint,request,jsonify
from ..db import get_connection
from ..utils import auth_required,current_user,save_upload
schools_bp=Blueprint("schools",__name__)

@schools_bp.get("")
def list_schools():
    q=request.args.get("search","").strip(); typ=request.args.get("school_type","").strip()
    loc=request.args.get("location","").strip(); status=request.args.get("status","PUBLISHED")
    sql="SELECT id,name,location,school_type,description,phone,email,website,address,logo,publication_status,rating,created_at FROM schools WHERE 1=1"
    p=[]
    if status: sql+=" AND publication_status=%s"; p.append(status)
    if q: sql+=" AND (name LIKE %s OR location LIKE %s)"; p += [f"%{q}%",f"%{q}%"]
    if typ: sql+=" AND school_type=%s"; p.append(typ)
    if loc: sql+=" AND location LIKE %s"; p.append(f"%{loc}%")
    sql+=" ORDER BY created_at DESC"
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute(sql,p); rows=cur.fetchall()
        return jsonify(success=True,schools=rows,count=len(rows))
    finally: c.close()

@schools_bp.get("/<int:sid>")
def get_school(sid):
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("SELECT * FROM schools WHERE id=%s",(sid,)); row=cur.fetchone()
        return jsonify(success=True,school=row) if row else (jsonify(success=False,message="School not found"),404)
    finally: c.close()

@schools_bp.post("")
@auth_required(["SUPERADMIN","ADMIN"])
def create_school():
    d=request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
    if not d.get("name"): return jsonify(success=False,message="School name is required"),400
    logo=save_upload(request.files.get("logo")) if request.files.get("logo") else None
    c=get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("""INSERT INTO schools(name,location,school_type,description,phone,email,website,address,logo,publication_status)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (d["name"],d.get("location",""),d.get("school_type",d.get("schoolType","")),d.get("description",""),
             d.get("phone",""),d.get("email",""),d.get("website",""),d.get("address",""),logo,
             "PUBLISHED" if current_user()["role"]=="SUPERADMIN" else "PENDING"))
            sid=cur.lastrowid
        c.commit(); return jsonify(success=True,school_id=sid),201
    finally: c.close()

@schools_bp.put("/<int:sid>")
@auth_required(["SUPERADMIN","ADMIN"])
def update_school(sid):
    d=request.form.to_dict() if request.form else (request.get_json(silent=True) or {})
    logo=save_upload(request.files.get("logo")) if request.files.get("logo") else None
    c=get_connection()
    try:
        with c.cursor() as cur:
            base=(d.get("name",""),d.get("location",""),d.get("school_type",d.get("schoolType","")),d.get("description",""),
                  d.get("phone",""),d.get("email",""),d.get("website",""),d.get("address",""))
            if logo:
                cur.execute("""UPDATE schools SET name=%s,location=%s,school_type=%s,description=%s,phone=%s,email=%s,website=%s,address=%s,logo=%s WHERE id=%s""",base+(logo,sid))
            else:
                cur.execute("""UPDATE schools SET name=%s,location=%s,school_type=%s,description=%s,phone=%s,email=%s,website=%s,address=%s WHERE id=%s""",base+(sid,))
        c.commit(); return jsonify(success=True,message="School updated")
    finally: c.close()

@schools_bp.patch("/<int:sid>/status")
@auth_required(["SUPERADMIN"])
def status(sid):
    s=(request.get_json(silent=True) or {}).get("status")
    if s not in ("PUBLISHED","PENDING","UNPUBLISHED"): return jsonify(success=False,message="Invalid status"),400
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("UPDATE schools SET publication_status=%s WHERE id=%s",(s,sid))
        c.commit(); return jsonify(success=True,message="School status updated")
    finally: c.close()

@schools_bp.delete("/<int:sid>")
@auth_required(["SUPERADMIN"])
def delete(sid):
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("DELETE FROM schools WHERE id=%s",(sid,))
        c.commit(); return jsonify(success=True,message="School deleted")
    finally: c.close()
