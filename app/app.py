from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import sys
import random
from dotenv import load_dotenv

# Make sure to adjust this path if your project structure is different
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.file_utils import save_uploaded_file, allowed_file
from src.utils.auth_utils import hash_password, verify_password, validate_password
from src.utils.database import get_connection, create_database, create_tables, show_tables, clear_all_tables
from src.utils.database import insert_student, insert_alumni, insert_admin, drop_all_tables
from src.utils.database import is_unique_email, is_unique_student_id, is_unique_admin_code
from src.utils.database import get_all_admins, get_all_students, get_all_alumni
from src.utils.database import login_credential_exists, verify_student_credentials
from flask import jsonify

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/')
def home():
    return render_template('homepage.html')

from flask import session

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash("You have been logged out successfully!", "success")
    return redirect(url_for('home'))  # redirect to public homepage


@app.route("/init-db")
def init_db():
    create_database()
    create_tables()
    tables = show_tables()
    return f"✅ Alumni Nexus DB and tables created!, {tables}"

@app.route("/del-tables")
def del_tables():
    # drop_all_tables()
    clear_all_tables()
    tables = show_tables()
    return "All tables Clear \n Current tables in AlumniNexus database: \n" + str(tables)


@app.route("/get-tables")
def get_tables():
    admins = get_all_admins()
    students = get_all_students()
    alumni = get_all_alumni()
    return jsonify({
        "Admins": admins,
        "Students": students,
        "Alumni": alumni
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        college = request.form.get('college')
        status = request.form.get('status')
        password = request.form.get('password')

        password_errors = validate_password(password)
        password = hash_password(password)

        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('register.html')

        # ---- Fetch role-specific fields ----
        if status == 'student':
            student_id_form = request.form.get('student_id')
            email = request.form.get('student_email')
            department = request.form.get('student_department')
            grad_year = int(request.form.get('student_grad_year'))
            degree = request.form.get('student_degree')

            # --- UNIQUE CHECKS ---
            if not is_unique_student_id(student_id_form):
                flash(f"Student ID {student_id_form} already exists!", "error")
                return render_template('register.html')
            if not is_unique_email(email, 'student'):
                flash(f"Email {email} is already registered!", "error")
                return render_template('register.html')

            # --- Insert into DB ---
            sid = insert_student(name, college, email, student_id_form, department, grad_year, degree, password)

        elif status == 'college':
            email = request.form.get('college_email')
            admin_code = request.form.get('admin_code')
            admin_department = request.form.get('admin_department')

            # --- UNIQUE CHECKS ---
            if not is_unique_admin_code(admin_code):
                flash(f"Admin code {admin_code} already exists!", "error")
                return render_template('register.html')
            if not is_unique_email(email, 'college'):
                flash(f"Email {email} is already registered!", "error")
                return render_template('register.html')

            # --- Insert into DB ---
            admin_id = insert_admin(name, college, email, admin_code, admin_department, password)

        elif status == 'alumni':
            email = request.form.get('alumni_email')
            department = request.form.get('alumni_department') 
            grad_year = int(request.form.get('alumni_grad_year'))
            degree = request.form.get('alumni_degree')
            id_card_file = request.files.get('id_card')

            # --- UNIQUE CHECKS ---
            if not is_unique_email(email, 'alumni'):
                flash(f"Email {email} is already registered!", "error")
                return render_template('register.html')

            # --- File Upload ---
            file_info = None
            if id_card_file and id_card_file.filename:
                file_info = save_uploaded_file(id_card_file, name, 'alumni')

            alumni_id = insert_alumni(
                name, college, email, department, grad_year, degree,
                file_info['filepath'] if file_info else None, password
            )

        flash(f'Registration successful! Welcome {name}!, Please log in to continue.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login-student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not login_credential_exists(email, status='student'):
            flash("Email not registered. Please register first!", "error")
            return redirect(url_for('login_student'))

        if not verify_student_credentials(email, password, status='student'):
            flash("Incorrect password. Try again!", "error")
            return redirect(url_for('login_student'))

        # Fetch student data from DB
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Students WHERE email=%s", (email,))
        student = cursor.fetchone()
        conn.close()

        if not student:
            flash("Student not found!", "error")
            return redirect(url_for('login_student'))

        # Store complete student info in session
        session['logged_in'] = True
        session['user_type'] = 'student'
        session['student_id'] = student['id']
        session['student_email'] = student['email']
        session['student_name'] = student['name']
        
        # flash(f"Welcome, {email}!", "success")
        return redirect(url_for('student_dashboard'))

    return render_template('loginstudent.html')


@app.route('/student-dashboard')
def student_dashboard():
    # Simple session check
    if not session.get('logged_in') or session.get('user_type') != 'student':
        flash("Please log in first!", "error")
        return redirect(url_for('login_student'))
    
    student_id = session.get('student_id')
    return render_template('studentpage.html', student_id=student_id)


@app.route('/student-card')
def student_card():
    # Simple session check
    if not session.get('logged_in') or session.get('user_type') != 'student':
        flash("Please log in first!", "error")
        return redirect(url_for('login_student'))
    
    student_id = session.get('student_id')
    
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students WHERE id=%s", (student_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        flash("Student not found!", "error")
        return redirect(url_for('login_student'))


    year = student['graduation_year'] - 4 if student['degree'] == 'BTech' else student['graduation_year'] - 2
    since_year = student['graduation_year']
    name = student['name']
    college = student['college']
    email = student['email']
    student_id_from_db = student['id']
    college_department = student['department']
    degree = student['degree']
    first_five_numb = 90000 + random.randint(0, 9999)
    last_five_numb = random.randint(10000, 99999)

    return render_template('studentcard.html', year=year, name=name, college=college, 
                         email=email, student_id=student_id_from_db, college_department=college_department, 
                         degree=degree, since_year=since_year, first_five_numb=first_five_numb, 
                         last_five_numb=last_five_numb)

import random  # Add this import at the top of your file

@app.route("/fintech-stud")
def fintech_stud():
    return render_template("fintech2 stud.html")

@app.route('/login-alumni', methods=['GET', 'POST'])
def login_alumni():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not login_credential_exists(email, status='alumni'):
            flash("Email not registered. Please register first!", "error")
            return redirect(url_for('login_alumni'))

        if not verify_student_credentials(email, password, status='alumni'):
            flash("Incorrect password. Try again!", "error")
            return redirect(url_for('login_alumni'))

        # Fetch alumni data from DB
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Alumni WHERE email=%s", (email,))
        alumni = cursor.fetchone()
        conn.close()

        if not alumni:
            flash("Alumni not found!", "error")
            return redirect(url_for('login_alumni'))

        # Store complete alumni info in session
        session['logged_in'] = True
        session['user_type'] = 'alumni'
        session['alumni_id'] = alumni['id']
        session['alumni_email'] = alumni['email']
        session['alumni_name'] = alumni['name']

        # flash(f"Welcome, {email}!", "success")
        return redirect(url_for('alumni_dashboard'))

    return render_template('loginalumni.html')


@app.route('/alumni-dashboard')
def alumni_dashboard():
    # Simple session check
    if not session.get('logged_in') or session.get('user_type') != 'alumni':
        flash("Please log in first!", "error")
        return redirect(url_for('login_alumni'))
    
    alumni_id = session.get('alumni_id')
    return render_template('alumnipage.html', alumni_id=alumni_id)


@app.route('/alumni-card')
def alumni_card():
    # Simple session check
    if not session.get('logged_in') or session.get('user_type') != 'alumni':
        flash("Please log in first!", "error")
        return redirect(url_for('login_alumni'))
    
    alumni_id = session.get('alumni_id')
    
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    # FIXED: Query Alumni table instead of Students table
    cursor.execute("SELECT * FROM Alumni WHERE id=%s", (alumni_id,))
    alumni = cursor.fetchone()
    conn.close()

    if not alumni:
        flash("Alumni not found!", "error")
        return redirect(url_for('login_alumni'))


    job_roles = job_roles = [
                    "Software Engineer","Frontend Developer","Backend Developer","Full Stack Developer","Mobile App Developer","DevOps Engineer",
                        "Site Reliability Engineer (SRE)","Embedded Systems Engineer","Game Developer","Software Architect","QA Engineer",
                            "Data Scientist","Data Analyst","Machine Learning Engineer","AI Specialist","Data Engineer","Business Intelligence Analyst","Product Manager",
                               "UI/UX Designer","Product Designer","UX Researcher","Graphic Designer","Cloud Engineer","Systems Administrator","Network Engineer",
                                    "Cybersecurity Analyst","IT Support Specialist","Database Administrator","Engineering Manager","Technical Lead","Project Manager",
                                        "Scrum Master","Chief Technology Officer (CTO)","Solutions Architect","Technical Writer","Business Analyst",
    ]
    
    
    tech_companies = [
                "Google", "Apple", "Meta", "Amazon", "Microsoft", "Netflix", "Salesforce", "Adobe", "Oracle", 
                  "IBM", "SAP", "Atlassian", "Snowflake", "ServiceNow", "VMware", "Databricks", "NVIDIA", "Intel",
                    "AMD", "Qualcomm", "Cisco Systems", "Dell Technologies", "Stripe", "PayPal", "Block (Square)",
                      "Goldman Sachs", "JPMorgan Chase & Co.", "Tesla", "SpaceX", "Ford", "General Motors", 
                        "Electronic Arts (EA)", "Activision Blizzard", "Epic Games", "Unity Technologies", "Spotify", 
                          "Disney", "Uber", "Airbnb", "LinkedIn", "X (formerly Twitter)", "Slack", "Zoom", "Dropbox"
                      ]
    
    cities = ["Gurugram, India", "Mumbai, India", "Delhi, India", "Bangalore, India", "Chennai, India", "Kolkata, India",
               "Hyderabad, India", "Pune, India", "Ahmedabad, India", "Jaipur, India", "Lucknow, India", "New York, USA",
                 "London, UK", "Tokyo, Japan", "Paris, France", "Singapore, Singapore", "Dubai, UAE", "Sydney, Australia",
                   "Toronto, Canada", "San Francisco, USA", "Berlin, Germany", "Hong Kong, Hong Kong", "Amsterdam, Netherlands",
                     "Seoul, South Korea", "Los Angeles, USA", "Chicago, USA", "Beijing, China", "Moscow, Russia", "Rome, Italy",
                       "Madrid, Spain", "Sao Paulo, Brazil"]


    # Extract alumni data using correct column names
    year = alumni['graduation_year'] - 4 if alumni['degree'] == 'Bachelors' else alumni['graduation_year'] - 2
    since_year = alumni['graduation_year']
    name = alumni['name']
    college = alumni['college']
    email = alumni['email']
    alumni_id_from_db = alumni['id']
    college_department = alumni['department']
    degree = alumni['degree']
    role = random.choice(job_roles)
    company = random.choice(tech_companies)
    # Generate random numbers for card
    first_five_numb = 90000 + random.randint(1000, 9999)
    last_five_numb = random.randint(10000, 99999)

    return render_template('alumnicard.html', 
                         year=year, 
                         name=name, 
                         college=college,
                         email=email, 
                         alumni_id=alumni_id_from_db, 
                         college_department=college_department, 
                         degree=degree, 
                         since_year=since_year, 
                         first_five_numb=first_five_numb, 
                         last_five_numb=last_five_numb,
                         role= role,
                         company = company,
                         random_numb = random.randint(1000, 9999),
                         city = random.choice(cities)                         
    )


@app.route('/login-college', methods=['GET', 'POST'])
def login_college():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not login_credential_exists(email, status='college'):
            flash("Email not registered. Please register first!", "error")
            return redirect(url_for('login_college'))

        if not verify_student_credentials(email, password, status='college'):
            flash("Incorrect password. Try again!", "error")
            return redirect(url_for('login_college'))

        # Fetch admin data from DB (corrected table name)
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Admins WHERE email=%s", (email,))
        admin = cursor.fetchone()
        conn.close()

        if not admin:
            flash("Admin not found!", "error")
            return redirect(url_for('login_college'))

        # Store complete admin info in session
        session['logged_in'] = True
        session['user_type'] = 'admin'
        session['admin_id'] = admin['id']
        session['admin_email'] = admin['email']
        session['admin_name'] = admin['name']
        
        # flash(f"Welcome, {email}!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template("logincollege.html")


@app.route('/admin-dashboard')
def admin_dashboard():
    # Simple session check
    if not session.get('logged_in') or session.get('user_type') != 'admin':
        flash("Please log in first!", "error")
        return redirect(url_for('login_college'))
    
    admin_id = session.get('admin_id')
    return render_template('index.html', admin_id=admin_id)

@app.route("/fintech")
def fintech():
    return render_template("fintech2.html")

@app.route('/alumni-database')
def alumni_database():
    # Simple session check for admin
    if not session.get('logged_in') or session.get('user_type') != 'admin':
        flash("Please log in as admin first!", "error")
        return redirect(url_for('login_college'))
    
    return render_template('alumni_database.html')

@app.route('/student-database')
def student_database():
    # Simple session check for admin
    if not session.get('logged_in') or session.get('user_type') != 'admin':
        flash("Please log in as admin first!", "error")
        return redirect(url_for('login_college'))
    
    return render_template('student_database.html')

# ---------------- DISABLE BACK AFTER LOGOUT ----------------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

if __name__ == '__main__':
    create_database()
    create_tables()
    app.run(debug=True)
