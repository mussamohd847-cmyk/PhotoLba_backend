from flask import Blueprint, request, jsonify
from ..db import get_connection
from ..utils import auth_required, current_user, save_upload

activities_bp = Blueprint("activities", __name__)


# =========================================================
# PUBLIC - LIST PUBLISHED ACTIVITIES
# =========================================================
@activities_bp.get("")
def list_activities():
    q = request.args.get("search", "").strip()
    cat = request.args.get("category", "").strip()

    sql = """
        SELECT
            a.id,
            a.school_id,
            a.title,
            a.category,
            a.description,
            a.event_date,
            a.status,
            a.image_url,
            a.created_at,
            a.updated_at,
            s.name AS school_name,
            s.location AS school_location
        FROM activities a
        JOIN schools s ON s.id = a.school_id
        WHERE s.publication_status = 'PUBLISHED'
          AND a.status = 'PUBLISHED'
    """

    params = []

    if q:
        sql += """
            AND (
                a.title LIKE %s
                OR a.description LIKE %s
                OR s.name LIKE %s
            )
        """

        params.extend([
            f"%{q}%",
            f"%{q}%",
            f"%{q}%"
        ])

    if cat and cat != "All Activities":
        sql += " AND a.category = %s"
        params.append(cat)

    sql += """
        ORDER BY
            a.event_date DESC,
            a.created_at DESC
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        return jsonify(
            success=True,
            activities=rows,
            count=len(rows)
        )

    finally:
        connection.close()


# =========================================================
# ADMIN - GET ACTIVITIES FOR ASSIGNED SCHOOL
# =========================================================
@activities_bp.get("/my-school")
@auth_required(["ADMIN"])
def my_school_activities():

    user = current_user()
    user_id = user["user_id"]

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

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

            cursor.execute("""
                SELECT
                    id,
                    school_id,
                    title,
                    category,
                    description,
                    event_date,
                    status,
                    image_url,
                    created_at,
                    updated_at
                FROM activities
                WHERE school_id=%s
                ORDER BY
                    event_date DESC,
                    created_at DESC
            """, (school_id,))

            activities = cursor.fetchall()

        return jsonify(
            success=True,
            activities=activities,
            count=len(activities),
            school_id=school_id
        )

    finally:
        connection.close()


# =========================================================
# ADMIN / SUPERADMIN - CREATE ACTIVITY
# =========================================================
@activities_bp.post("")
@auth_required(["SUPERADMIN", "ADMIN"])
def create():

    user = current_user()

    data = (
        request.form.to_dict()
        if request.form
        else (request.get_json(silent=True) or {})
    )

    title = (data.get("title") or "").strip()

    if not title:
        return jsonify(
            success=False,
            message="Activity title is required"
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # -------------------------------------------------
            # ADMIN
            # Automatically use assigned school
            # -------------------------------------------------
            if user["role"] == "ADMIN":

                cursor.execute("""
                    SELECT school_id
                    FROM school_admins
                    WHERE user_id=%s
                    LIMIT 1
                """, (user["user_id"],))

                assignment = cursor.fetchone()

                if not assignment:
                    return jsonify(
                        success=False,
                        message="No school has been assigned to this admin."
                    ), 404

                school_id = assignment["school_id"]

            # -------------------------------------------------
            # SUPERADMIN
            # Can choose school
            # -------------------------------------------------
            else:

                school_id = data.get("school_id")

                if not school_id:
                    return jsonify(
                        success=False,
                        message="school_id is required"
                    ), 400

            # Check school exists
            cursor.execute(
                "SELECT id FROM schools WHERE id=%s",
                (school_id,)
            )

            school = cursor.fetchone()

            if not school:
                return jsonify(
                    success=False,
                    message="School not found"
                ), 404

            image = None

            if request.files.get("image"):
                image = save_upload(
                    request.files.get("image")
                )

            cursor.execute("""
                INSERT INTO activities (
                    school_id,
                    title,
                    category,
                    description,
                    event_date,
                    status,
                    image_url
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                school_id,
                title,
                data.get("category", ""),
                data.get("description", ""),
                data.get("event_date") or None,
                data.get("status", "DRAFT"),
                image
            ))

            activity_id = cursor.lastrowid

        connection.commit()

        return jsonify(
            success=True,
            activity_id=activity_id,
            message="Activity created successfully"
        ), 201

    except Exception as e:

        connection.rollback()

        print("CREATE ACTIVITY ERROR:", e)

        return jsonify(
            success=False,
            message="Failed to create activity",
            error=str(e)
        ), 500

    finally:
        connection.close()


