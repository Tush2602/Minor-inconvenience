import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app as app


# Configuration for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, user_name, user_status):
    """Save uploaded file with unique name and return file info"""
    if file and file.filename and allowed_file(file.filename):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        clean_name = secure_filename(user_name.replace(' ', '_'))
        filename = f"{user_status}_{clean_name}_{timestamp}_{unique_id}.{file_extension}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return {
            'original_name': file.filename,
            'saved_name': filename,
            'filepath': os.path.abspath(filepath),
            'file_size': os.path.getsize(filepath)
        }
    return None
