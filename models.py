from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# DATABASE INSTANCE
db = SQLAlchemy()

# ---------------- USER MODEL ----------------

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)

    # 👑 ADMIN FLAG
    is_admin = db.Column(db.Boolean, default=False)

    # PROFILE DATA
    mobile = db.Column(db.String(15), default="")
    teams = db.Column(db.String(150), default="")
    events = db.Column(db.String(150), default="")
    bio = db.Column(db.Text, default="")
    
    # 📈 PROGRESS DATA
    xp = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

# ---------------- ACTIVITY MODEL ----------------

class Activity(db.Model):
    __tablename__ = "activity"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False) # e.g. "Solved challenge SQL Injection"
    type = db.Column(db.String(50)) # e.g. "solve", "team_join", "achievement"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("activities", lazy=True))


# ---------------- TEAM MODEL ----------------

class Team(db.Model):
    __tablename__ = "team"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    invite_code = db.Column(db.String(20), unique=True)
    captain_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    max_members = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- TEAM MEMBER ----------------

class TeamMember(db.Model):
    __tablename__ = "team_member"

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    role = db.Column(db.String(50), default="member")


# ---------------- TEAM JOIN REQUEST ----------------

class TeamRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")

    user = db.relationship("User", backref="team_requests")
    team = db.relationship("Team", backref="join_requests")


# ---------------- EVENT MODEL ----------------

class Event(db.Model):
    __tablename__ = "event"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    level = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Upcoming")
    image = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ctf_tasks = db.relationship(
        "CTFTask",
        backref="event",
        lazy=True,
        cascade="all, delete"
    )


# ---------------- EVENT REGISTRATION ----------------

class EventRegistration(db.Model):
    __tablename__ = "event_registration"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="unique_user_event_reg"),
    )


# ---------------- CTF TASK MODEL ----------------

class CTFTask(db.Model):
    __tablename__ = "ctf_task"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("event.id"),
        nullable=True
    )

    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    flag = db.Column(db.String(150))
    points = db.Column(db.Integer, default=100)

    level = db.Column(db.String(50), nullable=False)
    
    # 📂 FILE UPLOADS
    challenge_file = db.Column(db.String(500), nullable=True)
    preview_image = db.Column(db.String(500), nullable=True)

    # 🔥 NEW CORE FIELDS
    hint = db.Column(db.Text, default="")
    solved_count = db.Column(db.Integer, default=0)
    submissions_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =================================================
# ============ CORE CTF SYSTEM TABLES =============
# =================================================

# 1. TASK SOLVE (ek user ek task ek baar)
class TaskSolve(db.Model):
    __tablename__ = "task_solve"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    task_id = db.Column(db.Integer, db.ForeignKey("ctf_task.id"))
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "task_id", name="unique_user_task_solve"),
    )


# 2. TASK LIKE / DISLIKE (per user, ek baar)
class TaskLike(db.Model):
    __tablename__ = "task_like"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    task_id = db.Column(db.Integer, db.ForeignKey("ctf_task.id"))

    # True = Like, False = Dislike
    is_like = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "task_id", name="unique_user_task_like"),
    )


# 3. TASK SUBMISSIONS (har submit record)
class TaskSubmission(db.Model):
    __tablename__ = "task_submission"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    task_id = db.Column(db.Integer, db.ForeignKey("ctf_task.id"))
    submitted_flag = db.Column(db.String(255))
    is_correct = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- BLOG MODEL ----------------

class Blog(db.Model):
    __tablename__ = "blog"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255)) # Path to image
    short_description = db.Column(db.Text)
    category = db.Column(db.String(100))
    read_time = db.Column(db.String(50)) # e.g. "5 min read"
    external_url = db.Column(db.String(500)) # Link to Medium/Personal Blog
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Blog {self.title}>"
