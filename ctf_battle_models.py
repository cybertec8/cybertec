from datetime import datetime
from extensions import db

# ---------------- CTF BATTLE MODELS ----------------
# These tables are strictly isolated from the main CTF system.

class CTFEvent(db.Model):
    __tablename__ = "ctf_battle_event"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    visibility = db.Column(db.String(20), default="Public") # Public, Private (Invite Only)
    status = db.Column(db.String(20), default="Upcoming") # Upcoming, Live, Paused, Ended
    is_frozen = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    categories = db.relationship("CTFCategory", backref="event", cascade="all, delete-orphan", lazy=True)
    solves = db.relationship("CTFEventSolve", backref="event", cascade="all, delete-orphan", lazy=True)
    logs = db.relationship("ActivityLog", backref="event", cascade="all, delete-orphan", lazy=True)
    submissions = db.relationship("Submission", backref="event_rel", cascade="all, delete-orphan", lazy=True)
    sessions = db.relationship("UserSession", backref="event_rel", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "visibility": self.visibility,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class CTFCategory(db.Model):
    __tablename__ = "ctf_battle_category"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_event.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    challenges = db.relationship("CTFChallenge", backref="category_rel", cascade="all, delete-orphan", lazy=True)

class CTFChallenge(db.Model):
    __tablename__ = "ctf_battle_challenge"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_category.id"), nullable=False)
    
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    flag = db.Column(db.String(255), nullable=False)
    points = db.Column(db.Integer, default=100)
    is_enabled = db.Column(db.Boolean, default=True)
    
    hint = db.Column(db.Text, default="")
    files = db.Column(db.String(500)) # comma separated paths
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    solves = db.relationship("CTFEventSolve", backref="challenge", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "title": self.title,
            "description": self.description,
            "points": self.points,
            "hint": self.hint,
            "files": self.files,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class CTFEventSolve(db.Model):
    __tablename__ = "ctf_battle_solve"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_event.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_challenge.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    points = db.Column(db.Integer, nullable=False)
    solved_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="battle_solves")
    
    __table_args__ = (
        db.UniqueConstraint("user_id", "challenge_id", name="unique_user_battle_solve"),
    )

class ActivityLog(db.Model):
    __tablename__ = "ctf_battle_activity"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_event.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    
    # Geolocation data
    city = db.Column(db.String(100))
    region = db.Column(db.String(100))
    country = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="battle_logs")

class Submission(db.Model):
    __tablename__ = "ctf_battle_submission"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_event.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_challenge.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    flag = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    
    # Geolocation data
    city = db.Column(db.String(100))
    region = db.Column(db.String(100))
    country = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="battle_submissions")
    event = db.relationship("CTFEvent", backref="battle_submissions")
    challenge = db.relationship("CTFChallenge", backref="battle_submissions")

class UserSession(db.Model):
    __tablename__ = "ctf_battle_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("ctf_battle_event.id"), nullable=False)
    
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship("User", backref="battle_sessions")
    event = db.relationship("CTFEvent", backref="battle_sessions")
