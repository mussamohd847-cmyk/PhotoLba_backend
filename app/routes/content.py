from flask import Blueprint,request,jsonify,send_from_directory,current_app
from ..db import get_connection
from ..utils import auth_required,save_upload
content_bp=Blueprint("content",__name__)
TABLES={"features":"features","facilities":"facilities","qualifications":"qualifications","contacts":"school_contacts"}

@content_bp.get("/<kind>/<int:sid>")
def get_items(kind,sid):
    table=TABLES.get(kind)
    if not table: return jsonify(success=False,message="Invalid content type"),400
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute(f"SELECT * FROM {table} WHERE school_id=%s ORDER BY id DESC",(sid,)); rows=cur.fetchall()
        return jsonify(success=True,items=rows)
    finally: c.close()

@content_bp.post("/<kind>")
@auth_required(["SUPERADMIN","ADMIN"])
def create_item(kind):
    table=TABLES.get(kind); d=request.get_json(silent=True) or {}
    if not table: return jsonify(success=False,message="Invalid content type"),400
    sid=d.get("school_id"); name=d.get("name") or d.get("title") or d.get("label")
    if not sid or not name: return jsonify(success=False,message="school_id and name/title required"),400
    c=get_connection()
    try:
        with c.cursor() as cur:
            if kind=="contacts":
                cur.execute("INSERT INTO school_contacts(school_id,contact_type,label,value) VALUES(%s,%s,%s,%s)",(sid,d.get("contact_type","GENERAL"),name,d.get("value","")))
            else:
                cur.execute(f"INSERT INTO {table}(school_id,name,description) VALUES(%s,%s,%s)",(sid,name,d.get("description","")))
            iid=cur.lastrowid
        c.commit(); return jsonify(success=True,id=iid),201
    finally: c.close()

@content_bp.put("/<kind>/<int:iid>")
@auth_required(["SUPERADMIN","ADMIN"])
def update_item(kind,iid):
    table=TABLES.get(kind); d=request.get_json(silent=True) or {}
    if not table: return jsonify(success=False,message="Invalid content type"),400
    name=d.get("name") or d.get("title") or d.get("label")
    c=get_connection()
    try:
        with c.cursor() as cur:
            if kind=="contacts": cur.execute("UPDATE school_contacts SET contact_type=%s,label=%s,value=%s WHERE id=%s",(d.get("contact_type","GENERAL"),name,d.get("value",""),iid))
            else: cur.execute(f"UPDATE {table} SET name=%s,description=%s WHERE id=%s",(name,d.get("description",""),iid))
        c.commit(); return jsonify(success=True,message="Updated")
    finally: c.close()

@content_bp.delete("/<kind>/<int:iid>")
@auth_required(["SUPERADMIN","ADMIN"])
def delete_item(kind,iid):
    table=TABLES.get(kind)
    if not table: return jsonify(success=False,message="Invalid content type"),400
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute(f"DELETE FROM {table} WHERE id=%s",(iid,))
        c.commit(); return jsonify(success=True,message="Deleted")
    finally: c.close()

@content_bp.get("/images/<int:sid>")
def images(sid):
    c=get_connection()
    try:
        with c.cursor() as cur: cur.execute("SELECT * FROM school_images WHERE school_id=%s ORDER BY id DESC",(sid,)); rows=cur.fetchall()
        return jsonify(success=True,images=rows)
    finally: c.close()

@content_bp.get("/images")
def all_images():
    c = get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("""
                SELECT si.id, si.school_id, si.title, si.image_path,
                       s.name AS school_name
                FROM school_images si
                LEFT JOIN schools s ON s.id = si.school_id
                WHERE s.publication_status = 'PUBLISHED'
                ORDER BY si.id DESC
            """)
            rows = cur.fetchall()
        return jsonify(success=True, images=rows)
    finally:
        c.close()

@content_bp.post("/images")
@auth_required(["SUPERADMIN","ADMIN"])
def upload_image():
    sid=request.form.get("school_id"); f=request.files.get("image")
    if not sid or not f: return jsonify(success=False,message="school_id and image are required"),400
    name=save_upload(f); c=get_connection()
    try:
        with c.cursor() as cur:
            cur.execute("INSERT INTO school_images(school_id,title,image_path) VALUES(%s,%s,%s)",(sid,request.form.get("title",""),name)); iid=cur.lastrowid
        c.commit(); return jsonify(success=True,image_id=iid,image_path=name),201
    finally: c.close()


@content_bp.get("/uploads/<path:filename>")
def serve_uploaded_image(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
