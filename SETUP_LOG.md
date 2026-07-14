# Study Group Management System — Setup Log

Project: CSE-224 DBMS Lab, Metropolitan University
Stack: Flask (Python) + MySQL (XAMPP) + HTML/CSS/JS
Deadline: Final submission July 12, 2026 (source code + SQL on GitHub, link in Google Classroom, PPT)

---

## What the project is

A "Study Group Ledger" web app with full CRUD (Create, Read, Update, Delete) across 4 related MySQL tables:

| Table | Purpose |
|---|---|
| `subjects` | Academic subjects (e.g. CSE-224) |
| `members` | Students who organize/join groups |
| `study_groups` | A scheduled study session — linked to one subject + one organizer |
| `group_members` | Junction table — many-to-many between groups and members |

Project files delivered as `study-group-system.zip`:
```
study-group-system/
├── app.py              # Flask backend + REST API
├── schema.sql           # MySQL schema + sample data
├── requirements.txt
├── templates/index.html
└── static/css/style.css, static/js/script.js
```

---

## Setup progress so far

**✅ Step 1 — Confirmed Python works**
Ran `python --version` in Command Prompt — worked fine.

**✅ Step 2 — Started MySQL in XAMPP**
Opened XAMPP Control Panel, clicked Start next to MySQL — turned green/running.

**✅ Step 3 — Extracted project files**
Unzipped `study-group-system.zip` into a folder (e.g. Downloads or Documents) so `app.py`, `schema.sql`, `templates/`, `static/` are all accessible.

**✅ Step 4 — Created the database via phpMyAdmin**
- Initially `http://localhost/phpmyadmin` didn't load → fixed by also starting **Apache** in XAMPP Control Panel (phpMyAdmin is served by Apache, not MySQL).
- Pasted contents of `schema.sql` into the SQL tab in phpMyAdmin, clicked **Go**.
- Saw a harmless note: *"#1008 Can't drop database `study_group_db`; database doesn't exist"* — this is expected on first run (the script tries to clear out any old version first) and is not an error.
- Confirmed: `study_group_db` now appears in phpMyAdmin with all 4 tables inside.

**🔄 Step 5 — Installing Python packages (in progress)**
- Opened Command Prompt, navigated into the `study-group-system` folder using `cd` (drag-and-drop the folder into the terminal to auto-fill the path).
- Ran `pip install -r requirements.txt` → got `'pip' is not recognized`.
- **Fix:** use `python -m pip install -r requirements.txt` instead (calls pip through Python directly, sidesteps the PATH issue).
- Waiting to confirm this installs Flask + mysql-connector-python successfully.

**⬜ Step 6 — Confirm database connection settings**
Open `app.py` in Notepad, check near the top:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",   # should stay empty — XAMPP default has no root password
    "database": "study_group_db",
}
```
No changes needed unless you've manually set a MySQL root password before.

**⬜ Step 7 — Run the app (not done yet)**
In Command Prompt, still inside the project folder:
```
python app.py
```
Should print something like `Running on http://127.0.0.1:5000`. Then open that address in a browser to see the app.

**⬜ Step 8 — Push to GitHub (not done yet)**
Create a repo, commit all project files (including `schema.sql`), push, and share the link in Google Classroom before July 12.

**⬜ Step 9 — Build the PPT (not done yet)**
Still needed for final submission.

---

## MySQL won't start / "database may be corrupt" fix

If MySQL shows red in XAMPP and the Logs button shows errors like:
```
InnoDB: Page ... log sequence number ... is in the future!
InnoDB: Your database may be corrupt...
```
This usually happens after an unclean shutdown (laptop slept/closed while MySQL was running). Fix:
1. Stop MySQL in XAMPP Control Panel (if running).
2. Go to `C:\xampp\mysql\`, rename the `data` folder to `data_old`.
3. Copy the `backup` folder in that same location, paste it, rename the copy to `data`.
4. Start MySQL again in XAMPP — should go green with no errors.
5. Re-run `schema.sql` in phpMyAdmin (`http://localhost/phpmyadmin` → SQL tab → paste → Go) since this resets the database to empty.

## Permanent fix for repeated MySQL corruption

This happened twice — root cause is almost certainly Windows **Fast Startup**, which doesn't fully shut down the PC and can corrupt MySQL's data files if MySQL was running when the laptop was closed/shut down.

**One-time permanent fix:**
1. Control Panel → Hardware and Sound → Power Options
2. "Choose what the power buttons do" → "Change settings that are currently unavailable"
3. Uncheck "Turn on fast startup (recommended)" → Save changes

**Ongoing habit:** click **Stop** (or **Quit**) on MySQL/Apache in XAMPP Control Panel before closing the laptop lid or shutting down, rather than just closing it while MySQL is running.

## Common gotchas learned so far

- `python`/`pip` "not recognized" → try `python -m pip ...` instead of `pip ...` directly.
- phpMyAdmin unreachable → Apache needs to be running in XAMPP too, not just MySQL.
- A "#1008 note" about dropping a non-existent database is expected on first run — not an error.
- Don't confuse the **database name** (`study_group_db`, inside phpMyAdmin) with the **project folder name** (`study-group-system`, on your hard drive) — they're two different things.
