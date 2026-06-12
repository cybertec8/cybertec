import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from flask import (
    Flask, render_template, redirect,
    request, url_for, abort, session, flash
)
from authlib.integrations.flask_client import OAuth

from flask_login import (
    LoginManager, login_user,
    login_required, logout_user,
    current_user
)

from functools import wraps

from extensions import db
from models import (
    User, Team, TeamMember,
    TeamRequest, Event, EventRegistration, CTFTask,
    TaskSolve, TaskLike, TaskSubmission, Activity, Blog
)
import ctf_battle_models  # Ensure models are registered

# ---------------- FLASK APP ----------------
# ---------------- BASIC SETUP ----------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env FIRST so os.getenv() picks up all variables
load_dotenv()

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# Use DATABASE_URL for production (e.g. Render/Heroku Postgres),
# fall back to local SQLite for development.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cybertec8_secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'ctf.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -------- IMAGE UPLOAD FOLDER --------
UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads/blogs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from flask_migrate import Migrate

db.init_app(app)
migrate = Migrate(app, db)

from routes import admin_bp, ctf_admin_bp, participant_bp, ctf_battle_bp, battle_bp
app.register_blueprint(admin_bp)
app.register_blueprint(ctf_admin_bp)
app.register_blueprint(participant_bp)
app.register_blueprint(ctf_battle_bp)
app.register_blueprint(battle_bp)

# ---------------- OAUTH SETUP ----------------
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# ---------------- AUTH CONFIG ----------------

# Set to True to enable Google-only authentication
GOOGLE_AUTH_ONLY = True

# ---------------- MAINTENANCE MODE ----------------

# Set to False to disable authentication (maintenance mode)
AUTH_ENABLED = True
app.config['AUTH_ENABLED'] = AUTH_ENABLED
app.config['DEV_MODE'] = False

# DEV_MODE = True : auto-logs in a normal dev user (is_admin=False).
#   - Navbar shows Dashboard + Logout (fully authenticated look).
#   - /dashboard works normally; /admin/dashboard still requires real admin (if BYPASS_ADMIN=False).
# DEV_MODE = False : full production auth — Google login required.
app.config['DEV_MODE'] = True
app.config['DEV_USER_EMAIL'] = "dev@cybertec8.local"
app.config['DEV_USER_IS_ADMIN'] = False        # Set True to test admin UI
app.config['DEV_BYPASS_ADMIN'] = True         # Set True to bypass ALL role checks

# ---------------- BLOG UPLOAD CONFIG ----------------

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads/blogs')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- EMAIL CONFIG ----------------

EMAIL_ADDRESS = "cybertecc4@gmail.com"
EMAIL_PASSWORD = "ilcn bzds xdwk omsm"

# ---------------- LOGIN MANAGER ----------------

login_manager = LoginManager(app)
login_manager.login_view = "login"

@app.before_request
def require_login():
    """Route protection: redirects unauthenticated requests to login in production."""

    # ── DEV MODE ────────────────────────────────────────────────────────────────
    # Auto-login a local dev user so the navbar and role logic work correctly.
    # We SKIP this if:
    # 1. The user is already authenticated (preserves real admin sessions).
    # 2. The user is visiting an auth route (allows manual login/logout).
    # 3. request.endpoint is None (handles static files/special cases).
    # 4. The requested route is an ADMIN route but the dev user isn't admin.
    
    auth_routes = ['login', 'logout', 'google_login', 'google_callback']
    is_auth_route = request.endpoint in auth_routes if request.endpoint else False
    
    admin_prefixes = ['admin.', 'ctf_admin.']
    is_admin_route = any(request.endpoint.startswith(p) for p in admin_prefixes if request.endpoint)

    if app.config['DEV_MODE'] and not is_auth_route:
        # Auto-login the dev user if not already authenticated
        if not current_user.is_authenticated:
            dev_user = User.query.filter_by(email=app.config['DEV_USER_EMAIL']).first()
            if not dev_user:
                dev_user = User(
                    username="Dev User",
                    email=app.config['DEV_USER_EMAIL'],
                    is_admin=app.config['DEV_USER_IS_ADMIN']
                )
                db.session.add(dev_user)
                db.session.commit()
            elif dev_user.is_admin != app.config['DEV_USER_IS_ADMIN']:
                dev_user.is_admin = app.config['DEV_USER_IS_ADMIN']
                db.session.commit()
            login_user(dev_user)
        return  # skip all login enforcement in DEV_MODE
    # ── END DEV MODE ────────────────────────────────────────────────────────────

    if not GOOGLE_AUTH_ONLY:
        return  # Skip if Google-only auth is disabled (maintenance mode)

    # Allowed routes without login
    allowed_routes = ['home', 'about', 'features', 'blog', 'login', 'google_login', 'google_callback', 'static', 'resources']

    if not current_user.is_authenticated and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from utils import generate_invite_code

def send_otp_email(to_email, otp):
    if not AUTH_ENABLED:
        print(f"------------\n[DEV MODE] OTP for {to_email}: {otp}\n------------")
        return

    msg = MIMEText(f"Your Cybertec8 login OTP is: {otp}")
    msg["Subject"] = "Cybertec8 Login OTP"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

from decorators import (
    admin_required, 
    maintenance_mode_redirect, 
    optional_login_required
)

# ---------------- AUTH ----------------

@app.route("/")
def home():
    return render_template("home.html", auth_enabled=AUTH_ENABLED)



@app.route("/blog")
def blog():
    blogs = Blog.query.filter_by(is_published=True).order_by(Blog.published_at.desc()).all()
    return render_template("blog.html", blogs=blogs)

@app.route("/resources")
def resources():
    return render_template("resources.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/features")
def features():
    return render_template("features.html")


# ---------------- AUTH ROUTES ----------------

@app.route("/login")
def login():
    # In DEV_MODE, we allow authenticated users to visit the login page.
    # This prevents being trapped as a 'Dev User' when you want to log in as real admin.
    if current_user.is_authenticated and not app.config.get('DEV_MODE', False):
        return redirect(url_for("home"))
    return render_template("auth/login.html")



@app.route("/auth/google")
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        flash("Google authentication failed.", "danger")
        return redirect(url_for('login'))

    google_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name') or email.split('@')[0]

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        # Check by email if google_id is not set yet
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
        else:
            # Create new user
            user = User(
                username=name,
                email=email,
                google_id=google_id
            )
            db.session.add(user)
        db.session.commit()

    login_user(user)

    #if not user.profile_completed:
       #return redirect(url_for('participant.profile'))

    return redirect(url_for('home'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("login"))

# ---------------- OLD AUTH (REMOVED) ----------------
# Registration and password-based login have been removed.


# -------- DEV_MODE ADMIN PROMOTION ROUTE --------
# This route is only active when debug=True.
# Use it to promote your account if you are locked out locally.
@app.route("/make-admin-now")
@login_required
def make_admin_now():
    if not app.debug:
        abort(403)
    current_user.is_admin = True
    db.session.commit()
    return f"Success: {current_user.email} is now an admin. Logout and login again."



# ---------------- RUN LOCAL ----------------
if __name__ == "__main__":
    app.run(debug=True)
