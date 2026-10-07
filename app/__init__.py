import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()


def create_default_superadmin():
    from .db import get_connection

    email = os.getenv(
        "SUPERADMIN_EMAIL",
        "superadmin@shulebora.com"
    ).strip().lower()

    password = os.getenv(
        "SUPERADMIN_PASSWORD",
        "SuperAdmin@123"
    )

    name = os.getenv(
        "SUPERADMIN_NAME",
        "ShuleBora SuperAdmin"
    )

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT id
                FROM users
                WHERE role='SUPERADMIN'
                LIMIT 1
            """)

            existing = cursor.fetchone()

            if existing:
                return

            cursor.execute("""
                INSERT INTO users
                (
                    full_name,
                    email,
                    phone,
                    password_hash,
                    role,
                    status
                )
                VALUES (%s,%s,%s,%s,'SUPERADMIN','ACTIVE')
            """, (
                name,
                email,
                "",
                generate_password_hash(password)
            ))

        connection.commit()

        print("========================================")
        print("DEFAULT SUPERADMIN CREATED")
        print(f"Email: {email}")
        print("========================================")

    except Exception as error:
        connection.rollback()
        print("SuperAdmin setup error:", error)

    finally:
        connection.close()


def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "dev-secret"
    )

    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        "dev-jwt-secret"
    )

    app.config["HOST"] = os.getenv(
        "HOST",
        "127.0.0.1"
    )

    app.config["PORT"] = int(
        os.getenv("PORT", "5000")
    )

    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads"
    )

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    origins = [
        x.strip()
        for x in os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
    ]

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": origins
            }
        },
        supports_credentials=True
    )

    from .routes.auth import auth_bp
    from .routes.schools import schools_bp
    from .routes.activities import activities_bp
    from .routes.content import content_bp
    from .routes.users import users_bp
    from .routes.admins import admins_bp
    from .routes.contact import contact_bp
    from .routes.dashboard import dashboard_bp

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth"
    )

    app.register_blueprint(
        schools_bp,
        url_prefix="/api/schools"
    )

    app.register_blueprint(
        activities_bp,
        url_prefix="/api/activities"
    )

    app.register_blueprint(
        content_bp,
        url_prefix="/api/content"
    )

    app.register_blueprint(
        users_bp,
        url_prefix="/api/users"
    )

    app.register_blueprint(
        admins_bp,
        url_prefix="/api/admins"
    )

    app.register_blueprint(
        contact_bp,
        url_prefix="/api/contact"
    )

    app.register_blueprint(
        dashboard_bp,
        url_prefix="/api/dashboard"
    )

    # Create SuperAdmin automatically if none exists
    create_default_superadmin()

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
