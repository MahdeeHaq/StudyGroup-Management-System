"""
Study Group Management System
CSE-224 Database Management System Lab

Flask backend exposing a JSON REST API on top of MySQL, plus:
- Admin login (session-based) gating create/edit/delete of
  subjects, members, and study groups
- File uploads ("materials") attached to a study group, open to
  any visitor (not admin-gated) since that's the student-facing
  collaboration feature
- Search + subject filtering on study groups
- A simple max_members capacity check when joining a group
"""

import os
import uuid
from functools import wraps

from flask import Flask, request, jsonify, render_template, session, send_from_directory
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# NOTE: change this to something private before deploying anywhere
# public. For a local lab project running on your own machine this
# is fine as-is.
app.secret_key = "dev-secret-key-change-this-before-any-real-deployment"

# --------------------------------------------------------------
# Database configuration
# --------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # XAMPP default MySQL root password is empty
    "database": "study_group_db",
}

# --------------------------------------------------------------
# File upload configuration
# --------------------------------------------------------------
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB per file
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
    "txt", "png", "jpg", "jpeg", "gif", "zip",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def run_query(query, params=None, fetch=False, fetch_one=False, commit=False):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch:
            result = cursor.fetchall()

        if commit:
            conn.commit()
            result = cursor.lastrowid

        cursor.close()
        return result
    except Error as e:
        raise e
    finally:
        if conn and conn.is_connected():
            conn.close()


def ensure_default_admin():
    """Create a default admin account the first time the app runs
    against a fresh database. Safe to call on every startup."""
    try:
        existing = run_query("SELECT admin_id FROM admins LIMIT 1", fetch_one=True)
        if not existing:
            run_query(
                "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
                ("admin", generate_password_hash("admin123")),
                commit=True,
            )
            print("Created default admin -> username: admin | password: admin123")
            print("Change this password once logged in, or edit the admins table directly.")
    except Error as e:
        print(f"Could not check/create default admin (is MySQL running? Did you load schema.sql?): {e}")


def login_required(f):
    """Blocks a route unless an admin is logged in (session-based)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return jsonify({"error": "Admin login required for this action"}), 401
        return f(*args, **kwargs)
    return wrapper


# ================================================================
# Page route
# ================================================================
@app.route("/")
def index():
    return render_template("index.html")


# ================================================================
# ADMIN AUTH
# ================================================================
@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    if session.get("admin_id"):
        return jsonify({"logged_in": True, "username": session.get("admin_username")})
    return jsonify({"logged_in": False})


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        admin = run_query("SELECT * FROM admins WHERE username = %s", (username,), fetch_one=True)
    except Error as e:
        return jsonify({"error": str(e)}), 500

    if not admin or not check_password_hash(admin["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["admin_id"] = admin["admin_id"]
    session["admin_username"] = admin["username"]
    return jsonify({"message": "Logged in", "username": admin["username"]})


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/admin/stats", methods=["GET"])
@login_required
def admin_stats():
    try:
        stats = {
            "subjects": run_query("SELECT COUNT(*) AS c FROM subjects", fetch_one=True)["c"],
            "members": run_query("SELECT COUNT(*) AS c FROM members", fetch_one=True)["c"],
            "groups": run_query("SELECT COUNT(*) AS c FROM study_groups", fetch_one=True)["c"],
            "materials": run_query("SELECT COUNT(*) AS c FROM materials", fetch_one=True)["c"],
        }
        return jsonify(stats)
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# SUBJECTS  (CRUD — writes require admin login)
# ================================================================
@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    try:
        rows = run_query("SELECT * FROM subjects ORDER BY subject_name", fetch=True)
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/subjects", methods=["POST"])
@login_required
def create_subject():
    data = request.get_json() or {}
    code = (data.get("subject_code") or "").strip()
    name = (data.get("subject_name") or "").strip()

    if not code or not name:
        return jsonify({"error": "subject_code and subject_name are required"}), 400

    try:
        new_id = run_query(
            "INSERT INTO subjects (subject_code, subject_name) VALUES (%s, %s)",
            (code, name),
            commit=True,
        )
        return jsonify({"subject_id": new_id, "subject_code": code, "subject_name": name}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/subjects/<int:subject_id>", methods=["PUT"])
@login_required
def update_subject(subject_id):
    data = request.get_json() or {}
    code = (data.get("subject_code") or "").strip()
    name = (data.get("subject_name") or "").strip()

    if not code or not name:
        return jsonify({"error": "subject_code and subject_name are required"}), 400

    try:
        run_query(
            "UPDATE subjects SET subject_code=%s, subject_name=%s WHERE subject_id=%s",
            (code, name, subject_id),
            commit=True,
        )
        return jsonify({"message": "Subject updated"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
@login_required
def delete_subject(subject_id):
    try:
        run_query("DELETE FROM subjects WHERE subject_id=%s", (subject_id,), commit=True)
        return jsonify({"message": "Subject deleted"})
    except Error as e:
        return jsonify({"error": "Cannot delete: this subject is still used by a study group."}), 400


# ================================================================
# MEMBERS  (CRUD — writes require admin login)
# ================================================================
@app.route("/api/members", methods=["GET"])
def get_members():
    try:
        rows = run_query("SELECT * FROM members ORDER BY full_name", fetch=True)
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/members", methods=["POST"])
@login_required
def create_member():
    data = request.get_json() or {}
    name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not name or not email:
        return jsonify({"error": "full_name and email are required"}), 400

    try:
        new_id = run_query(
            "INSERT INTO members (full_name, email, phone) VALUES (%s, %s, %s)",
            (name, email, phone),
            commit=True,
        )
        return jsonify({"member_id": new_id, "full_name": name, "email": email, "phone": phone}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/members/<int:member_id>", methods=["PUT"])
@login_required
def update_member(member_id):
    data = request.get_json() or {}
    name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not name or not email:
        return jsonify({"error": "full_name and email are required"}), 400

    try:
        run_query(
            "UPDATE members SET full_name=%s, email=%s, phone=%s WHERE member_id=%s",
            (name, email, phone, member_id),
            commit=True,
        )
        return jsonify({"message": "Member updated"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/members/<int:member_id>", methods=["DELETE"])
@login_required
def delete_member(member_id):
    try:
        run_query("DELETE FROM members WHERE member_id=%s", (member_id,), commit=True)
        return jsonify({"message": "Member deleted"})
    except Error as e:
        return jsonify({"error": "Cannot delete: this member organizes, belongs to, or uploaded materials to a study group."}), 400


# ================================================================
# STUDY GROUPS  (CRUD — writes require admin login)
# ================================================================
GROUP_SELECT = """
    SELECT sg.group_id, sg.group_name, sg.meeting_time, sg.location,
           sg.description, sg.status, sg.max_members,
           s.subject_id, s.subject_code, s.subject_name,
           m.member_id AS organizer_id, m.full_name AS organizer_name
    FROM study_groups sg
    JOIN subjects s ON s.subject_id = sg.subject_id
    JOIN members m ON m.member_id = sg.organizer_id
