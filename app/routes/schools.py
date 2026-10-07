from flask import Blueprint, request, jsonify
from ..db import get_connection
from ..utils import auth_required, current_user, save_upload

schools_bp = Blueprint("schools", __name__)


# =========================================================
# PUBLIC - LIST SCHOOLS
# =========================================================
@schools_bp.get("")
def list_schools():
    q = request.args.get("search", "").strip()
    typ = request.args.get("school_type", "").strip()
    loc = request.args.get("location", "").strip()
    status = request.args.get("status", "").strip()

    sql = """
        SELECT
            id,
            name,
            location,
            school_type,
            description,
            phone,
            email,
            website,
            address,
            logo,
            publication_status,
            rating,
            created_at
        FROM schools
        WHERE 1=1
    """

    params = []

    if status:
        sql += " AND publication_status=%s"
        params.append(status)

    if q:
        sql += " AND (name LIKE %s OR location LIKE %s)"
        params.extend([f"%{q}%", f"%{q}%"])

    if typ:
        sql += " AND school_type=%s"
        params.append(typ)

    if loc:
        sql += " AND location LIKE %s"
        params.append(f"%{loc}%")

    sql += " ORDER BY created_at DESC"

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            schools = cursor.fetchall()

        return jsonify(
            success=True,
            schools=schools,
            count=len(schools)
        )

    finally:
        connection.close()


# =========================================================
# PUBLIC - GET SINGLE SCHOOL
# =========================================================
@schools_bp.get("/<int:sid>")
def get_school(sid):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM schools WHERE id=%s",
                (sid,)
            )

            school = cursor.fetchone()

        if not school:
            return jsonify(
                success=False,
                message="School not found"
            ), 404

        return jsonify(
            success=True,
            school=school
        )

    finally:
        connection.close()


