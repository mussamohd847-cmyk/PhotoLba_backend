import os, uuid, jwt
from datetime import datetime,timedelta,timezone
from functools import wraps
from flask import request,jsonify,current_app
from werkzeug.utils import secure_filename
ALLOWED={"png","jpg","jpeg","webp","gif"}

def make_token(user):
    payload={"user_id":user["id"],"role":user["role"],
             "exp":datetime.now(timezone.utc)+timedelta(days=7)}
    return jwt.encode(payload,current_app.config["JWT_SECRET_KEY"],algorithm="HS256")

def current_user():
    h=request.headers.get("Authorization","")
    if not h.startswith("Bearer "): return None
    try: return jwt.decode(h.split(" ",1)[1],current_app.config["JWT_SECRET_KEY"],algorithms=["HS256"])
    except jwt.PyJWTError: return None

def auth_required(roles=None):
    roles=roles or []
    def deco(fn):
        @wraps(fn)
        def wrapper(*a,**kw):
            p=current_user()
            if not p: return jsonify(success=False,message="Authentication required"),401
            if roles and p.get("role") not in roles: return jsonify(success=False,message="Access denied"),403
            return fn(*a,**kw)
        return wrapper
    return deco

def save_upload(file):
    if not file or not file.filename: return None
    ext=file.filename.rsplit(".",1)[-1].lower()
    if ext not in ALLOWED: raise ValueError("Unsupported image type")
    name=f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(current_app.config["UPLOAD_FOLDER"],exist_ok=True)
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"],secure_filename(name)))
    return name
