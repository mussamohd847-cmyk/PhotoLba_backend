import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    app.config["HOST"] = os.getenv("HOST", "127.0.0.1")
    app.config["PORT"] = int(os.getenv("PORT", "8000"))
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=False
    )

    from .routes.auth import auth_bp
    from .routes.schools import schools_bp
    from .routes.activities import activities_bp
    from .routes.content import content_bp
    from .routes.users import users_bp
    from .routes.contact import contact_bp
    from .routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(schools_bp, url_prefix="/api/schools")
    app.register_blueprint(activities_bp, url_prefix="/api/activities")
    app.register_blueprint(content_bp, url_prefix="/api/content")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(contact_bp, url_prefix="/api/contact")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

    @app.get("/api/health")
    def health():
        return jsonify(
            success=True,
            message="ShuleBora API is running"
        )

    @app.get("/")
    def home():
        return jsonify(
            name="ShuleBora API",
            version="1.0.0",
            status="running"
        )

    return app
