from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Hash a plain-text password using Werkzeug."""
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain-text password against its hash."""
    return check_password_hash(hashed, password)

def validate_password(password: str):
    """Validate password according to requirements"""
    errors = []

    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if password and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if password and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if password and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")

    return errors
