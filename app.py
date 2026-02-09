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

from models import (
    db, User, Team, TeamMember,
    TeamRequest, Event, EventRegistration, CTFTask,
    TaskSolve, TaskLike, TaskSubmission, Activity, Blog
)


# ---------------- BASIC SETUP ----------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cybertec8_secret")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'ctf.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

load_dotenv()

db.init_app(app)

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
AUTH_ENABLED = False

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
    """Strict route protection: Redirect all unauthenticated requests to login"""
    if not GOOGLE_AUTH_ONLY:
        return # Skip if Google-only auth is disabled (dev/maintenance)

    # Allowed routes without login
    allowed_routes = ['login', 'google_login', 'google_callback', 'static', 'resources']
    
    if not current_user.is_authenticated and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------------- UTILS ----------------

def generate_invite_code():
    return "CTF-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )

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

def maintenance_mode_redirect(f):
    """Decorator to redirect auth routes when AUTH_ENABLED is False"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AUTH_ENABLED:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def optional_login_required(f):
    """Decorator that only requires login when AUTH_ENABLED is True"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if AUTH_ENABLED:
            return login_required(f)(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# ---------------- AUTH ----------------

@app.route("/")
def home():
    return "Server Running 🚀"


@app.route("/blog")
def blog():
    blogs = Blog.query.filter_by(is_published=True).order_by(Blog.published_at.desc()).all()
    return render_template("blog.html", blogs=blogs)

@app.route("/resources")
def resources():
    return render_template("resources.html")


# ---------------- AUTH ROUTES ----------------

@app.route("/login")
def login():
    if current_user.is_authenticated:
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
    return redirect(url_for('home'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("login"))

# ---------------- OLD AUTH (REMOVED) ----------------
# Registration and password-based login have been removed.


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("console/dashboard.html")

# ---------------- SCOREBOARD ----------------

@app.route("/scoreboard")
@login_required
def scoreboard():
    return render_template("console/scoreboard.html")

# ---------------- PROFILE ----------------

@app.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html")

@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.email = request.form.get("email")
        current_user.mobile = request.form.get("mobile")
        current_user.bio = request.form.get("bio")
        db.session.commit()
        return redirect(url_for("profile"))

    return render_template("auth/edit_profile.html")

# ---------------- EVENTS (DASHBOARD) ----------------

@app.route("/dashboard/events")
@login_required
def dashboard_events():
    # Fetch all events
    events = Event.query.all()
    
    # Check registration status for user
    registered_event_ids = []
    regs = EventRegistration.query.filter_by(user_id=current_user.id).all()
    registered_event_ids = [r.event_id for r in regs]
        
    return render_template("console/events.html", events=events, registered_event_ids=registered_event_ids)

@app.route("/register-event/<int:event_id>", methods=["POST"])
@login_required
def register_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if already registered
    existing = EventRegistration.query.filter_by(
        user_id=current_user.id,
        event_id=event.id
    ).first()
    
    if not existing:
        new_reg = EventRegistration(user_id=current_user.id, event_id=event.id)
        db.session.add(new_reg)
        db.session.commit()
    
    return redirect(url_for('dashboard_events'))

# ---------------- CONSOLE: CHALLENGES ----------------

# @app.route("/dashboard/events") -> Removed, using /events above as main view

@app.route("/challenges")
@login_required
def challenges():
    # Fetch all tasks from all events (or filter by active events)
    tasks = CTFTask.query.all()
    
    # Enrich tasks with solve status for UI
    for task in tasks:
        # Check if solved by current user
        is_solved = TaskSolve.query.filter_by(
            user_id=current_user.id,
            task_id=task.id
        ).first()
        task.is_completed = bool(is_solved)
        
    return render_template("console/challenges.html", tasks=tasks)

@app.route("/event/<int:event_id>")
@login_required
def event_tasks(event_id):
    event = Event.query.get_or_404(event_id)
    tasks = CTFTask.query.filter_by(event_id=event.id).all()
    return render_template(
        "console/event_tasks.html",
        event=event,
        tasks=tasks
    )

# ---------------- TEAMS ----------------

@app.route("/teams")
@login_required
def teams():
    my_teams = Team.query.join(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()

    pending_requests = TeamRequest.query.join(Team).filter(
        Team.captain_id == current_user.id,
        TeamRequest.status == "pending"
    ).all()

    my_team_request = TeamRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(TeamRequest.id.desc()).first()

    return render_template(
        "console/teams.html",
        my_teams=my_teams,
        pending_requests=pending_requests,
        my_team_request=my_team_request
    )

# ---------------- CREATE TEAM ----------------

@app.route("/create-team", methods=["GET", "POST"])
@login_required
def create_team():
    if request.method == "POST":
        team = Team(
            name=request.form.get("team_name"),
            captain_id=current_user.id,
            invite_code=generate_invite_code()
        )
        db.session.add(team)
        db.session.commit()

        member = TeamMember(team_id=team.id, user_id=current_user.id)
        db.session.add(member)
        db.session.commit()

        # 📈 Activity Log
        activity = Activity(
            user_id=current_user.id,
            action=f"Created team \"{team.name}\"",
            type="team_join"
        )
        db.session.add(activity)
        db.session.commit()

        return redirect(url_for("teams"))

    return render_template("console/create_team.html")

# ---------------- JOIN TEAM ----------------

@app.route("/join-team", methods=["POST"])
@login_required
def join_team():
    invite_code = request.form.get("invite_code")
    team = Team.query.filter_by(invite_code=invite_code).first()
    if not team:
        return redirect(url_for("teams"))

    if TeamMember.query.filter_by(user_id=current_user.id, team_id=team.id).first():
        return redirect(url_for("teams"))

    old_req = TeamRequest.query.filter_by(
        user_id=current_user.id,
        team_id=team.id
    ).first()

    if old_req:
        if old_req.status == "rejected":
            db.session.delete(old_req)
            db.session.commit()
        else:
            return redirect(url_for("teams"))

    req = TeamRequest(
        team_id=team.id,
        user_id=current_user.id,
        status="pending"
    )
    db.session.add(req)
    db.session.commit()

    return redirect(url_for("teams"))

# ---------------- APPROVE / REJECT ----------------

@app.route("/approve-request/<int:req_id>", methods=["POST"])
@login_required
def approve_request(req_id):
    req = TeamRequest.query.get_or_404(req_id)
    team = Team.query.get(req.team_id)

    if team.captain_id != current_user.id:
        abort(403)

    # User ko team me add karo
    member = TeamMember(team_id=req.team_id, user_id=req.user_id)
    db.session.add(member)

    # Request ko delete karo taaki captain ke panel se hat jaye
    db.session.delete(req)
    db.session.commit()

    # 📈 Activity Log for the joining member
    activity = Activity(
        user_id=req.user_id,
        action=f"Joined team \"{team.name}\"",
        type="team_join"
    )
    db.session.add(activity)
    db.session.commit()

    return redirect(url_for("teams"))


@app.route("/reject-request/<int:req_id>", methods=["POST"])
@login_required
def reject_request(req_id):
    req = TeamRequest.query.get_or_404(req_id)
    team = Team.query.get(req.team_id)

    if team.captain_id != current_user.id:
        abort(403)

    # Request ko delete karo
    db.session.delete(req)
    db.session.commit()

    return redirect(url_for("teams"))

# ---------------- ADMIN ----------------

#@app.route("/admin/setup")
#@login_required
#def admin_setup():
  #  current_user.is_admin = True
  #
    db.session.commit()
  #  return "Admin enabled. Logout & login again."

@app.route("/admin")
@admin_required
def admin_panel():
    return render_template("admin/dashboard.html")

# ---------------- ADMIN BLOG MANAGEMENT ----------------

@app.route("/admin/blogs")
@admin_required
def admin_blogs():
    blogs = Blog.query.order_by(Blog.published_at.desc()).all()
    return render_template("admin/blogs.html", blogs=blogs)

@app.route("/admin/add-blog", methods=["GET", "POST"])
@admin_required
def admin_add_blog():
        
    if request.method == "POST":
        title = request.form.get("title")
        short_description = request.form.get("short_description")
        category = request.form.get("category")
        read_time = request.form.get("read_time")
        external_url = request.form.get("external_url")
        
        # Handle thumbnail upload
        thumbnail_filename = None
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                from datetime import datetime
                filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                thumbnail_filename = filename

        new_blog = Blog(
            title=title,
            short_description=short_description,
            category=category,
            read_time=read_time,
            external_url=external_url,
            thumbnail=thumbnail_filename
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for("admin_blogs"))

    return render_template("admin/add_blog.html")

@app.route("/admin/edit-blog/<int:blog_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_blog(blog_id):
        
    blog_item = Blog.query.get_or_404(blog_id)
    
    if request.method == "POST":
        blog_item.title = request.form.get("title")
        blog_item.short_description = request.form.get("short_description")
        blog_item.category = request.form.get("category")
        blog_item.read_time = request.form.get("read_time")
        blog_item.external_url = request.form.get("external_url")
        
        # Handle thumbnail upload
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                from datetime import datetime
                filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                blog_item.thumbnail = filename

        db.session.commit()
        return redirect(url_for("admin_blogs"))

    return render_template("admin/add_blog.html", blog=blog_item) # REUSING add_blog.html for edit

@app.route("/admin/delete-blog/<int:blog_id>", methods=["POST"])
@admin_required
def admin_delete_blog(blog_id):
    blog_item = Blog.query.get_or_404(blog_id)
    db.session.delete(blog_item)
    db.session.commit()
    return redirect(url_for("admin_blogs"))

# ---------------- ADMIN EVENTS LIST ----------------

@app.route("/admin/events")
@admin_required
def admin_events():
    events = Event.query.all()
    return render_template("admin/events.html", events=events)

# ---------------- ADMIN CREATE EVENT ----------------

@app.route("/admin/create-event", methods=["GET", "POST"])
@admin_required
def admin_create_event():

    if request.method == "POST":
        event = Event(
            name=request.form.get("name"),
            level=request.form.get("level"),
            description=request.form.get("description"),
            date=request.form.get("date"),
            status=request.form.get("status"),
            image=request.form.get("image")
        )
        db.session.add(event)
        db.session.commit()
        # Create ke baad events list par bhejo
        return redirect(url_for("admin_events"))

    return render_template("admin/create_event.html")


# ---------------- ADMIN ADD TASK (FIXED) ----------------

@app.route("/admin/add-task", methods=["GET", "POST"])
@admin_required
def admin_add_task():
    import os
    from werkzeug.utils import secure_filename
    import uuid
    
    events = Event.query.all()

    if request.method == "POST":
        event = None
        event_id = request.form.get("event_id")
        
        # Optional Event Logic
        if not event_id or event_id == "":
            event_id = None
        else:
            # If ID provided, validate existence
            event = Event.query.get(event_id)
            if not event:
                flash("Selected event not found. Task created as global.", "warning")
                event_id = None

        # Handle file uploads
        challenge_file_path = None
        preview_image_path = None
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(app.static_folder, 'uploads', 'ctf')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Handle challenge file upload
        if 'challenge_file' in request.files:
            files = request.files.getlist('challenge_file')
            uploaded_files = []
            for file in files:
                if file and file.filename:
                    # Generate unique filename
                    ext = os.path.splitext(file.filename)[1]
                    unique_filename = f"{uuid.uuid4().hex}{ext}"
                    file_path = os.path.join(upload_dir, unique_filename)
                    file.save(file_path)
                    uploaded_files.append(f"uploads/ctf/{unique_filename}")
            
            if uploaded_files:
                challenge_file_path = ','.join(uploaded_files)  # Store multiple files as comma-separated
        
        # Handle preview image upload
        if 'preview_image' in request.files:
            file = request.files['preview_image']
            if file and file.filename:
                # Generate unique filename
                ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                file_path = os.path.join(upload_dir, unique_filename)
                file.save(file_path)
                preview_image_path = f"uploads/ctf/{unique_filename}"

        # Get Level from Form or Fallback to Event Level
        form_level = request.form.get("level")
        task_level = form_level if form_level else (event.level if event else "Easy")

        task = CTFTask(
            title=request.form.get("title"),
            category=request.form.get("category"),
            description=request.form.get("description"),
            flag=request.form.get("flag"),
            points=int(request.form.get("points")),
            level=task_level,  
            event_id=event_id,
            hint=request.form.get("hint", ""),
            challenge_file=challenge_file_path,
            preview_image=preview_image_path
        )
        
        db.session.add(task)
        db.session.commit()
        flash("Task created successfully!", "success")
        return redirect(url_for("admin_manage_tasks"))

    return render_template("admin/add_task.html", events=events)


@app.route("/admin/manage-tasks")
@admin_required
def admin_manage_tasks():
    tasks = CTFTask.query.order_by(CTFTask.created_at.desc()).all()
    return render_template("admin/manage_tasks.html", tasks=tasks)


# ---------------- ADMIN DELETE EVENT ----------------

@app.route("/admin/delete-event/<int:event_id>", methods=["POST"])
@admin_required
def admin_delete_event(event_id):

    event = Event.query.get_or_404(event_id)

    # Pehle event ke saare tasks delete honge
    CTFTask.query.filter_by(event_id=event.id).delete()

    # Phir event delete hoga
    db.session.delete(event)
    db.session.commit()

    return redirect(url_for("admin_panel"))


# ---------------- ADMIN DELETE TASK ----------------

@app.route("/admin/delete-task/<int:task_id>")
@admin_required
def admin_delete_task(task_id):

    task = CTFTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("admin_add_task"))

# ---------------- ADMIN MANAGE TEAMS ----------------

@app.route("/admin/manage-teams")
@admin_required
def admin_manage_teams():

    teams = Team.query.all()
    team_data = []

    for team in teams:
        captain = User.query.get(team.captain_id)
        used_count = TeamMember.query.filter_by(team_id=team.id).count()

        team_data.append({
            "id": team.id,
            "name": team.name,
            "captain_username": captain.username if captain else "N/A",
            "invite_code": team.invite_code,
            "used_count": used_count
        })

    return render_template("admin/manage_teams.html", team_data=team_data)

# ---------------- ADMIN DELETE TEAM ----------------

@app.route("/admin/delete-team/<int:team_id>")
@admin_required
def admin_delete_team(team_id):

    TeamMember.query.filter_by(team_id=team_id).delete()
    TeamRequest.query.filter_by(team_id=team_id).delete()
    Team.query.filter_by(id=team_id).delete()
    db.session.commit()
    return redirect(url_for("admin_manage_teams"))

 # ---------------- STATIC PAGES ----------------

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/features")
def features():
    return render_template("features.html")




# ---------------- ORGANIZATIONS ----------------

@app.route("/organizations")
@login_required
def organizations():
    return render_template("console/organizations.html")


# ---------------- TASK DETAIL ----------------

@app.route("/task/<int:task_id>", methods=["GET", "POST"])
@login_required
def task_detail(task_id):
    task = CTFTask.query.get_or_404(task_id)
    user = current_user
    message = None

    # Check already solved or not
    already_solved = TaskSolve.query.filter_by(
        user_id=user.id,
        task_id=task.id
    ).first()

    if request.method == "POST":
        submitted_flag = request.form.get("flag")

        # Increase submission count
        task.submissions_count += 1

        # Save submission
        submission = TaskSubmission(
            user_id=user.id,
            task_id=task.id,
            submitted_flag=submitted_flag
        )

        if submitted_flag == task.flag:
            submission.is_correct = True

            if not already_solved:
                solve = TaskSolve(
                    user_id=user.id,
                    task_id=task.id
                )
                db.session.add(solve)

                task.solved_count += 1
                message = "✅ Correct Flag! Task Solved."
            else:
                message = "⚠️ You already solved this task."
        else:
            submission.is_correct = False
            message = "❌ Wrong Flag, try again."

        db.session.add(submission)
        db.session.commit()

    # Like / Dislike count
    likes = TaskLike.query.filter_by(task_id=task.id, is_like=True).count()
    dislikes = TaskLike.query.filter_by(task_id=task.id, is_like=False).count()

    return render_template(
        "console/task_detail.html",
        task=task,
        message=message,
        already_solved=already_solved,
        likes=likes,
        dislikes=dislikes,
        solved_count=task.solved_count,
        submissions_count=task.submissions_count
    )

# ---------------- API: TASK DETAILS ----------------

@app.route("/api/task/<int:task_id>")
@login_required
def api_task_detail(task_id):
    task = CTFTask.query.get_or_404(task_id)
    
    # Check if solved by current user
    solved = TaskSolve.query.filter_by(
        user_id=current_user.id,
        task_id=task.id
    ).first()

    # 📈 Activity Log
    # Only log if not already solved and haven't logged "Started" recently
    already_started = Activity.query.filter_by(
        user_id=current_user.id, 
        action=f"Started challenge \"{task.title}\"",
        type="start"
    ).first()
    
    if not solved and not already_started:
        activity = Activity(
            user_id=current_user.id,
            action=f"Started challenge \"{task.title}\"",
            type="start"
        )
        db.session.add(activity)
        db.session.commit()

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "category": task.category,
        "points": task.points,
        "level": task.level,
        "hint": task.hint,
        "solved_count": task.solved_count,
        "submissions_count": task.submissions_count,
        "already_solved": bool(solved),
        "challenge_file": task.challenge_file,
        "preview_image": task.preview_image
    }

# ---------------- API: FLAG SUBMISSION ----------------

@app.route("/api/task/submit", methods=["POST"])
@login_required
def api_submit_flag():
    data = request.get_json()
    if not data:
        return {"success": False, "message": "Invalid request"}, 400

    task_id = data.get("task_id")
    submitted_flag = data.get("flag", "").strip()
    
    task = CTFTask.query.get_or_404(task_id)
    user = current_user

    # Check already solved
    already_solved = TaskSolve.query.filter_by(
        user_id=user.id,
        task_id=task.id
    ).first()

    # Log submission
    task.submissions_count += 1
    submission = TaskSubmission(
        user_id=user.id,
        task_id=task.id,
        submitted_flag=submitted_flag
    )

    success = False
    if submitted_flag == task.flag:
        submission.is_correct = True
        if not already_solved:
            solve = TaskSolve(user_id=user.id, task_id=task.id)
            db.session.add(solve)
            task.solved_count += 1
            
            # 📈 XP Reward & Activity Log
            user.xp += task.points
            activity = Activity(
                user_id=user.id,
                action=f"Solved challenge \"{task.title}\"",
                type="solve"
            )
            db.session.add(activity)
            
            message = "✅ Correct Flag! Task Solved."
            success = True
        else:
            message = "⚠️ You already solved this task."
            success = True
    else:
        submission.is_correct = False
        message = "❌ Wrong Flag, try again."

    db.session.add(submission)
    db.session.commit()

    return {
        "success": success,
        "message": message,
        "already_solved": bool(already_solved)
    }

# ---------------- DASHBOARD: LIVE DATA APIs ----------------

def get_rank_info(xp):
    """Calculate rank and next level progress based on XP"""
    if xp < 1000:
        return "Beginner", 1000, xp
    elif xp < 3000:
        return "Intermediate", 3000, xp
    else:
        return "Advanced", 10000, xp # Max level cap placeholder

@app.route("/api/dashboard/stats")
@login_required
def api_dashboard_stats():
    user = current_user
    
    # Active challenges (solved by user)
    solved_count = TaskSolve.query.filter_by(user_id=user.id).count()
    
    # My teams count
    teams_count = TeamMember.query.filter_by(user_id=user.id).count()
    
    rank, next_xp, current_xp = get_rank_info(user.xp)
    
    return {
        "username": user.username,
        "player_id": user.id,
        "active_challenges": solved_count,
        "teams_count": teams_count,
        "rank": rank,
        "xp": user.xp,
        "next_xp_threshold": next_xp,
        "progress_percent": min(100, (user.xp / next_xp) * 100) if next_xp > 0 else 100
    }

@app.route("/api/dashboard/activity")
@login_required
def api_dashboard_activity():
    # Fetch recent activities for the user (Limit to 15)
    activities = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).limit(15).all()
    
    output = []
    from datetime import datetime
    
    for act in activities:
        # Simple time ago logic
        delta = datetime.utcnow() - act.created_at
        if delta.days > 0:
            time_str = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds // 3600 > 0:
            hours = delta.seconds // 3600
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds // 60 > 0:
            mins = delta.seconds // 60
            time_str = f"{mins} min{'s' if mins > 1 else ''} ago"
        else:
            time_str = "just now"
            
        output.append({
            "action": act.action,
            "type": act.type,
            "time_ago": time_str
        })
        
    return {"activities": output}

# ---------------- API: SCOREBOARD ----------------

@app.route("/api/scoreboard")
@login_required
def api_scoreboard():
    from sqlalchemy import func
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Query users with their solved challenge count
    # Using outerjoin to include users with 0 solves
    query = db.session.query(
        User.id,
        User.username,
        User.xp,
        func.count(TaskSolve.id).label('challenges_solved')
    ).outerjoin(
        TaskSolve, User.id == TaskSolve.user_id
    ).group_by(
        User.id
    ).order_by(
        User.xp.desc(), User.id.asc()  # Secondary sort by ID for consistent ordering
    )
    
    # Get total count for pagination
    total_users = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    users = query.limit(per_page).offset(offset).all()
    
    # Build response with rank calculation
    results = []
    base_rank = offset + 1
    for idx, (user_id, username, xp, solved) in enumerate(users):
        results.append({
            "rank": base_rank + idx,
            "user_id": user_id,
            "username": username,
            "xp": xp,
            "challenges_solved": solved,
            "is_current_user": user_id == current_user.id
        })
    
    return {
        "users": results,
        "page": page,
        "per_page": per_page,
        "total_users": total_users,
        "total_pages": (total_users + per_page - 1) // per_page  # Ceiling division
    }

# ---------------- MAKE ADMIN (TEMP) - DISABLED FOR SECURITY ----------------
# This route has been disabled as it's a security risk.
# Use the promote_admin.py script instead:
#   python promote_admin.py promote <email>
#
# @app.route("/make-admin")
# @login_required
# def make_admin():
#     current_user.is_admin = True
#     db.session.commit()
#     return "You are now admin. Logout and login again."

# ---------------- DATABASE INIT ----------------
with app.app_context():
    db.create_all()

# ---------------- RUN LOCAL ----------------
if __name__ == "__main__":
    app.run(debug=True)
