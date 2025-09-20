import uuid
import pymysql
from dotenv import load_dotenv
import os
import sys

from src.utils.auth_utils import verify_password

load_dotenv()

# Connection to Aiven MySQL
def get_connection(db_name=None):
    return pymysql.connect(
        charset="utf8mb4",
        connect_timeout=10,
        cursorclass=pymysql.cursors.DictCursor,
        db=db_name if db_name else os.getenv("DB_NAME"),  # connect to given db or default
        host=os.getenv("DB_HOST"),
        password=os.getenv("DB_PASSWORD"),
        read_timeout=10,
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        write_timeout=10,
    )

# Create the main database (AlumniNexus)
def create_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS AlumniNexus")
    conn.commit()
    conn.close()

# Create all tables inside AlumniNexus
def create_tables():
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Students (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(100),
        college VARCHAR(150),
        email VARCHAR(150) UNIQUE,
        department VARCHAR(100),
        graduation_year INT,
        degree VARCHAR(100),
        password_hash VARCHAR(200),
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Alumni (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(100),
        college VARCHAR(150),
        email VARCHAR(150) UNIQUE,
        department VARCHAR(100),
        graduation_year INT,
        degree VARCHAR(100),
        profile_image VARCHAR(200),
        password_hash VARCHAR(200),
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Admins (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(100),
        college VARCHAR(150),
        email VARCHAR(150) UNIQUE,
        department_section VARCHAR(100),
        password_hash VARCHAR(200),
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def show_tables():
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    conn.close()
    return tables

# ---------- Student ----------
def insert_student(name, college, email, sid,  department, graduation_year, degree, password_hash):
    student_id = sid
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Students (id, name, college, email, department, graduation_year, degree, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (student_id, name, college, email, department, graduation_year, degree, password_hash))
    conn.commit()
    conn.close()
    return student_id

# ---------- Alumni ----------
def insert_alumni(name, college, email, department, graduation_year, degree, profile_image, password_hash):
    alumni_id = str(uuid.uuid4())
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Alumni (id, name, college, email, department, graduation_year, degree, profile_image, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (alumni_id, name, college, email, department, graduation_year, degree, profile_image, password_hash))
    conn.commit()
    conn.close()
    return alumni_id

# ---------- Admin ----------
def insert_admin(name, college, email, admin_code, department_section, password_hash):
    admin_id = admin_code
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Admins (id, name, college, email, department_section, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (admin_id, name, college, email, department_section, password_hash))
    conn.commit()
    conn.close()
    return admin_id


def clear_all_tables():
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM Students")
        cursor.execute("DELETE FROM Alumni")
        cursor.execute("DELETE FROM Admins")
        conn.commit()
        print("✅ All tables cleared successfully!")
    except Exception as e:
        print("❌ Error clearing tables:", e)
    finally:
        conn.close()


def drop_all_tables():
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS Students")
        cursor.execute("DROP TABLE IF EXISTS Alumni")
        cursor.execute("DROP TABLE IF EXISTS Admins")
        conn.commit()
        print("✅ All tables dropped successfully!")
    except Exception as e:
        print("❌ Error dropping tables:", e)
    finally:
        conn.close()




# ---------- Check uniqueness ----------
def is_unique_student_id(student_id):
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM Students WHERE id=%s", (student_id,))
    count = cursor.fetchone()['count']
    conn.close()
    return count == 0

def is_unique_admin_code(admin_code):
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM Admins WHERE id=%s", (admin_code,))
    count = cursor.fetchone()['count']
    conn.close()
    return count == 0

def is_unique_email(email, status):
    """
    status: 'student', 'alumni', 'college'
    """
    table_map = {
        'student': 'Students',
        'alumni': 'Alumni',
        'college': 'Admins'
    }
    table = table_map.get(status)
    if not table:
        return False

    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE email=%s", (email,))
    count = cursor.fetchone()['count']
    conn.close()
    return count == 0


# ---------- Show all Students ----------
def get_all_students():
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ---------- Show all Alumni ----------
def get_all_alumni():
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Alumni")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ---------- Show all Admins ----------
def get_all_admins():
    conn = get_connection("AlumniNexus")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Admins")
    rows = cursor.fetchall()
    conn.close()
    return rows


def login_credential_exists(email, status):

    if status == 'student':
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Students WHERE email=%s", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    elif status == 'alumni':
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Alumni WHERE email=%s", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    elif status == 'college':
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM Admins WHERE email=%s", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

def verify_student_credentials(email, password, status):

    if status == 'student':
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM Students WHERE email=%s", (email,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return verify_password(password, result['password_hash'])
        return False
    elif status == 'alumni':
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM Alumni WHERE email=%s", (email,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return verify_password(password, result['password_hash'])
        return False
    elif status == 'college':
        conn = get_connection("AlumniNexus")
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM Admins WHERE email=%s", (email,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return verify_password(password, result['password_hash'])
        return False