"""


@app.route("/api/groups", methods=["GET"])
def get_groups():
    subject_filter = request.args.get("subject_id")
    search = (request.args.get("search") or "").strip()

    clauses = []
    params = []
    if subject_filter:
        clauses.append("s.subject_id = %s")
        params.append(subject_filter)
    if search:
        clauses.append("(sg.group_name LIKE %s OR sg.location LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like])

    query = GROUP_SELECT
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY sg.meeting_time"

    try:
        rows = run_query(query, tuple(params), fetch=True)

        for g in rows:
            g["members"] = run_query(
                """SELECT m.member_id, m.full_name FROM group_members gm
                   JOIN members m ON m.member_id = gm.member_id
                   WHERE gm.group_id = %s""",
                (g["group_id"],),
                fetch=True,
            )
            g["materials"] = run_query(
                """SELECT ma.material_id, ma.original_filename, ma.stored_filename,
                          ma.description, ma.uploaded_at, m.full_name AS uploaded_by_name
                   FROM materials ma
                   JOIN members m ON m.member_id = ma.uploaded_by
                   WHERE ma.group_id = %s
                   ORDER BY ma.uploaded_at DESC""",
                (g["group_id"],),
                fetch=True,
            )

        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/groups", methods=["POST"])
@login_required
def create_group():
    data = request.get_json() or {}
    required = ["group_name", "subject_id", "organizer_id", "meeting_time", "location"]
    if not all((data.get(f) or "").__str__().strip() for f in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400

    try:
        new_id = run_query(
            """INSERT INTO study_groups
               (group_name, subject_id, organizer_id, meeting_time, location, description, max_members, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                data["group_name"].strip(),
                data["subject_id"],
                data["organizer_id"],
                data["meeting_time"],
                data["location"].strip(),
                (data.get("description") or "").strip(),
                int(data.get("max_members") or 8),
                data.get("status") or "Scheduled",
            ),
            commit=True,
        )
        # The organizer is automatically a member of the group they organize.
        run_query(
            "INSERT IGNORE INTO group_members (group_id, member_id) VALUES (%s, %s)",
            (new_id, data["organizer_id"]),
            commit=True,
        )
        return jsonify({"group_id": new_id, "message": "Study group created"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/groups/<int:group_id>", methods=["PUT"])
@login_required
def update_group(group_id):
    data = request.get_json() or {}
    required = ["group_name", "subject_id", "organizer_id", "meeting_time", "location"]
    if not all((data.get(f) or "").__str__().strip() for f in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400

    try:
        run_query(
            """UPDATE study_groups
               SET group_name=%s, subject_id=%s, organizer_id=%s, meeting_time=%s,
                   location=%s, description=%s, max_members=%s, status=%s
               WHERE group_id=%s""",
            (
                data["group_name"].strip(),
                data["subject_id"],
                data["organizer_id"],
                data["meeting_time"],
                data["location"].strip(),
                (data.get("description") or "").strip(),
                int(data.get("max_members") or 8),
                data.get("status") or "Scheduled",
                group_id,
            ),
            commit=True,
        )
        # Make sure the (possibly new) organizer is a member of the group.
        run_query(
            "INSERT IGNORE INTO group_members (group_id, member_id) VALUES (%s, %s)",
            (group_id, data["organizer_id"]),
            commit=True,
        )
        return jsonify({"message": "Study group updated"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/groups/<int:group_id>", methods=["DELETE"])
@login_required
def delete_group(group_id):
    try:
        run_query("DELETE FROM study_groups WHERE group_id=%s", (group_id,), commit=True)
        return jsonify({"message": "Study group deleted"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


# ---- group membership (many-to-many) — open to any visitor ----
@app.route("/api/groups/<int:group_id>/members", methods=["POST"])
def add_group_member(group_id):
    data = request.get_json() or {}
    member_id = data.get("member_id")
    if not member_id:
        return jsonify({"error": "member_id is required"}), 400

    try:
        group = run_query(
            "SELECT max_members FROM study_groups WHERE group_id=%s", (group_id,), fetch_one=True
        )
        if not group:
            return jsonify({"error": "Study group not found"}), 404

        current_count = run_query(
            "SELECT COUNT(*) AS c FROM group_members WHERE group_id=%s", (group_id,), fetch_one=True
        )["c"]

        if current_count >= group["max_members"]:
            return jsonify({"error": f"This group is full ({group['max_members']} members max)."}), 400

        run_query(
            "INSERT IGNORE INTO group_members (group_id, member_id) VALUES (%s, %s)",
            (group_id, member_id),
            commit=True,
        )
        return jsonify({"message": "Member added to group"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/groups/<int:group_id>/members/<int:member_id>", methods=["DELETE"])
def remove_group_member(group_id, member_id):
    try:
        run_query(
            "DELETE FROM group_members WHERE group_id=%s AND member_id=%s",
            (group_id, member_id),
            commit=True,
        )
        return jsonify({"message": "Member removed from group"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


# ================================================================
# MATERIALS — file uploads attached to a study group
# Open to any visitor (this is the collaborative student feature,
# not gated behind admin login).
# ================================================================
@app.route("/api/groups/<int:group_id>/materials", methods=["POST"])
def upload_material(group_id):
    if "file" not in request.files:
        return jsonify({"error": "No file was included in the upload"}), 400

    file = request.files["file"]
    uploaded_by = request.form.get("uploaded_by")
    description = (request.form.get("description") or "").strip()

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not uploaded_by:
        return jsonify({"error": "uploaded_by (member) is required"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Allowed: " + ", ".join(sorted(ALLOWED_EXTENSIONS))}), 400

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(UPLOAD_FOLDER, stored_name))

    try:
        new_id = run_query(
            """INSERT INTO materials (group_id, uploaded_by, original_filename, stored_filename, description)
               VALUES (%s, %s, %s, %s, %s)""",
            (group_id, uploaded_by, original_name, stored_name, description),
            commit=True,
        )
        return jsonify({"material_id": new_id, "message": "Material uploaded"}), 201
    except Error as e:
        # roll back the saved file if the DB insert failed
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, stored_name))
        except OSError:
            pass
        return jsonify({"error": str(e)}), 400


@app.route("/api/materials/<int:material_id>", methods=["DELETE"])
@login_required
def delete_material(material_id):
    try:
        material = run_query(
            "SELECT stored_filename FROM materials WHERE material_id=%s", (material_id,), fetch_one=True
        )
        run_query("DELETE FROM materials WHERE material_id=%s", (material_id,), commit=True)
        if material:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, material["stored_filename"]))
            except OSError:
                pass
        return jsonify({"message": "Material deleted"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/uploads/<path:stored_filename>")
def download_material(stored_filename):
    return send_from_directory(UPLOAD_FOLDER, stored_filename)


if __name__ == "__main__":
    ensure_default_admin()
    app.run(debug=True, port=5000)
