import os
import uuid
from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user
from extensions import db
from models import Event, CTFTask, Team, User, TeamMember
from decorators import ctf_admin_required
from . import ctf_admin_bp

@ctf_admin_bp.route("/dashboard")
@ctf_admin_required
def dashboard():
    return render_template("ctf_admin/dashboard.html")

@ctf_admin_bp.route("/tasks")
@ctf_admin_required
def manage_tasks():
    tasks = CTFTask.query.order_by(CTFTask.created_at.desc()).all()
    return render_template("ctf_admin/manage_tasks.html", tasks=tasks)

@ctf_admin_bp.route("/tasks/create", methods=["GET", "POST"])
@ctf_admin_required
def add_task():
    events = Event.query.all()
    if request.method == "POST":
        event_id = request.form.get("event_id") or None
        
        challenge_file_path = None
        preview_image_path = None
        
        upload_dir = os.path.join(current_app.static_folder, 'uploads', 'ctf')
        os.makedirs(upload_dir, exist_ok=True)
        
        if 'challenge_file' in request.files:
            files = request.files.getlist('challenge_file')
            uploaded_files = []
            for file in files:
                if file and file.filename:
                    ext = os.path.splitext(file.filename)[1]
                    unique_filename = f"{uuid.uuid4().hex}{ext}"
                    file.save(os.path.join(upload_dir, unique_filename))
                    uploaded_files.append(f"uploads/ctf/{unique_filename}")
            if uploaded_files:
                challenge_file_path = ','.join(uploaded_files)
        
        if 'preview_image' in request.files:
            file = request.files['preview_image']
            if file and file.filename:
                ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                file.save(os.path.join(upload_dir, unique_filename))
                preview_image_path = f"uploads/ctf/{unique_filename}"

        task = CTFTask(
            title=request.form.get("title"),
            category=request.form.get("category"),
            description=request.form.get("description"),
            flag=request.form.get("flag"),
            points=int(request.form.get("points", 100)),
            level=request.form.get("level", "Easy"),
            event_id=event_id,
            hint=request.form.get("hint", ""),
            challenge_file=challenge_file_path,
            preview_image=preview_image_path
        )
        db.session.add(task)
        db.session.commit()
        flash("Task created successfully!", "success")
        return redirect(url_for("ctf_admin.manage_tasks"))
    return render_template("ctf_admin/add_task.html", events=events)

@ctf_admin_bp.route("/teams")
@ctf_admin_required
def manage_teams():
    teams = Team.query.all()
    team_data = []
    for team in teams:
        captain = User.query.get(team.captain_id)
        member_count = TeamMember.query.filter_by(team_id=team.id).count()
        team_data.append({
            "id": team.id,
            "name": team.name,
            "captain_username": captain.username if captain else "N/A",
            "invite_code": team.invite_code,
            "member_count": member_count
        })
    return render_template("ctf_admin/manage_teams.html", team_data=team_data)

@ctf_admin_bp.route("/scoreboard")
@ctf_admin_required
def scoreboard():
    return render_template("ctf_admin/scoreboard.html")

@ctf_admin_bp.route("/logs")
@ctf_admin_required
def logs():
    return render_template("ctf_admin/logs.html")
