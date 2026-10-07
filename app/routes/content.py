from flask import Blueprint, request, jsonify, send_from_directory, current_app
from ..db import get_connection
from ..utils import auth_required, current_user, save_upload
import json

content_bp = Blueprint("content", __name__)

TABLES = {
    "features": "features",
    "facilities": "facilities",
    "qualifications": "qualifications",
}


def get_admin_school_id():
    user = current_user()

    if user["role"] != "ADMIN":
        return None

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT school_id
                FROM school_admins
                WHERE user_id=%s
                LIMIT 1
            """, (user["user_id"],))

            row = cursor.fetchone()

        return row["school_id"] if row else None

    finally:
        connection.close()


# =========================================================
# GET CONTENT
# =========================================================
@content_bp.get("/<kind>/<int:sid>")
def get_items(kind, sid):

    table = TABLES.get(kind)

    if not table:
        return jsonify(
            success=False,
            message="Invalid content type"
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM {table}
                WHERE school_id=%s
                ORDER BY id DESC
                """,
                (sid,)
            )

            rows = cursor.fetchall()

        return jsonify(
            success=True,
            items=rows
        )

    finally:
        connection.close()


# =========================================================
# ADMIN - GET MY SCHOOL CONTENT
# =========================================================
@content_bp.get("/my-school/<kind>")
@auth_required(["ADMIN"])
def get_my_school_content(kind):

    table = TABLES.get(kind)

    if not table:
        return jsonify(
            success=False,
            message="Invalid content type"
        ), 400

    school_id = get_admin_school_id()

    if not school_id:
        return jsonify(
            success=False,
            message="No school has been assigned to this admin."
        ), 404

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM {table}
                WHERE school_id=%s
                ORDER BY id DESC
                """,
                (school_id,)
            )

            rows = cursor.fetchall()

        return jsonify(
            success=True,
            items=rows,
            school_id=school_id
        )

    finally:
        connection.close()


# =========================================================
# CREATE CONTENT
# =========================================================
@content_bp.post("/<kind>")
@auth_required(["SUPERADMIN", "ADMIN"])
def create_item(kind):

    table = TABLES.get(kind)

    if not table:
        return jsonify(
            success=False,
            message="Invalid content type"
        ), 400

    data = request.get_json(silent=True) or {}

    user = current_user()

    if user["role"] == "ADMIN":
        school_id = get_admin_school_id()

        if not school_id:
            return jsonify(
                success=False,
                message="No school has been assigned to this admin."
            ), 404
    else:
        school_id = data.get("school_id")

        if not school_id:
            return jsonify(
                success=False,
                message="school_id is required"
            ), 400

    name = (
        data.get("name")
        or data.get("title")
        or data.get("label")
    )

    description = data.get("description", "")

    if not name:
        return jsonify(
            success=False,
            message="Name/title is required"
        ), 400

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO {table}
                (school_id, name, description)
                VALUES (%s, %s, %s)
                """,
                (
                    school_id,
                    name,
                    description
                )
            )

            item_id = cursor.lastrowid

        connection.commit()

        return jsonify(
            success=True,
            message="Created successfully",
            id=item_id
        ), 201

    except Exception as e:
        connection.rollback()

        return jsonify(
            success=False,
            message="Failed to create content",
            error=str(e)
        ), 500

    finally:
        connection.close()


