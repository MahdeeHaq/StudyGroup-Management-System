# Study Group Management System

CSE-224 Database Management System Lab — full-stack CRUD project.

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python (Flask)
- **Database:** MySQL (via XAMPP / MySQL Workbench)

## Database design

| Table | Purpose | Relationships |
|---|---|---|
| `subjects` | Academic subjects (e.g. CSE-224) | referenced by `study_groups` |
| `members` | Students who organize/join groups | referenced by `study_groups` and `group_members` |
| `study_groups` | A scheduled study session | belongs to one subject, has one organizer (both foreign keys → 1-to-many) |
| `group_members` | Junction table | many-to-many between `study_groups` and `members` |

This gives you a proper relational schema (1-to-many *and* many-to-many) rather than one flat table, which is what a DBMS lab grader wants to see.

---

## 1. Install prerequisites

1. **Install XAMPP** (includes MySQL + phpMyAdmin): https://www.apachefriends.org/download.html
   - After installing, open the XAMPP Control Panel and click **Start** next to **MySQL**.
2. **Install Python 3.10+**: https://www.python.org/downloads/
   - On Windows, tick "Add Python to PATH" during install.
3. (Optional but recommended) **Install MySQL Workbench** for a visual way to inspect your tables: https://dev.mysql.com/downloads/workbench/

## 2. Create the database

You have two options — pick whichever you're more comfortable with.

**Option A — phpMyAdmin (comes with XAMPP)**
1. With MySQL running in XAMPP, open `http://localhost/phpmyadmin` in your browser.
2. Click the **SQL** tab.
3. Open `schema.sql` from this project, copy its entire contents, paste into the SQL box, and click **Go**.

**Option B — MySQL Workbench**
1. Open MySQL Workbench and connect to your local MySQL instance (default user `root`, no password, if using XAMPP's default).
2. Open `schema.sql` as a script (File → Open SQL Script).
3. Click the lightning bolt icon to execute the whole script.

Either way, this creates a `study_group_db` database with all 4 tables and some sample data already in it, so the app has something to display immediately.

## 3. Set up the Python backend

Open a terminal in this project folder and run:

```bash
# create a virtual environment (recommended)
python -m venv venv

# activate it
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# install dependencies
pip install -r requirements.txt
```

## 4. Configure the database connection

Open `app.py` and check the `DB_CONFIG` dictionary near the top:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # XAMPP default is an empty password
    "database": "study_group_db",
}
```

If your MySQL root user has a password set, update `"password"` accordingly.

## 5. Run the app

```bash
python app.py
```

You should see output like `Running on http://127.0.0.1:5000`. Open that URL in your browser.

## 6. Using the app

- **Study Groups tab:** browse/search/filter study sessions, join or leave a group, and upload materials — open to any visitor.
- **Subjects tab / Members tab:** browse the lists — open to any visitor.
- **Creating, editing, or deleting** subjects, members, or study groups requires an **admin login** (see below).

Deleting a subject or member that's still referenced by a study group will fail on purpose — this demonstrates that your foreign key constraints (`ON DELETE RESTRICT`) are working correctly, which is exactly the kind of data integrity a DBMS course wants you to show.

## 7. Admin login

Click **Admin login** in the top-right of the page. A default account is created automatically the first time you run `python app.py`:

```
username: admin
password: admin123
```

Logged in as admin, you can create/edit/delete subjects, members, and study groups, and see a small **Dashboard** with row counts across all 4 tables. Log out with the **Logout** button — everyone else only sees the read-only view plus joining groups and uploading materials.

To change the default password, either add a "change password" flow yourself, or directly update the `admins` table in phpMyAdmin with a new bcrypt/werkzeug hash generated in a Python shell:

```python
from werkzeug.security import generate_password_hash
print(generate_password_hash("your-new-password"))
```
Paste the result into the `password_hash` column for the `admin` row.

## 8. Materials (file uploads)

Any visitor can upload a file (PDF, Word, PowerPoint, Excel, images, or zip, up to 16MB) to a study group via **+ Upload material** on that group's card. Files are stored on disk in `static/uploads/` and tracked in the `materials` table (linked to the group and to whichever member uploaded it). Only an admin can delete a material.

## 9. Capacity and "This week"

- Each study group has a **max members** value; once a group reaches that count, joining is blocked both in the UI and by the backend (so it can't be bypassed by calling the API directly).
- Groups meeting within the next 7 days get an automatic **"This week"** badge — purely a frontend calculation based on `meeting_time`, no extra data needed.

## Project structure

```
study-group-system/
├── app.py                  # Flask backend + REST API
├── schema.sql               # MySQL schema + sample data
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/script.js
```

## For your GitHub submission

1. `git init`, commit all these files, push to a new GitHub repo.
2. Include `schema.sql` in the repo root so graders can see your database design directly.
3. Add a short section to this README (or your report) with a screenshot of your ER-style table relationships if your instructor wants one — you can generate this quickly from MySQL Workbench's **Database → Reverse Engineer** feature.