# =========================================================
# ADMIN / SUPERADMIN - UPDATE ACTIVITY
# =========================================================
@activities_bp.put("/<int:iid>")
@auth_required(["SUPERADMIN", "ADMIN"])
def update(iid):

    user = current_user()

    data = (
        request.form.to_dict()
        if request.form
        else (request.get_json(silent=True) or {})
    )

    title = (data.get("title") or "").strip()

    if not title:
        return jsonify(
            success=False,
            message="Activity title is required"
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # -------------------------------------------------
            # ADMIN SECURITY CHECK
            # -------------------------------------------------
            if user["role"] == "ADMIN":

                cursor.execute("""
                    SELECT a.id
                    FROM activities a
                    INNER JOIN school_admins sa
                        ON sa.school_id = a.school_id
                    WHERE a.id=%s
                    AND sa.user_id=%s
                    LIMIT 1
                """, (
                    iid,
                    user["user_id"]
                ))

                activity = cursor.fetchone()

                if not activity:
                    return jsonify(
                        success=False,
                        message="You can only manage activities for your assigned school."
                    ), 403

            else:

                cursor.execute("""
                    SELECT id
                    FROM activities
                    WHERE id=%s
                """, (iid,))

                activity = cursor.fetchone()

                if not activity:
                    return jsonify(
                        success=False,
                        message="Activity not found"
                    ), 404

            image = None

            if request.files.get("image"):
                image = save_upload(
                    request.files.get("image")
                )

            if image:

                cursor.execute("""
                    UPDATE activities
                    SET
                        title=%s,
                        category=%s,
                        description=%s,
                        event_date=%s,
                        status=%s,
                        image_url=%s
                    WHERE id=%s
                """, (
                    title,
                    data.get("category", ""),
                    data.get("description", ""),
                    data.get("event_date") or None,
                    data.get("status", "DRAFT"),
                    image,
                    iid
                ))

            else:

                cursor.execute("""
                    UPDATE activities
                    SET
                        title=%s,
                        category=%s,
                        description=%s,
                        event_date=%s,
                        status=%s
                    WHERE id=%s
                """, (
                    title,
                    data.get("category", ""),
                    data.get("description", ""),
                    data.get("event_date") or None,
                    data.get("status", "DRAFT"),
                    iid
                ))

        connection.commit()

        return jsonify(
            success=True,
            message="Activity updated successfully"
        )

    except Exception as e:

        connection.rollback()

        print("UPDATE ACTIVITY ERROR:", e)

        return jsonify(
            success=False,
            message="Failed to update activity",
            error=str(e)
        ), 500

    finally:
        connection.close()


# =========================================================
# ADMIN / SUPERADMIN - DELETE ACTIVITY
# =========================================================
@activities_bp.delete("/<int:iid>")
@auth_required(["SUPERADMIN", "ADMIN"])
def delete(iid):

    user = current_user()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # ADMIN can delete only own school's activity
            if user["role"] == "ADMIN":

                cursor.execute("""
                    SELECT a.id
                    FROM activities a
                    INNER JOIN school_admins sa
                        ON sa.school_id=a.school_id
                    WHERE a.id=%s
                    AND sa.user_id=%s
                    LIMIT 1
                """, (
                    iid,
                    user["user_id"]
                ))

                activity = cursor.fetchone()

                if not activity:
                    return jsonify(
                        success=False,
                        message="You can only delete activities for your assigned school."
                    ), 403

            cursor.execute(
                "DELETE FROM activities WHERE id=%s",
                (iid,)
            )

        connection.commit()

        return jsonify(
            success=True,
            message="Activity deleted successfully"
        )

    except Exception as e:

        connection.rollback()

        print("DELETE ACTIVITY ERROR:", e)

        return jsonify(
            success=False,
            message="Failed to delete activity",
            error=str(e)
        ), 500

    finally:
        connection.close()