# =========================================================
# UPDATE CONTENT
# =========================================================
@content_bp.put("/<kind>/<int:iid>")
@auth_required(["SUPERADMIN", "ADMIN"])
def update_item(kind, iid):

    table = TABLES.get(kind)

    if not table:
        return jsonify(
            success=False,
            message="Invalid content type"
        ), 400

    data = request.get_json(silent=True) or {}

    name = (
        data.get("name")
        or data.get("title")
        or data.get("label")
    )

    description = data.get("description", "")

    if not name:
        return jsonify(
            success=False,
            message="Name/title is required"
        ), 400

    user = current_user()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            if user["role"] == "ADMIN":

                school_id = get_admin_school_id()

                if not school_id:
                    return jsonify(
                        success=False,
                        message="No school has been assigned to this admin."
                    ), 404

                cursor.execute(
                    f"""
                    UPDATE {table}
                    SET name=%s,
                        description=%s
                    WHERE id=%s
                    AND school_id=%s
                    """,
                    (
                        name,
                        description,
                        iid,
                        school_id
                    )
                )

            else:

                cursor.execute(
                    f"""
                    UPDATE {table}
                    SET name=%s,
                        description=%s
                    WHERE id=%s
                    """,
                    (
                        name,
                        description,
                        iid
                    )
                )

        connection.commit()

        return jsonify(
            success=True,
            message="Updated successfully"
        )

    except Exception as e:
        connection.rollback()

        return jsonify(
            success=False,
            message="Failed to update content",
            error=str(e)
        ), 500

    finally:
        connection.close()


# =========================================================
# DELETE CONTENT
# =========================================================
@content_bp.delete("/<kind>/<int:iid>")
@auth_required(["SUPERADMIN", "ADMIN"])
def delete_item(kind, iid):

    table = TABLES.get(kind)

    if not table:
        return jsonify(
            success=False,
            message="Invalid content type"
        ), 400

    user = current_user()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            if user["role"] == "ADMIN":

                school_id = get_admin_school_id()

                if not school_id:
                    return jsonify(
                        success=False,
                        message="No school has been assigned to this admin."
                    ), 404

                cursor.execute(
                    f"""
                    DELETE FROM {table}
                    WHERE id=%s
                    AND school_id=%s
                    """,
                    (
                        iid,
                        school_id
                    )
                )

            else:

                cursor.execute(
                    f"""
                    DELETE FROM {table}
                    WHERE id=%s
                    """,
                    (iid,)
                )

        connection.commit()

        return jsonify(
            success=True,
            message="Deleted successfully"
        )

    except Exception as e:
        connection.rollback()

        return jsonify(
            success=False,
            message="Failed to delete content",
            error=str(e)
        ), 500

    finally:
        connection.close()


