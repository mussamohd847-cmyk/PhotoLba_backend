from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..db import get_connection
from ..utils import auth_required

admins_bp = Blueprint("admins", __name__)


@admins_bp.get("")
@auth_required(["SUPERADMIN"])
def list_admins():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    u.id,
                    u.full_name,
                    u.email,
                    u.phone,
                    u.status,
                    u.created_at,
                    GROUP_CONCAT(s.name SEPARATOR ', ') AS school_name,
                    GROUP_CONCAT(s.id SEPARATOR ',') AS school_ids
                FROM users u
                LEFT JOIN school_admins sa
                    ON sa.user_id = u.id
                LEFT JOIN schools s
                    ON s.id = sa.school_id
                WHERE u.role = 'ADMIN'
                GROUP BY
                    u.id,
                    u.full_name,
                    u.email,
                    u.phone,
                    u.status,
                    u.created_at
                ORDER BY u.created_at DESC
            """)

            admins = cursor.fetchall()

        return jsonify(
            success=True,
            admins=admins
        )

    finally:
        connection.close()


@admins_bp.post("")
@auth_required(["SUPERADMIN"])
def create_admin():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    school_id = data.get("school_id")

    if not name or not email or not password:
        return jsonify(
            success=False,
            message="Name, email and password are required"
        ), 400

    if len(password) < 6:
        return jsonify(
            success=False,
            message="Password must be at least 6 characters"
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM users WHERE email=%s",
                (email,)
            )

            if cursor.fetchone():
                return jsonify(
                    success=False,
                    message="Email already registered"
                ), 409

            cursor.execute(
                """
                INSERT INTO users
                (full_name,email,phone,password_hash,role,status)
                VALUES (%s,%s,%s,%s,'ADMIN','ACTIVE')
                """,
                (
                    name,
                    email,
                    phone,
                    generate_password_hash(password)
                )
            )

            user_id = cursor.lastrowid

            if school_id:
                cursor.execute(
                    "SELECT id FROM schools WHERE id=%s",
                    (school_id,)
                )

                if not cursor.fetchone():
                    connection.rollback()

                    return jsonify(
                        success=False,
                        message="School not found"
                    ), 404

                cursor.execute(
                    """
                    INSERT INTO school_admins
                    (user_id,school_id)
                    VALUES (%s,%s)
                    """,
                    (user_id, school_id)
                )

        connection.commit()

        return jsonify(
            success=True,
            message="Admin created successfully",
            admin_id=user_id
        ), 201

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


@admins_bp.patch("/<int:uid>/status")
@auth_required(["SUPERADMIN"])
def update_status(uid):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in ("ACTIVE", "BLOCKED"):
        return jsonify(
            success=False,
            message="Invalid status"
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET status=%s
                WHERE id=%s AND role='ADMIN'
                """,
                (status, uid)
            )

        connection.commit()

        return jsonify(
            success=True,
            message="Admin status updated"
        )

    finally:
        connection.close()


@admins_bp.delete("/<int:uid>")
@auth_required(["SUPERADMIN"])
def delete_admin(uid):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM users
                WHERE id=%s AND role='ADMIN'
                """,
                (uid,)
            )

        connection.commit()

        return jsonify(
            success=True,
            message="Admin deleted"
        )

    finally:
        connection.close()
