from functools import wraps
from flask import redirect, url_for, abort, request, session, current_app
from flask_login import current_user, login_required

def admin_required(f):
    """Decorator to require admin privileges (is_admin=True)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('DEV_MODE') and current_app.config.get('DEV_BYPASS_ADMIN'):
            return f(*args, **kwargs)

        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        
        if not current_user.is_admin:
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function

def ctf_admin_required(f):
    """Decorator for CTF admins (currently mapping to is_admin=True)"""
    return admin_required(f)

def maintenance_mode_redirect(f):
    """Decorator to redirect auth routes when AUTH_ENABLED is False"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('DEV_MODE'):
             return f(*args, **kwargs)
        if not current_app.config.get('AUTH_ENABLED', True):
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def optional_login_required(f):
    """Decorator that only requires login when AUTH_ENABLED is True"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('DEV_MODE'):
            return f(*args, **kwargs)
        if current_app.config.get('AUTH_ENABLED', True):
            return login_required(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function