# =========================================================
# ADMIN - GET MY SCHOOL
# =========================================================
@schools_bp.get("/my-school")
@auth_required(["ADMIN"])
def get_my_school():

    user = current_user()
    user_id = user["user_id"]

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    s.id,
                    s.name,
                    s.location,
                    s.school_type,
                    s.description,
                    s.phone,
                    s.email,
                    s.website,
                    s.address,
                    s.logo,
                    s.publication_status,
                    s.rating,
                    s.created_at
                FROM school_admins sa
                INNER JOIN schools s
                    ON s.id = sa.school_id
                WHERE sa.user_id=%s
                LIMIT 1
            """, (user_id,))

            school = cursor.fetchone()

        if not school:
            return jsonify(
                success=False,
                message="No school has been assigned to this admin."
            ), 404

        return jsonify(
            success=True,
            school=school
        )

    finally:
        connection.close()


# =========================================================
# ADMIN - UPDATE MY SCHOOL
# =========================================================
@schools_bp.put("/my-school")
@auth_required(["ADMIN"])
def update_my_school():

    user = current_user()
    user_id = user["user_id"]

    data = (
        request.form.to_dict()
        if request.form
        else (request.get_json(silent=True) or {})
    )

    name = (data.get("name") or "").strip()
    location = (data.get("location") or "").strip()
    description = (data.get("description") or "").strip()

    if not name:
        return jsonify(
            success=False,
            message="School name is required"
        ), 400

    logo = None

    if request.files.get("logo"):
        logo = save_upload(request.files.get("logo"))

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # Find school assigned to this admin
            cursor.execute("""
                SELECT school_id
                FROM school_admins
                WHERE user_id=%s
                LIMIT 1
            """, (user_id,))

            assignment = cursor.fetchone()

            if not assignment:
                return jsonify(
                    success=False,
                    message="No school has been assigned to this admin."
                ), 404

            school_id = assignment["school_id"]

            if logo:

                cursor.execute("""
                    UPDATE schools
                    SET
                        name=%s,
                        location=%s,
                        description=%s,
                        logo=%s
                    WHERE id=%s
                """, (
                    name,
                    location,
                    description,
                    logo,
                    school_id
                ))

            else:

                cursor.execute("""
                    UPDATE schools
                    SET
                        name=%s,
                        location=%s,
                        description=%s
                    WHERE id=%s
                """, (
                    name,
                    location,
                    description,
                    school_id
                ))

        connection.commit()

        return jsonify(
            success=True,
            message="School information updated successfully"
        )

    except Exception as e:

        connection.rollback()

        print("UPDATE MY SCHOOL ERROR:", e)

        return jsonify(
            success=False,
            message="Failed to update school information",
            error=str(e)
        ), 500

    finally:
        connection.close()


# =========================================================
# SUPERADMIN / ADMIN - CREATE SCHOOL
# =========================================================
@schools_bp.post("")
@auth_required(["SUPERADMIN", "ADMIN"])
def create_school():

    data = (
        request.form.to_dict()
        if request.form
        else (request.get_json(silent=True) or {})
    )

    if not data.get("name"):
        return jsonify(
            success=False,
            message="School name is required"
        ), 400

    logo = (
        save_upload(request.files.get("logo"))
        if request.files.get("logo")
        else None
    )

    user = current_user()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                INSERT INTO schools
                (
                    name,
                    location,
                    school_type,
                    description,
                    phone,
                    email,
                    website,
                    address,
                    logo,
                    publication_status
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                data["name"],
                data.get("location", ""),
                data.get(
                    "school_type",
                    data.get("schoolType", "")
                ),
                data.get("description", ""),
                data.get("phone", ""),
                data.get("email", ""),
                data.get("website", ""),
                data.get("address", ""),
                logo,
                "PUBLISHED"
                if user["role"] == "SUPERADMIN"
                else "PENDING"
            ))

            school_id = cursor.lastrowid

        connection.commit()

        return jsonify(
            success=True,
            school_id=school_id
        ), 201

    finally:
        connection.close()


# =========================================================
# SUPERADMIN / ADMIN - UPDATE SCHOOL
# =========================================================
@schools_bp.put("/<int:sid>")
@auth_required(["SUPERADMIN", "ADMIN"])
def update_school(sid):

    user = current_user()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # ADMIN can only update assigned school
            if user["role"] == "ADMIN":

                cursor.execute("""
                    SELECT school_id
                    FROM school_admins
                    WHERE user_id=%s
                    AND school_id=%s
                    LIMIT 1
                """, (
                    user["user_id"],
                    sid
                ))

                if not cursor.fetchone():
                    return jsonify(
                        success=False,
                        message="You can only manage your assigned school."
                    ), 403

            data = (
                request.form.to_dict()
                if request.form
                else (request.get_json(silent=True) or {})
            )

            logo = (
                save_upload(request.files.get("logo"))
                if request.files.get("logo")
                else None
            )

            base = (
                data.get("name", ""),
                data.get("location", ""),
                data.get(
                    "school_type",
                    data.get("schoolType", "")
                ),
                data.get("description", ""),
                data.get("phone", ""),
                data.get("email", ""),
                data.get("website", ""),
                data.get("address", "")
            )

            if logo:

                cursor.execute("""
                    UPDATE schools
                    SET
                        name=%s,
                        location=%s,
                        school_type=%s,
                        description=%s,
                        phone=%s,
                        email=%s,
                        website=%s,
                        address=%s,
                        logo=%s
                    WHERE id=%s
                """, base + (logo, sid))

            else:

                cursor.execute("""
                    UPDATE schools
                    SET
                        name=%s,
                        location=%s,
                        school_type=%s,
                        description=%s,
                        phone=%s,
                        email=%s,
                        website=%s,
                        address=%s
                    WHERE id=%s
                """, base + (sid,))

        connection.commit()

        return jsonify(
            success=True,
            message="School updated successfully"
        )

    except Exception as e:

        connection.rollback()

        print("UPDATE SCHOOL ERROR:", e)

        return jsonify(
            success=False,
            message="Failed to update school",
            error=str(e)
        ), 500

    finally:
        connection.close()


# =========================================================
# SUPERADMIN - SCHOOL STATUS
# =========================================================
@schools_bp.patch("/<int:sid>/status")
@auth_required(["SUPERADMIN"])
def status(sid):

    status_value = (
        request.get_json(silent=True) or {}
    ).get("status")

    if status_value not in (
        "PUBLISHED",
        "PENDING",
        "UNPUBLISHED"
    ):
        return jsonify(
            success=False,
            message="Invalid status"
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                UPDATE schools
                SET publication_status=%s
                WHERE id=%s
            """, (
                status_value,
                sid
            ))

        connection.commit()

        return jsonify(
            success=True,
            message="School status updated"
        )

    finally:
        connection.close()


# =========================================================
# SUPERADMIN - DELETE SCHOOL
# =========================================================
@schools_bp.delete("/<int:sid>")
@auth_required(["SUPERADMIN"])
def delete(sid):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                DELETE FROM schools
                WHERE id=%s
            """, (sid,))

        connection.commit()

        return jsonify(
            success=True,
            message="School deleted"
        )

    finally:
        connection.close()