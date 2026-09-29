from flask import Flask, request, redirect,send_file,session
import sqlite3
import os
import secrets
import io
import csv
import qrcode
from datetime import date, datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
DATABASE = "mottem_attendance.db"

UPLOAD_FOLDER = "static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():

    db = sqlite3.connect(DATABASE)

    db.row_factory = sqlite3.Row

    return db


def init_db():

    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT,
            phone TEXT,
            email TEXT,
            joining_date TEXT,
            photo TEXT,
            qr_token TEXT UNIQUE,
            attendance_target REAL DEFAULT 90,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            work_date TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()


# ============================================================
# COMMON WEBSITE DESIGN
# ============================================================

def page(content):

    return f"""
<!DOCTYPE html>

<html>

<head>

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>MOTTEM STUDIOS</title>

    <style>
    
 input {{
    width: 100%;
    padding: 13px;
    margin-bottom: 15px;
    background: #111;
    color: white;
    border: 1px solid #444;
    border-radius: 8px;
    font-size: 15px;
}}

input:focus {{
    outline: none;
    border-color: #d4af37;
}}

button {{
    border: none;
    cursor: pointer;
    font-size: 14px;
}}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #101010;
            color: white;
        }}

        /* HEADER */

        .header {{
            background: #181818;
            border-bottom: 1px solid #333;
            padding: 18px 25px;

            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            font-size: 23px;
            font-weight: bold;
            letter-spacing: 2px;
        }}

        .gold {{
            color: #d4af37;
        }}

        .status {{
            color: #aaa;
            font-size: 14px;
        }}


        /* MAIN */

        .container {{
            max-width: 1100px;
            margin: auto;
            padding: 30px 20px;
        }}


        /* WELCOME */

        .welcome {{
            margin-bottom: 30px;
        }}

        .welcome h1 {{
            font-size: 34px;
            margin-bottom: 8px;
        }}

        .welcome p {{
            color: #999;
            font-size: 16px;
        }}


        /* CARDS */

        .grid {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));

            gap: 18px;
        }}

        .card {{
            background: #1b1b1b;
            border: 1px solid #333;
            border-radius: 14px;
            padding: 22px;
        }}

        .card:hover {{
            border-color: #d4af37;
        }}

        .label {{
            color: #999;
            font-size: 13px;
            letter-spacing: 1px;
        }}

        .number {{
            font-size: 36px;
            font-weight: bold;
            margin-top: 12px;
        }}


        /* QUICK ACTIONS */

        .section-title {{
            margin-top: 40px;
            margin-bottom: 18px;
        }}

        .actions {{
            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(180px, 1fr));

            gap: 15px;
        }}

        .action {{
            background: #1b1b1b;
            border: 1px solid #333;
            border-radius: 14px;

            padding: 25px;

            text-decoration: none;
            color: white;

            text-align: center;

            transition: 0.2s;
        }}

        .action:hover {{
            transform: translateY(-3px);
            border-color: #d4af37;
        }}

        .icon {{
            font-size: 30px;
            margin-bottom: 10px;
        }}

        .action-title {{
            font-weight: bold;
            font-size: 15px;
        }}

        .action-text {{
            color: #888;
            font-size: 13px;
            margin-top: 7px;
        }}


        /* BUTTON */

        .btn {{
            display: inline-block;

            padding: 12px 20px;

            border-radius: 8px;

            text-decoration: none;

            font-weight: bold;
        }}

        .gold-btn {{
            background: #d4af37;
            color: #111;
        }}

        /* NAVIGATION */

        .navbar {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 15px;
            justify-content: center;
            background: #151515;
            border-bottom: 1px solid #333;
        }}

        .nav-link {{
            text-decoration: none;
            padding: 10px 14px;
            border: 1px solid #d4af37;
            border-radius: 8px;
            color: white;
            font-weight: bold;
        }}

        .nav-link:hover {{
            background: #d4af37;
            color: #111;
        }}
        /* FOOTER */

        footer {{
            text-align: center;
            color: #666;
            padding: 35px 15px;
            font-size: 13px;
        }}


        /* MOBILE */

        @media (max-width: 600px) {{

            .header {{
                padding: 15px;
            }}

            .logo {{
                font-size: 18px;
            }}

            .status {{
                font-size: 11px;
            }}

            .container {{
                padding: 22px 15px;
            }}

            .welcome h1 {{
                font-size: 27px;
            }}

        }}
         @media (max-width: 600px) {{

    body {{
        padding: 10px;
    }}

    .card {{
        width: 100%;
        box-sizing: border-box;
    }}

    input,
    select,
    button {{
        width: 100%;
        box-sizing: border-box;
    }}

    .btn {{
        display: block;
        width: 100%;
        box-sizing: border-box;
        text-align: center;
        margin: 8px 0;
    }}

    .grid {{
        grid-template-columns: 1fr;
    }}

    h1 {{
        font-size: 28px;
    }}

    h2 {{
        font-size: 21px;
    }}
      .attendance-table {{
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }}  

}}
/* Professional Attendance Tables */
.attendance-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    overflow: hidden;
    border-radius: 12px;
}}

.attendance-table th {{
    background: #d4af37;
    color: #000;
    padding: 14px;
    text-align: left;
    font-weight: bold;
}}

.attendance-table td {{
    padding: 13px;
    border-bottom: 1px solid #333;
    color: #eee;
}}

.attendance-table tr:hover {{
    background: #1c1c1c;
}}

.attendance-table .in {{
    color: #4caf50;
    font-weight: bold;
}}

.attendance-table .out {{
    color: #ff6b6b;
    font-weight: bold;
}}


.attendance-summary {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 15px;
    margin-top: 20px;
}}

.employee-card {{
    background: #1b1b1b;
    border: 1px solid #333;
    border-radius: 16px;
    padding: 22px;
    transition: 0.2s;
}}

.employee-card:hover {{
    border-color: #d4af37;
    transform: translateY(-3px);
}}

.employee-photo {{
    width: 90px;
    height: 90px;
    object-fit: cover;
    border-radius: 50%;
    border: 3px solid #d4af37;
}}

.active-badge {{
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    background: #173b28;
    color: #5fd68a;
    font-size: 12px;
    font-weight: bold;
}}
.employee-status {{
    background: #151515;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 18px;
}}

.employee-status:hover {{
    border-color: #d4af37;
}}

.present {{
    color: #5fd68a;
    font-weight: bold;
}}

.absent {{
    color: #e57373;
    font-weight: bold;
}}

.status-time {{
    color: #999;
    font-size: 13px;
    margin-top: 6px;
}}


    </style>

</head>


<body>



<nav class="navbar">

    <a href="/" class="nav-link">
        🏠 DASHBOARD
    </a>

    <a href="/add" class="nav-link">
        ➕ ADD EMPLOYEE
    </a>

    <a href="/employees" class="nav-link">
        👥 EMPLOYEES
    </a>

    <a href="/attendance-history" class="nav-link">
        📅 ATTENDANCE
    </a>
    <a href="/logout"
   class="nav-link"
   onclick="return confirm('Are you sure you want to logout?');">
    🚪 LOGOUT
</a>

</nav>


<header class="header">

    <div class="logo">

        MOTTEM
        <span class="gold">
            STUDIOS
        </span>

    </div>

    <div class="status">

        ATTENDANCE SYSTEM

    </div>

</header>


<main class="container">

    {content}

</main>


<footer>
    MOTTEM STUDIOS
    •
    Employee Attendance Management System
    <br>
    Founder: <span class="gold">CHALLA SANVITH REDDY</span>
</footer>


</body>

</html>
"""