# =========================================================
# GET CONTACT
# =========================================================
@content_bp.get("/contacts/<int:sid>")
def get_contact(sid):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM contacts
                WHERE school_id=%s
                LIMIT 1
                """,
                (sid,)
            )

            contact = cursor.fetchone()

        return jsonify(
            success=True,
            contact=contact
        )

    finally:
        connection.close()


# =========================================================
# CREATE / UPDATE CONTACT
# =========================================================
@content_bp.post("/contacts")
@auth_required(["SUPERADMIN", "ADMIN"])
def save_contact():

    data = request.get_json(silent=True) or {}

    user = current_user()

    if user["role"] == "ADMIN":
        school_id = get_admin_school_id()

        if not school_id:
            return jsonify(
                success=False,
                message="No school has been assigned to this admin."
            ), 404
    else:
        school_id = data.get("school_id")

        if not school_id:
            return jsonify(
                success=False,
                message="school_id is required"
            ), 400

    phone = data.get("phone", "")
    alternate_phone = data.get("alternate_phone", "")
    email = data.get("email", "")
    address = data.get("address", "")
    website = data.get("website", "")
    social_links = data.get("social_links")

    if isinstance(social_links, (dict, list)):
        social_links = json.dumps(social_links)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT id
                FROM contacts
                WHERE school_id=%s
                LIMIT 1
                """,
                (school_id,)
            )

            existing = cursor.fetchone()

            if existing:

                cursor.execute(
                    """
                    UPDATE contacts
                    SET phone=%s,
                        alternate_phone=%s,
                        email=%s,
                        address=%s,
                        website=%s,
                        social_links=%s
                    WHERE school_id=%s
                    """,
                    (
                        phone,
                        alternate_phone,
                        email,
                        address,
                        website,
                        social_links,
                        school_id
                    )
                )

                contact_id = existing["id"]

            else:

                cursor.execute(
                    """
                    INSERT INTO contacts
                    (
                        school_id,
                        phone,
                        alternate_phone,
                        email,
                        address,
                        website,
                        social_links
                    )
                    VALUES
                    (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        school_id,
                        phone,
                        alternate_phone,
                        email,
                        address,
                        website,
                        social_links
                    )
                )

                contact_id = cursor.lastrowid

        connection.commit()

        return jsonify(
            success=True,
            message="Contact saved successfully",
            contact_id=contact_id
        )

    finally:
        connection.close()


# =========================================================
# DELETE CONTACT
# =========================================================
@content_bp.delete("/contacts/<int:sid>")
@auth_required(["SUPERADMIN", "ADMIN"])
def delete_contact(sid):

    user = current_user()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            if user["role"] == "ADMIN":

                school_id = get_admin_school_id()

                if not school_id:
                    return jsonify(
                        success=False,
                        message="No school has been assigned to this admin."
                    ), 404

                if int(sid) != int(school_id):
                    return jsonify(
                        success=False,
                        message="You can only manage your assigned school's contact."
                    ), 403

            cursor.execute(
                """
                DELETE FROM contacts
                WHERE school_id=%s
                """,
                (sid,)
            )

        connection.commit()

        return jsonify(
            success=True,
            message="Contact deleted successfully"
        )

    finally:
        connection.close()


# =========================================================
# SCHOOL IMAGES
# =========================================================
@content_bp.get("/images/<int:sid>")
def images(sid):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM school_images
                WHERE school_id=%s
                ORDER BY id DESC
                """,
                (sid,)
            )

            rows = cursor.fetchall()

        return jsonify(
            success=True,
            images=rows
        )

    finally:
        connection.close()


# =========================================================
# UPLOAD IMAGE
# =========================================================
@content_bp.post("/images")
@auth_required(["SUPERADMIN", "ADMIN"])
def upload_image():
    user = current_user()

    try:
        if user["role"] == "ADMIN":
            school_id = get_admin_school_id()

            if not school_id:
                return jsonify(
                    success=False,
                    message="No school has been assigned to this admin."
                ), 404
        else:
            school_id = request.form.get("school_id")

            if not school_id:
                return jsonify(
                    success=False,
                    message="school_id is required"
                ), 400

        image = request.files.get("image")

        if not image or not image.filename:
            return jsonify(
                success=False,
                message="Please select an image"
            ), 400

        try:
            filename = save_upload(image)
        except ValueError as error:
            return jsonify(
                success=False,
                message=str(error)
            ), 400

        if not filename:
            return jsonify(
                success=False,
                message="Failed to save image"
            ), 500

        connection = get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM schools WHERE id=%s",
                    (school_id,)
                )

                if not cursor.fetchone():
                    return jsonify(
                        success=False,
                        message="School not found"
                    ), 404

                cursor.execute("""
                    INSERT INTO school_images
                    (school_id, title, image_path, image_url)
                    VALUES (%s, %s, %s, %s)
                """, (
                    school_id,
                    request.form.get("title", "").strip(),
                    filename,
                    f"/api/content/uploads/{filename}"
                ))

                image_id = cursor.lastrowid

            connection.commit()

        except Exception as error:
            connection.rollback()
            print("IMAGE DATABASE ERROR:", error)

            return jsonify(
                success=False,
                message=f"Database error: {str(error)}"
            ), 500

        finally:
            connection.close()

        return jsonify(
            success=True,
            message="Image uploaded successfully",
            image_id=image_id,
            image_path=filename
        ), 201

    except Exception as error:
        print("IMAGE UPLOAD ERROR:", error)

        return jsonify(
            success=False,
            message=f"Image upload failed: {str(error)}"
        ), 500


@content_bp.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )