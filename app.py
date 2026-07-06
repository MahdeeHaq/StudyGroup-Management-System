"""
Study Group Management System
CSE-224 Database Management System Lab

Flask backend that exposes a small JSON REST API on top of MySQL
and serves a single-page frontend (templates/index.html).
"""

from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# --------------------------------------------------------------
# Database configuration
# Update these values to match your local MySQL / XAMPP setup.
# --------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # XAMPP default MySQL root password is empty
    "database": "study_group_db",
}


def get_connection():
    """Open and return a new MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def run_query(query, params=None, fetch=False, fetch_one=False, commit=False):
    """
    Small helper so every route doesn't repeat connect/cursor/close logic.
    """
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


# ================================================================
# Page route
# ================================================================
@app.route("/")
def index():
    return render_template("index.html")


# ================================================================
# SUBJECTS  (CRUD)
# ================================================================
@app.route("/api/subjects", methods=["GET"])
def get_subjects():
    try:
        rows = run_query("SELECT * FROM subjects ORDER BY subject_name", fetch=True)
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/subjects", methods=["POST"])
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
def delete_subject(subject_id):
    try:
        run_query("DELETE FROM subjects WHERE subject_id=%s", (subject_id,), commit=True)
        return jsonify({"message": "Subject deleted"})
    except Error as e:
        # Likely a foreign key restriction (subject still used by a study group)
        return jsonify({"error": "Cannot delete: this subject is still used by a study group."}), 400


# ================================================================
# MEMBERS  (CRUD)
# ================================================================
@app.route("/api/members", methods=["GET"])
def get_members():
    try:
        rows = run_query("SELECT * FROM members ORDER BY full_name", fetch=True)
        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/members", methods=["POST"])
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
def delete_member(member_id):
    try:
        run_query("DELETE FROM members WHERE member_id=%s", (member_id,), commit=True)
        return jsonify({"message": "Member deleted"})
    except Error as e:
        return jsonify({"error": "Cannot delete: this member organizes or belongs to a study group."}), 400


# ================================================================
# STUDY GROUPS  (CRUD) + membership sub-resource
# ================================================================
GROUP_SELECT = """
    SELECT sg.group_id, sg.group_name, sg.meeting_time, sg.location,
           sg.description, sg.status,
           s.subject_id, s.subject_code, s.subject_name,
           m.member_id AS organizer_id, m.full_name AS organizer_name
    FROM study_groups sg
    JOIN subjects s ON s.subject_id = sg.subject_id
    JOIN members m ON m.member_id = sg.organizer_id
"""


@app.route("/api/groups", methods=["GET"])
def get_groups():
    subject_filter = request.args.get("subject_id")
    try:
        if subject_filter:
            rows = run_query(
                GROUP_SELECT + " WHERE s.subject_id = %s ORDER BY sg.meeting_time",
                (subject_filter,),
                fetch=True,
            )
        else:
            rows = run_query(GROUP_SELECT + " ORDER BY sg.meeting_time", fetch=True)

        # attach member count + member list for each group
        for g in rows:
            members = run_query(
                """SELECT m.member_id, m.full_name FROM group_members gm
                   JOIN members m ON m.member_id = gm.member_id
                   WHERE gm.group_id = %s""",
                (g["group_id"],),
                fetch=True,
            )
            g["members"] = members

        return jsonify(rows)
    except Error as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/groups", methods=["POST"])
def create_group():
    data = request.get_json() or {}
    required = ["group_name", "subject_id", "organizer_id", "meeting_time", "location"]
    if not all((data.get(f) or "").__str__().strip() for f in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400

    try:
        new_id = run_query(
            """INSERT INTO study_groups
               (group_name, subject_id, organizer_id, meeting_time, location, description, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                data["group_name"].strip(),
                data["subject_id"],
                data["organizer_id"],
                data["meeting_time"],
                data["location"].strip(),
                (data.get("description") or "").strip(),
                data.get("status") or "Scheduled",
            ),
            commit=True,
        )
        return jsonify({"group_id": new_id, "message": "Study group created"}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/groups/<int:group_id>", methods=["PUT"])
def update_group(group_id):
    data = request.get_json() or {}
    required = ["group_name", "subject_id", "organizer_id", "meeting_time", "location"]
    if not all((data.get(f) or "").__str__().strip() for f in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400

    try:
        run_query(
            """UPDATE study_groups
               SET group_name=%s, subject_id=%s, organizer_id=%s, meeting_time=%s,
                   location=%s, description=%s, status=%s
               WHERE group_id=%s""",
            (
                data["group_name"].strip(),
                data["subject_id"],
                data["organizer_id"],
                data["meeting_time"],
                data["location"].strip(),
                (data.get("description") or "").strip(),
                data.get("status") or "Scheduled",
                group_id,
            ),
            commit=True,
        )
        return jsonify({"message": "Study group updated"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/groups/<int:group_id>", methods=["DELETE"])
def delete_group(group_id):
    try:
        run_query("DELETE FROM study_groups WHERE group_id=%s", (group_id,), commit=True)
        return jsonify({"message": "Study group deleted"})
    except Error as e:
        return jsonify({"error": str(e)}), 400


# ---- group membership (many-to-many) ----
@app.route("/api/groups/<int:group_id>/members", methods=["POST"])
def add_group_member(group_id):
    data = request.get_json() or {}
    member_id = data.get("member_id")
    if not member_id:
        return jsonify({"error": "member_id is required"}), 400
    try:
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
