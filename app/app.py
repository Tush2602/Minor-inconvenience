from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, user_name, user_status):
    """Save uploaded file with unique name and return file info"""
    if file and file.filename and allowed_file(file.filename):
        # Create unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        
        # Clean user name for filename
        clean_name = secure_filename(user_name.replace(' ', '_'))
        filename = f"{user_status}_{clean_name}_{timestamp}_{unique_id}.{file_extension}"
        
        # Save file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return {
            'original_name': file.filename,
            'saved_name': filename,
            'filepath': os.path.abspath(filepath),
            'file_size': os.path.getsize(filepath)
        }
    return None

def validate_password(password):
    """Validate password according to requirements"""
    errors = []
    
    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    # Additional validations can be added here
    if password and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if password and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if password and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")
    
    return errors

@app.route('/')
def home():
    """Render the homepage"""
    print("Rendering homepage")
    return render_template('homepage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If the user is submitting the form (POST request)
    if request.method == 'POST':
        # Get the common data
        name = request.form.get('name')
        college = request.form.get('college')
        status = request.form.get('status')
        password = request.form.get('password')
        
        # Debug: Print all form data
        print("DEBUG - All form data:")
        for key, value in request.form.items():
            print(f"  {key}: {value}")
        
        # Validate password
        password_errors = validate_password(password)
        
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('register.html')
        
        print("\n" + "="*50)
        print(f"NEW {status.upper()} REGISTRATION")
        print("="*50)
        print(f"Name: {name}")
        print(f"College: {college}")
        print(f"Status: {status}")
        print(f"Password: {'*' * len(password)} (length: {len(password)})")
        
        # Get specific fields based on status
        if status == 'student':
            student_id = request.form.get('student_id')
            email = request.form.get('student_email')
            department = request.form.get('student_department')
            grad_year = request.form.get('student_grad_year')
            degree = request.form.get('student_degree')
            
            print(f"Student ID: {student_id}")
            print(f"Email: {email}")
            print(f"Department: {department}")
            print(f"Graduation Year: {grad_year}")
            print(f"Degree: {degree}")
            
        elif status == 'college':
            email = request.form.get('college_email')
            admin_code = request.form.get('admin_code')
            admin_department = request.form.get('admin_department')
            
            print(f"Official Email: {email}")
            print(f"Admin Code: {admin_code}")
            print(f"Department/Section: {admin_department}")
            
        elif status == 'alumni':
            email = request.form.get('alumni_email')
            department = request.form.get('alumni_department') 
            grad_year = request.form.get('alumni_grad_year')
            degree = request.form.get('alumni_degree')
            id_card_file = request.files.get('id_card')
            
            print(f"Email: {email}")
            print(f"Department: {department}")
            print(f"Graduation Year: {grad_year}")
            print(f"Degree: {degree}")
            
            # Handle file upload
            if id_card_file and id_card_file.filename:
                file_info = save_uploaded_file(id_card_file, name, 'alumni')
                if file_info:
                    print(f"ID Card File: {file_info['original_name']}")
                    print(f"File Size: {file_info['file_size']} bytes")
                    print(f"File Location: {file_info['filepath']}")
                else:
                    print("ID Card File: Invalid file format")
            else:
                print("ID Card File: No file uploaded")
        
        print("="*50)
        print("REGISTRATION SUCCESSFUL!")
        print("="*50 + "\n")
        
        # Flash success message
        flash(f'Registration successful! Welcome {name}!', 'success')
        
        # After processing, redirect to the homepage
        return redirect(url_for('home'))

    # If the user is just visiting the page (GET request), show them the form
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)