# ============================================================
# HOME / DASHBOARD
# ============================================================
@app.route("/add", methods=["GET", "POST"])
def add_employee():

    if request.method == "POST":

        employee_id = request.form["employee_id"].strip()

        if not employee_id:
            return page("""
                <div class="card">

                    <h2 class="gold">
                        INVALID EMPLOYEE ID
                    </h2>

                    <p>
                        Employee ID cannot be empty.
                    </p>

                    <a
                        href="/add"
                        class="btn gold-btn"
                    >
                        GO BACK
                    </a>

                </div>
            """)

        name = request.form["name"].strip()
        role = request.form["role"].strip()
        department = request.form.get("department", "")
        phone = request.form.get("phone", "")
        email = request.form.get("email", "")
        joining_date = request.form.get("joining_date", "")

        try:
            target = float(
                request.form.get("target", 90)
            )

            if target < 0 or target > 100:
                target = 90

        except (ValueError, TypeError):
            target = 90

        photo = ""

        uploaded = request.files.get("photo")

        if uploaded and uploaded.filename:

            filename = secure_filename(
                employee_id + "_" + uploaded.filename
            )

            uploaded.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    filename
                )
            )

            photo = filename

        db = get_db()

        try:

            qr_token = secrets.token_urlsafe(32)

            db.execute("""
                INSERT INTO employees
                (
                    employee_id,
                    name,
                    role,
                    department,
                    phone,
                    email,
                    joining_date,
                    photo,
                    qr_token,
                    attendance_target
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                employee_id,
                name,
                role,
                department,
                phone,
                email,
                joining_date,
                photo,
                qr_token,
                target
            ))

            db.commit()

        except sqlite3.IntegrityError:

            db.close()

            return page("""
                <div class="card">

                    <h2>
                        Employee ID Already Exists
                    </h2>

                    <p class="label">
                        Please use a different Employee ID.
                    </p>

                    <a
                        href="/add"
                        class="btn gold-btn"
                    >
                        GO BACK
                    </a>

                </div>
            """)

        db.close()

        return redirect("/")

    return page("""
        <div class="welcome">

            <h1>
                <span class="gold">
                    ADD EMPLOYEE
                </span>
            </h1>

            <p>
                Create a new MOTTEM STUDIOS employee profile.
            </p>

        </div>

        <div class="card">

            <form
                method="post"
                enctype="multipart/form-data"
            >

                <p>Employee ID</p>

                <input
                    name="employee_id"
                    placeholder="MS-AN-002"
                    required
                >

                <p>Full Name</p>

                <input
                    name="name"
                    placeholder="Full Name"
                    required
                >

                <p>Position / Role</p>

                <input
                    name="role"
                    placeholder="Position / Role"
                    required
                >

                <p>Department</p>

                <input
                    name="department"
                    placeholder="Department"
                >

                <p>Phone Number</p>

                <input
                    name="phone"
                    placeholder="Phone Number"
                >

                <p>Email</p>

                <input
                    name="email"
                    type="email"
                    placeholder="Email"
                >

                <p>Joining Date</p>

                <input
                    name="joining_date"
                    type="date"
                >

                <p>Attendance Target %</p>

                <input
                    name="target"
                    type="number"
                    value="90"
                    min="0"
                    max="100"
                >

                <p>
                    <b>Employee Profile Photo</b>
                </p>

                <input
                    name="photo"
                    type="file"
                    accept="image/*"
                >

                <br><br>

                <button
                    type="submit"
                    class="btn gold-btn"
                >
                    CREATE EMPLOYEE
                </button>

            </form>

        </div>
    """)


    
@app.route("/")
def home():

    if not session.get("admin_logged_in"):
        return redirect("/login")

    db = get_db()

    total_employees = db.execute(
        "SELECT COUNT(*) FROM employees"
    ).fetchone()[0]

    today = date.today().isoformat()

    today_attendance = db.execute("""
        SELECT COUNT(DISTINCT employee_id)
        FROM attendance
        WHERE work_date=?
        AND action='IN'
    """, (today,)).fetchone()[0]

    absent_today = total_employees - today_attendance

    if total_employees > 0:
        attendance_rate = round(
            (today_attendance / total_employees) * 100
        )
    else:
        attendance_rate = 0

    today_employees = db.execute("""
        SELECT
            employees.employee_id,
            employees.name,
            attendance.action,
            attendance.timestamp
        FROM employees
        LEFT JOIN attendance
        ON employees.employee_id = attendance.employee_id
        AND attendance.work_date = ?
        AND attendance.action = 'IN'
        AND attendance.id = (
            SELECT MAX(a2.id)
            FROM attendance a2
            WHERE a2.employee_id = employees.employee_id
            AND a2.work_date = ?
            AND a2.action = 'IN'
        )
        WHERE employees.active = 1
        ORDER BY employees.name
    """, (today, today)).fetchall()

    db.close()

    employee_status = ""

    for employee in today_employees:

        if employee["action"] == "IN":

            employee_status += f"""
            <div class="employee-status">

                <div>
                    <b>{employee['name']}</b>
                </div>

                <div class="label">
                    {employee['employee_id']}
                </div>

                <div class="present">
                    🟢 PRESENT
                </div>

                <div class="status-time">
                    Check-in: {employee['timestamp']}
                </div>

            </div>
            """

        else:

            employee_status += f"""
            <div class="employee-status">

                <div>
                    <b>{employee['name']}</b>
                </div>

                <div class="label">
                    {employee['employee_id']}
                </div>

                <div class="absent">
                    🔴 ABSENT
                </div>

                <div class="status-time">
                    No check-in recorded today
                </div>

            </div>
            """

    if not employee_status:

        employee_status = """
        <div class="employee-status">
            <b>No employees registered</b>
        </div>
        """

    return page(f"""

        <div class="welcome">

            <h1>
                Welcome to
                <span class="gold">
                    MOTTEM STUDIOS
                </span>
            </h1>

            <a
                href="/logout"
                class="btn gold-btn"
            >
                🚪 LOGOUT
            </a>

            <p>
                Employee Attendance
                Management System
            </p>

        </div>

        <div class="card">

            <h2>QUICK ACTIONS</h2>

            <a href="/add" class="btn gold-btn">
                ➕ ADD EMPLOYEE
            </a>

           <a href="/employees" class="btn gold-btn">
    👥 VIEW EMPLOYEES
</a> 

            <a href="/download" class="btn gold-btn">
                📊 DOWNLOAD CSV
            </a>

            <a href="/attendance-history" class="btn gold-btn">
                📅 ATTENDANCE HISTORY
            </a>

        </div>

        <div class="grid">

            <div class="card">
                <div class="label">
                    TOTAL EMPLOYEES
                </div>

                <div class="number">
                    {total_employees}
                </div>

                <p class="label">
                    Registered employees
                </p>
            </div>

            <div class="card">
                <div class="label">
                    TODAY'S ATTENDANCE
                </div>

                <div class="number">
                    {today_attendance}
                </div>

                <p class="label">
                    Employees present
                </p>
            </div>

            <div class="card">
                <div class="label">
                    ATTENDANCE RATE
                </div>

                <div class="number gold">
                    {attendance_rate}%
                </div>

                <p class="label">
                    Today's attendance
                </p>
            </div>

            <div class="card">
                <div class="label">
                    ABSENT TODAY
                </div>

                <div class="number">
                    {absent_today}
                </div>

                <p class="label">
                    Employees absent
                </p>
            </div>

        </div>

        <h2 class="section-title">
            TODAY'S ATTENDANCE
        </h2>

        <div class="attendance-summary">

            {employee_status}

        </div>

        <h2 class="section-title">
            QUICK ACTIONS
        </h2>

        <div class="actions">

            <a href="/add" class="action">

                <div class="icon">➕</div>

                <div class="action-title">
                    ADD EMPLOYEE
                </div>

                <div class="action-text">
                    Create employee profile
                </div>

            </a>

            <a href="/employees" class="action">

                <div class="icon">👥</div>

                <div class="action-title">
                    EMPLOYEES
                </div>

                <div class="action-text">
                    View employee records
                </div>

            </a>

            <a href="/download" class="action">

                <div class="icon">📥</div>

                <div class="action-title">
                    ATTENDANCE REPORT
                </div>

                <div class="action-text">
                    Download CSV report
                </div>

            </a>

        </div>

    """)

# ============================================================
# EMPLOYEES
# ============================================================

@app.route("/employees")
def employees():

    if not session.get("admin_logged_in"):
        return redirect("/login")

    search = request.args.get("search", "").strip()

    db = get_db()

    if search:
        records = db.execute("""
            SELECT *
            FROM employees
            WHERE employee_id LIKE ?
               OR name LIKE ?
               OR role LIKE ?
               OR department LIKE ?
            ORDER BY name
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:
        records = db.execute("""
            SELECT *
            FROM employees
            ORDER BY name
        """).fetchall()

    db.close()

    employee_cards = ""

    for employee in records:

        photo_html = ""

        if employee["photo"]:

            photo_html = f"""
            <img
                src="/static/uploads/{employee['photo']}"
                style="
                    width:80px;
                    height:80px;
                    object-fit:cover;
                    border-radius:50%;
                    border:2px solid #d4af37;
                    margin-bottom:12px;
                "
            >
            """

        employee_cards += f"""
        <div class="employee-card">

            <div style="text-align:center;">

                {photo_html}

                <h2>{employee['name']}</h2>

                <p class="gold">
                    {employee['role']}
                </p>

                <span class="active-badge">
                    ● ACTIVE
                </span>

            </div>

            <p class="label">
                Employee ID:
                {employee['employee_id']}
            </p>

            <p>
                Department:
                {employee['department'] or 'Not specified'}
            </p>

            <a
                href="/employee/{employee['employee_id']}"
                class="btn gold-btn"
            >
                VIEW PROFILE
            </a>

        </div>
        """

    if not employee_cards:

        employee_cards = """
        <div class="card">

            <h2>No Employees Found</h2>

            <p class="label">
                Try another search.
            </p>

        </div>
        """

    return page(f"""

        <div class="welcome">

            <h1>
                <span class="gold">
                    EMPLOYEES
                </span>
            </h1>

            <p>
                MOTTEM STUDIOS Employee Directory
            </p>

            <a href="/" class="btn">
                ← BACK TO DASHBOARD
            </a>

        </div>

        <div class="card">

            <form method="GET" action="/employees">

                <input
                    type="text"
                    name="search"
                    value="{search}"
                    placeholder="Search by ID, name, role or department"
                >

                <br><br>

                <button
                    type="submit"
                    class="btn gold-btn"
                >
                    🔍 SEARCH
                </button>

                <a
                    href="/employees"
                    class="btn gold-btn"
                >
                    CLEAR
                </a>

            </form>

        </div>

        <div class="grid">

            {employee_cards}

        </div>

    """)
    # ============================================================
# EMPLOYEE PROFILE
# ============================================================

def get_employee(employee_id):

    db = get_db()

    employee = db.execute("""
        SELECT *
        FROM employees
        WHERE employee_id=?
    """, (employee_id,)).fetchone()

    db.close()

    return employee


@app.route("/employee/<employee_id>")
def employee_profile(employee_id):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    employee = get_employee(employee_id)

    if not employee:
        return "Employee not found", 404

    qr_url = f"/qr/{employee['employee_id']}"

    # ==============================
    # ATTENDANCE PERCENTAGE
    # ==============================

    attendance_percentage = 0

    db_temp = get_db()

    if employee["joining_date"]:

        start_date = employee["joining_date"]

    else:

        first_attendance = db_temp.execute("""
            SELECT MIN(work_date)
            FROM attendance
            WHERE employee_id=?
            AND action='IN'
        """, (
            employee["employee_id"],
        )).fetchone()[0]

        start_date = first_attendance

    if start_date:

        today_date = date.today()

        start_date_obj = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

        total_days = (
            today_date - start_date_obj
        ).days + 1

        present_days = db_temp.execute("""
            SELECT COUNT(DISTINCT work_date)
            FROM attendance
            WHERE employee_id=?
            AND action='IN'
            AND work_date BETWEEN ? AND ?
        """, (
            employee["employee_id"],
            start_date,
            today_date.isoformat()
        )).fetchone()[0]

        if total_days > 0:

            attendance_percentage = round(
                (present_days / total_days) * 100,
                1
            )

    db_temp.close()

    # ==============================
    # TODAY'S ATTENDANCE
    # ==============================

    today = date.today().isoformat()

    db = get_db()

    today_status = db.execute("""
        SELECT action
        FROM attendance
        WHERE employee_id=?
        AND work_date=?
        AND action='IN'
        ORDER BY id ASC
        LIMIT 1
    """, (
        employee["employee_id"],
        today
    )).fetchone()

    # ==============================
    # CHECK-IN / CHECK-OUT BUTTONS
    # ==============================

    if not today_status:

        attendance_status = "🔴 NOT MARKED"

        check_in_time = "Not checked in"

        check_out_time = "Not checked out"

        attendance_buttons = f"""
        <form
            action="/attendance/{employee['employee_id']}/IN"
            method="POST"
        >
            <button
                type="submit"
                class="btn gold-btn"
            >
                🟢 CHECK IN
            </button>
        </form>
        """

    else:

        attendance_status = "🟢 PRESENT"

        check_in_record = db.execute("""
            SELECT timestamp
            FROM attendance
            WHERE employee_id=?
            AND work_date=?
            AND action='IN'
            ORDER BY id ASC
            LIMIT 1
        """, (
            employee["employee_id"],
            today
        )).fetchone()

        check_in_time = check_in_record["timestamp"]

        check_out_record = db.execute("""
            SELECT timestamp
            FROM attendance
            WHERE employee_id=?
            AND work_date=?
            AND action='OUT'
            ORDER BY id DESC
            LIMIT 1
        """, (
            employee["employee_id"],
            today
        )).fetchone()

        if check_out_record:

            check_out_time = check_out_record["timestamp"]

            attendance_buttons = """
            <p class="present">
                ✅ TODAY'S ATTENDANCE COMPLETED
            </p>
            """

        else:

            check_out_time = "Not checked out"

            attendance_buttons = f"""
            <form
                action="/attendance/{employee['employee_id']}/OUT"
                method="POST"
            >
                <button
                    type="submit"
                    class="btn gold-btn"
                >
                    🔴 CHECK OUT
                </button>
            </form>
            """

    db.close()

    # ==============================
    # EMPLOYEE PHOTO
    # ==============================

    photo_html = ""

    if employee["photo"]:

        photo_html = f"""
        <img
            src="/static/uploads/{employee['photo']}"
            style="
                width:140px;
                height:140px;
                object-fit:cover;
                border-radius:50%;
                border:3px solid #d4af37;
            "
        >
        """

    # ==============================
    # EMPLOYEE PROFILE PAGE
    # ==============================

    return page(f"""

        <div class="card">

            <div style="text-align:center;">

                <h2>
    <span class="gold">EMPLOYEE QR CODE</span>
</h2>

<p style="color:#aaa; margin-top:-5px;">
    Scan to view employee profile
</p>

                <img
                    src="{qr_url}"
                    width="220"
                    height="220"
                    style="
                        background:white;
                        padding:12px;
                        border-radius:14px;
                        border:2px solid #d4af37;
                        box-shadow:0 0 15px rgba(212,175,55,0.25);
                    "
                >

                <p class="label">
                    Scan this QR code to open the employee profile
                </p>

                {photo_html}

                <h1>
                    {employee['name']}
                </h1>

                <p class="gold">
                    {employee['role']}
                </p>

                <p class="label">
                    Employee ID: {employee['employee_id']}
                </p>

                <div style="
    display:inline-block;
    margin:12px 0;
    padding:8px 16px;
    border-radius:20px;
    border:1px solid #d4af37;
    background:#111;
    color:#d4af37;
    font-weight:bold;
">
    ● ACTIVE EMPLOYEE
</div>

                <p>
                    <b>Today's Status:</b>
                    {attendance_status}
                </p>

                <p>
                    <b>Check-In Time:</b>
                    {check_in_time}
                </p>

                <p>
                    <b>Check-Out Time:</b>
                    {check_out_time}
                </p>

            </div>

            <hr>

            <p>
                <b>Employee ID:</b>
                {employee['employee_id']}
            </p>

            <p>
                <b>Department:</b>
                {employee['department'] or 'Not specified'}
            </p>

            <p>
                <b>Phone:</b>
                {employee['phone'] or 'Not specified'}
            </p>

            <p>
                <b>Email:</b>
                {employee['email'] or 'Not specified'}
            </p>

            <p>
                <b>Joining Date:</b>
                {employee['joining_date'] or 'Not specified'}
            </p>

            <p>
                <b>Attendance Target:</b>
                {employee['attendance_target']}%
            </p>

            <div style="
    margin-top:15px;
    padding:15px;
    background:#111;
    border:1px solid #d4af37;
    border-radius:12px;
    text-align:center;
">

    <p style="margin:0; color:#aaa;">
        CURRENT ATTENDANCE
    </p>

    <h2 class="gold" style="margin:8px 0 0;">
        {attendance_percentage}%
    </h2>

</div>

            <br>

            <div style="
                display:flex;
                justify-content:center;
                gap:15px;
                flex-wrap:wrap;
                margin-top:20px;
            ">

                {attendance_buttons}

            </div>

            <br>

            <a
                href="/edit/{employee['employee_id']}"
                class="btn gold-btn"
            >
                ✏️ EDIT EMPLOYEE
            </a>

            <br><br>

            <a
                href="/delete/{employee['employee_id']}"
                class="btn"
                onclick="return confirm('Are you sure you want to delete this employee?');"
            >
                🗑️ DELETE EMPLOYEE
            </a>

            <br><br>

            <a
                href="/employee-attendance/{employee['employee_id']}"
                class="btn gold-btn"
            >
                📅 VIEW ATTENDANCE HISTORY
            </a>

            <br><br>

            <a
                href="/employees"
                class="btn gold-btn"
            >
                ← BACK TO EMPLOYEES
            </a>

        </div>

    """)
@app.route("/mark-attendance/<employee_id>")
def mark_attendance_page(employee_id):

    employee = get_employee(employee_id)

    if not employee:
        return "Employee not found", 404

    today = date.today().isoformat()

    db = get_db()

    today_records = db.execute("""
        SELECT action, timestamp
        FROM attendance
        WHERE employee_id=?
        AND work_date=?
        ORDER BY id ASC
    """, (employee_id, today)).fetchall()

    today_status = today_records[-1] if today_records else None

    check_in_time = ""
    check_out_time = ""

    for record in today_records:

        if record["action"] == "IN":
            check_in_time = record["timestamp"]

        elif record["action"] == "OUT":
            check_out_time = record["timestamp"]

    db.close()


    if not today_status:

        attendance_button = f"""
        <form action="/employee-check/{employee_id}/{employee['qr_token']}/IN"
              method="POST">

            <button type="submit" class="btn">
                CHECK IN
            </button>

        </form>
        """

        status = "🔴 NOT MARKED"


    elif today_status["action"] == "IN":

        attendance_button = f"""
        <form action="/employee-check/{employee_id}/{employee['qr_token']}/OUT"
              method="POST">

            <button type="submit" class="btn">
                CHECK OUT
            </button>

        </form>
        """

        status = "🟢 CHECKED IN"


    else:

        attendance_button = """
        <p class="present">
            ✅ TODAY'S ATTENDANCE COMPLETED
        </p>
        """

        status = "🟢 COMPLETED"


    time_details = ""

    if check_in_time:

        time_details += f"""
        <p class="id">
            🟢 Check-in:
            <b>{check_in_time}</b>
        </p>
        """

    if check_out_time:

        time_details += f"""
        <p class="id">
            🔴 Check-out:
            <b>{check_out_time}</b>
        </p>
        """


    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>Employee Attendance</title>


        <style>

            body {{
                margin: 0;
                background: #0d0d0d;
                color: white;
                font-family: Arial, sans-serif;
            }}


            .header {{
                padding: 20px;
                background: #151515;
                border-bottom: 1px solid #333;
                text-align: center;
            }}


            .logo {{
                font-size: 26px;
                font-weight: bold;
                letter-spacing: 2px;
            }}


            .gold {{
                color: #d4af37;
            }}


            .subtitle {{
                color: #aaa;
                margin-top: 8px;
                font-size: 14px;
            }}


            .card {{
                max-width: 500px;
                margin: 50px auto;
                padding: 35px 25px;
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 18px;
                text-align: center;
                box-sizing: border-box;
            }}


            h1 {{
                color: #d4af37;
                font-size: 32px;
                margin-bottom: 30px;
            }}


            h2 {{
                font-size: 28px;
                margin: 10px 0;
            }}


            .id {{
                color: #aaa;
                font-size: 16px;
                margin: 10px 0;
            }}


            .id b {{
                color: white;
            }}


            .status {{
                margin: 30px 0;
                font-size: 20px;
            }}


            .btn {{
                background: #d4af37;
                color: #000;
                border: none;
                padding: 14px 30px;
                border-radius: 10px;
                font-size: 17px;
                font-weight: bold;
                cursor: pointer;
            }}


            .btn:active {{
                transform: scale(0.98);
            }}


            .present {{
                color: #4caf50;
                font-size: 18px;
                font-weight: bold;
            }}


            .time-box {{
                margin: 25px 0;
                padding: 15px;
                background: #111;
                border: 1px solid #333;
                border-radius: 12px;
            }}


            footer {{
                text-align: center;
                color: #666;
                margin-top: 80px;
                padding: 20px;
                font-size: 13px;
            }}


            @media (max-width: 600px) {{

                .card {{
                    margin: 35px 20px;
                    padding: 30px 20px;
                }}

                h1 {{
                    font-size: 28px;
                }}

                h2 {{
                    font-size: 25px;
                }}

            }}

        </style>

    </head>


    <body>


        <div class="header">

            <div class="logo">
                MOTTEM
                <span class="gold">STUDIOS</span>
            </div>

            <div class="subtitle">
                EMPLOYEE ATTENDANCE
            </div>

        </div>


        <div class="card">


            <h1>
                ATTENDANCE
            </h1>


            <h2>
                {employee['name']}
            </h2>


            <p class="id">
                Employee ID:
                {employee['employee_id']}
            </p>


            <p class="id">
                Date:
                {datetime.now().strftime("%d-%m-%Y")}
            </p>


            <div class="status">
                {status}
            </div>


            {attendance_button}


            <div class="time-box">

                {time_details}

            </div>


        </div>


        <footer>
            MOTTEM STUDIOS • Employee Attendance
        </footer>


    </body>

    </html>
    """
    
#     ============================================================
# QR CODE
# ============================================================
@app.route("/delete/<employee_id>")
def delete_employee(employee_id):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    db = get_db()

    employee = db.execute(
        "SELECT * FROM employees WHERE employee_id = ?",
        (employee_id,)
    ).fetchone()

    if not employee:
        db.close()
        return "Employee not found", 404

    # Delete attendance records first
    db.execute(
        "DELETE FROM attendance WHERE employee_id = ?",
        (employee_id,)
    )

    # Delete employee
    db.execute(
        "DELETE FROM employees WHERE employee_id = ?",
        (employee_id,)
    )

    db.commit()
    db.close()

    return redirect("/employees")


@app.route("/logout")
def logout():

    session.pop("admin_logged_in", None)

    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "Mottem@2026": 

            session["admin_logged_in"] = True

            return redirect("/")

        return page("""
            <div class="card">

                <h2>
    <span class="gold">LOGIN FAILED</span>
</h2>

<p>Invalid username or password.</p>

                <a
                    href="/login"
                    class="btn gold-btn"
                >
                    TRY AGAIN
                </a>

            </div>
        """)

    return page("""
        <div class="card" style="max-width:450px; margin:50px auto; text-align:center;">

    <div style="font-size:45px; margin-bottom:10px;">
        🔐
    </div>

    <h1>
        <span class="gold">
            ADMIN LOGIN
        </span>
    </h1>

    <p style="color:#aaa; margin-bottom:25px;">
        MOTTEM STUDIOS ATTENDANCE SYSTEM
    </p>

    <form method="POST">

                <p class="label">
                    Username
                </p>

                <input
                    type="text"
                    name="username"
                    required
                >

                <p class="label">
                    Password
                </p>

                <input
                    type="password"
                    name="password"
                    required
                >

                <br><br>

                <button
                    type="submit"
                    class="btn gold-btn"
                >
                    LOGIN
                </button>

            </form>

        </div>
    """)
@app.route("/edit/<employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    employee = get_employee(employee_id)

    if not employee:
        return "Employee not found", 404

    if request.method == "POST":

        name = request.form["name"]
        role = request.form["role"]
        department = request.form["department"]
        phone = request.form["phone"]
        email = request.form["email"]
        joining_date = request.form["joining_date"]
        attendance_target = request.form["attendance_target"]

        photo = request.files.get("photo")

        photo_filename = employee["photo"]

        if photo and photo.filename:

            filename = secure_filename(
                employee_id + "_" + secrets.token_hex(8) + "_" + photo.filename
            )

            photo.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    filename
                )
            )

            photo_filename = filename

        db = get_db()

        db.execute("""
            UPDATE employees
            SET name = ?,
                role = ?,
                department = ?,
                phone = ?,
                email = ?,
                joining_date = ?,
                attendance_target = ?,
                photo = ?
            WHERE employee_id = ?
        """, (
            name,
            role,
            department,
            phone,
            email,
            joining_date,
            attendance_target,
            photo_filename,
            employee_id
        ))

        db.commit()
        db.close()

        return redirect(
            f"/employee/{employee_id}"
        )

    return page(f"""

        <div class="card">

            <h1>
                <span class="gold">EDIT EMPLOYEE</span>
            </h1>

            <form
                method="POST"
                enctype="multipart/form-data"
            >

                <p class="label">
                    Employee Photo
                </p>

                <input
                    type="file"
                    name="photo"
                    accept="image/*"
                >

                <p class="label">
                    Name
                </p>

                <input
                    type="text"
                    name="name"
                    value="{employee['name']}"
                    required
                >

                <p class="label">
                    Role
                </p>

                <input
                    type="text"
                    name="role"
                    value="{employee['role']}"
                    required
                >

                <p class="label">
                    Department
                </p>

                <input
                    type="text"
                    name="department"
                    value="{employee['department'] or ''}"
                >

                <p class="label">
                    Phone
                </p>

                <input
                    type="text"
                    name="phone"
                    value="{employee['phone'] or ''}"
                >

                <p class="label">
                    Email
                </p>

                <input
                    type="email"
                    name="email"
                    value="{employee['email'] or ''}"
                >

                <p class="label">
                    Joining Date
                </p>

                <input
                    type="date"
                    name="joining_date"
                    value="{employee['joining_date'] or ''}"
                >

                <p class="label">
                    Attendance Target (%)
                </p>

                <input
                    type="number"
                    name="attendance_target"
                    value="{employee['attendance_target']}"
                    min="0"
                    max="100"
                >

                <br><br>

                <button
                    type="submit"
                    class="btn gold-btn"
                >
                    SAVE CHANGES
                </button>

            </form>

            <br>

            <a
                href="/employee/{employee_id}"
                class="btn gold-btn"
            >
                CANCEL
            </a>

        </div>

    """)
@app.route("/qr/<employee_id>")
def employee_qr(employee_id):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    employee = get_employee(employee_id)

    if not employee:
        return "Employee not found", 404

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(
    f"http://127.0.0.1:5000/mark-attendance/{employee_id}"
)

    qr.make(fit=True)

    img = qr.make_image()

    output = io.BytesIO()

    img.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return send_file(
        output,
        mimetype="image/png"
    )
    # ============================================================
# ATTENDANCE
# ============================================================
@app.route("/employee-attendance/<employee_id>")
def employee_attendance(employee_id):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    employee = get_employee(employee_id)

    if not employee:
        return "Employee not found", 404

    db = get_db()

    records = db.execute("""
        SELECT action, timestamp, work_date
        FROM attendance
        WHERE employee_id=?
        ORDER BY timestamp DESC
    """, (employee_id,)).fetchall()

    db.close()

    rows = ""

    for record in records:
        rows += f"""
        <tr>
            <td>{record['action']}</td>
            <td>{record['work_date']}</td>
            <td>{record['timestamp']}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="3">
                No attendance records found.
            </td>
        </tr>
        """

    return page(f"""
        <div class="welcome">

            <h1>
                <span class="gold">
                    ATTENDANCE HISTORY
                </span>
            </h1>

            <p>
                {employee['name']} —
                {employee['employee_id']}
            </p>

        </div>

        <div class="card">

            <table class="attendance-table">

                <tr>
                    <th>Action</th>
                    <th>Date</th>
                    <th>Time</th>
                </tr>

                {rows}

            </table>

            <br>

            <a
                href="/employee/{employee_id}"
                class="btn gold-btn"
            >
                ← BACK TO PROFILE
            </a>

        </div>
    """)
@app.route("/attendance-history")
def attendance_history():

    if not session.get("admin_logged_in"):
        return redirect("/login")

    selected_date = request.args.get(
        "date",
        date.today().isoformat()
    )

    selected_employee = request.args.get(
        "employee",
        ""
    )

    db = get_db()

    employees = db.execute("""
        SELECT employee_id, name
        FROM employees
        ORDER BY name
    """).fetchall()

    if selected_employee:

        records = db.execute("""
            SELECT
                attendance.employee_id,
                employees.name,
                employees.role,
                attendance.action,
                attendance.work_date,
                attendance.timestamp
            FROM attendance
            JOIN employees
            ON attendance.employee_id = employees.employee_id
            WHERE attendance.work_date = ?
            AND attendance.employee_id = ?
            ORDER BY attendance.timestamp DESC
        """, (
            selected_date,
            selected_employee
        )).fetchall()

    else:

        records = db.execute("""
            SELECT
                attendance.employee_id,
                employees.name,
                employees.role,
                attendance.action,
                attendance.work_date,
                attendance.timestamp
            FROM attendance
            JOIN employees
            ON attendance.employee_id = employees.employee_id
            WHERE attendance.work_date = ?
            ORDER BY attendance.timestamp DESC
        """, (selected_date,)).fetchall()

    db.close()

    attendance_rows = ""

    for record in records:

        attendance_rows += f"""
        <tr>
            <td>{record['employee_id']}</td>
            <td>{record['name']}</td>
            <td>{record['role']}</td>
            <td class="{record['action'].lower()}">{record['action']}</td>
            <td>{record['work_date']}</td>
            <td>{record['timestamp']}</td>
        </tr>
        """

    if not attendance_rows:

        attendance_rows = """
        <tr>
            <td colspan="6">
                No attendance records for this date.
            </td>
        </tr>
        """

    employee_options = ""

    for emp in employees:

        selected = ""

        if selected_employee == emp["employee_id"]:
            selected = "selected"

        employee_options += f"""
        <option value="{emp['employee_id']}" {selected}>
            {emp['name']} ({emp['employee_id']})
        </option>
        """

    return page(f"""

        <div class="welcome">

            <button
    onclick="window.print()"
    class="btn gold-btn"
    style="margin-top:15px;"
>
    🖨️ PRINT REPORT
</button>

            <p>
                View attendance by date and employee
            </p>

        </div>

        <div class="card">

            <form method="GET">

                <p class="label">
                    Select Date
                </p>

                <input
                    type="date"
                    name="date"
                    value="{selected_date}"
                    required
                >

                <br><br>

                <p class="label">
                    Select Employee
                </p>

                <select
                    name="employee"
                    style="
                        width:100%;
                        padding:13px;
                        background:#111;
                        color:white;
                        border:1px solid #444;
                        border-radius:8px;
                        font-size:15px;
                    "
                >

                    <option value="">
                        All Employees
                    </option>

                    {employee_options}

                </select>

                <br><br>

                <button
                    type="submit"
                    class="btn gold-btn"
                >
                    🔍 VIEW ATTENDANCE
                </button>

            </form>

        </div>

        <div class="card">

            <table class="attendance-table">

                <tr>
                    <th>Employee ID</th>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Action</th>
                    <th>Date</th>
                    <th>Timestamp</th>
                </tr>

                {attendance_rows}

            </table>

            <br>

            <a href="/" class="btn">
                ← BACK TO DASHBOARD
            </a>

        </div>

    """)
@app.route("/employee-check/<employee_id>/<token>/<action>", methods=["POST"])
def employee_check(employee_id, token, action):

    employee = get_employee(employee_id)

    if not employee:
        return "Employee not found", 404

    # Verify employee token
    if employee["qr_token"] != token:
        return "Invalid attendance link", 403

    if action not in ["IN", "OUT"]:
        return "Invalid action", 400

    today = date.today().isoformat()

    db = get_db()

    last = db.execute("""
        SELECT action
        FROM attendance
        WHERE employee_id=?
        AND work_date=?
        ORDER BY id DESC
        LIMIT 1
    """, (employee_id, today)).fetchone()

    if action == "OUT":
        if not last or last["action"] != "IN":
            db.close()
            return """
            <h2 style="text-align:center; margin-top:50px;">
                CHECK-IN REQUIRED
            </h2>
            """

    if last and last["action"] == action:
        db.close()
        return """
        <h2 style="text-align:center; margin-top:50px;">
            ATTENDANCE ALREADY RECORDED
        </h2>
        """

    timestamp = datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

    db.execute("""
        INSERT INTO attendance
        (employee_id, action, timestamp, work_date)
        VALUES (?, ?, ?, ?)
    """, (employee_id, action, timestamp, today))

    db.commit()
    db.close()

    return redirect(f"/mark-attendance/{employee_id}")
@app.route("/attendance/<employee_id>/<action>", methods=["POST"])
def mark_attendance(employee_id, action):

    if not session.get("admin_logged_in"):
        return redirect("/login")

    if action not in ["IN", "OUT"]:
        return "Invalid action", 400

    employee = get_employee(employee_id)

    if not employee:
        return "Employee not found", 404

    today = date.today().isoformat()

    db = get_db()

    last = db.execute("""
        SELECT action
        FROM attendance
        WHERE employee_id=?
        AND work_date=?
        ORDER BY id DESC
        LIMIT 1
    """, (
        employee_id,
        today
    )).fetchone()

    # OUT is allowed only after IN
    if action == "OUT":

        if not last or last["action"] != "IN":

            db.close()

            return page(f"""
                <div class="card">

                    <h2>⚠️ CHECK-IN REQUIRED</h2>

                    <p>
                        {employee['name']} must check in
                        before checking out.
                    </p>

                    <a
                        href="/employee/{employee_id}"
                        class="btn gold-btn"
                    >
                        ← BACK TO PROFILE
                    </a>

                </div>
            """)

    # Prevent duplicate consecutive actions
    if last and last["action"] == action:

        db.close()

        return page(f"""
            <div class="card">

                <h2>⚠️ ALREADY RECORDED</h2>

                <p>
                    {action} attendance has already
                    been recorded.
                </p>

                <a
                    href="/employee/{employee_id}"
                    class="btn gold-btn"
                >
                    ← BACK TO PROFILE
                </a>

            </div>
        """)

    timestamp = datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )

    db.execute("""
        INSERT INTO attendance
        (employee_id, action, timestamp, work_date)
        VALUES (?, ?, ?, ?)
    """, (
        employee_id,
        action,
        timestamp,
        today
    ))

    db.commit()
    db.close()

    return page(f"""
        <div class="card">

            <h2>
                {action} RECORDED ✓
            </h2>

            <p>
                <b>Employee:</b>
                {employee['name']}
            </p>

            <p>
                <b>Employee ID:</b>
                {employee_id}
            </p>

            <p>
                <b>Action:</b>
                {action}
            </p>

            <p>
                <b>Time:</b>
                {timestamp}
            </p>

            <br>

            <a
                href="/employee/{employee_id}"
                class="btn gold-btn"
            >
                ← BACK TO PROFILE
            </a>

        </div>
    """)
    # ============================================================
# ATTENDANCE REPORT
# ============================================================
@app.route("/attendance-report")
def attendance_report():

    if not session.get("admin_logged_in"):
        return redirect("/login")

    db = get_db()

    records = db.execute("""
        SELECT
            attendance.employee_id,
            employees.name,
            employees.department,
            attendance.action,
            attendance.timestamp,
            attendance.work_date
        FROM attendance
        JOIN employees
        ON attendance.employee_id = employees.employee_id
        ORDER BY attendance.timestamp DESC
    """).fetchall()

    db.close()

    rows = ""

    for record in records:
        rows += f"""
        <tr>
            <td>{record['employee_id']}</td>
            <td>{record['name']}</td>
            <td>{record['department'] or '-'}</td>
            <td>{record['action']}</td>
            <td>{record['timestamp']}</td>
            <td>{record['work_date']}</td>
        </tr>
        """

    if not rows:
        rows = """
        <tr>
            <td colspan="6">
                No attendance records found.
            </td>
        </tr>
        """

    return page(f"""
        <div class="welcome">
            <h1>
    <span class="gold">ATTENDANCE REPORT</span>
</h1>
<button
    onclick="window.print()"
    class="btn gold-btn"
    style="margin-top:15px;"
>
    🖨️ PRINT REPORT
</button>
            <p>Employee attendance records</p>
        </div>

        <div class="card">
            <table class="attendance-table">
                <tr>
                    <th>Employee ID</th>
                    <th>Name</th>
                    <th>Department</th>
                    <th>Action</th>
                    <th>Time</th>
                    <th>Date</th>
                </tr>

                {rows}

            </table>

            <br>

            <a href="/" class="btn">
                ← BACK TO DASHBOARD
            </a>
        </div>
    """)
@app.route("/download")
def download():
    if not session.get("admin_logged_in"):
        return redirect("/login")	

    db = get_db()

    records = db.execute("""
        SELECT
            attendance.work_date,
            attendance.timestamp,
            attendance.action,
            employees.employee_id,
            employees.name,
            employees.role
        FROM attendance
        JOIN employees
        ON employees.employee_id = attendance.employee_id
        ORDER BY attendance.id DESC
    """).fetchall()

    db.close()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Employee ID",
        "Name",
        "Role",
        "Action",
        "Date",
        "Timestamp"
    ])

    for record in records:

        writer.writerow([
            record["employee_id"],
            record["name"],
            record["role"],
            record["action"],
            record["work_date"],
            record["timestamp"]
        ])

    return send_file(
        io.BytesIO(
            output.getvalue().encode()
        ),
        mimetype="text/csv",
        as_attachment=True,
        download_name="MOTTEM_Attendance.csv"
    )
# ============================================================
# START SERVER
# ============================================================

init_db()

if __name__ == "__main__":

    print()

    print("=" * 50)

    print("       MOTTEM STUDIOS")

    print("       ATTENDANCE SYSTEM")

    print("=" * 50)

    print()

    print("Open in browser:")

    print("http://127.0.0.1:5000")

    print()

    app.run(
    host="0.0.0.0",
    port=5000,
    debug=False,
    use_reloader=False
)