import os
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, current_app, abort
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from extensions import db
from models import (
    User, Team, TeamMember, TeamRequest, 
    Event, EventRegistration, CTFTask, 
    TaskSolve, TaskLike, TaskSubmission, Activity
)
from utils import generate_invite_code
from . import participant_bp


# ---------------- DASHBOARD ----------------

@participant_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return render_template("console/dashboard.html")

# ---------------- SCOREBOARD ----------------

@participant_bp.route("/scoreboard")
@login_required
def scoreboard():
    return render_template("console/scoreboard.html")

# ---------------- PROFILE ----------------

@participant_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        new_username = request.form.get("username")
        new_mobile = request.form.get("mobile")
        new_bio = request.form.get("bio")
        new_linkedin = request.form.get("linkedin_url")
        new_github = request.form.get("github_url")
        new_discord = request.form.get("discord_handle")
        selected_avatar = request.form.get("avatar")

        # Username validation
        if new_username and new_username != current_user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash("Username already taken!", "danger")
                return render_template("auth/test_profile.html")
            current_user.username = new_username

        # Avatar selection
        if selected_avatar:
            current_user.avatar_filename = selected_avatar
            current_user.avatar_type = "default"

        # Update fields
        current_user.mobile = new_mobile
        current_user.mobile_number = new_mobile  # Sync both mobile fields
        current_user.bio = new_bio
        current_user.linkedin_url = new_linkedin
        current_user.github_url = new_github
        current_user.discord_handle = new_discord
        current_user.profile_completed = True

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while saving your profile.", "danger")
            return render_template("auth/test_profile.html")

        flash("Profile saved successfully!", "success")
        return redirect(url_for("home"))

    return render_template("auth/test_profile.html")

# ---------------- PROFILE UPLOAD CONFIG ----------------
def get_upload_folder_profile():
    folder = os.path.join(current_app.static_folder, 'uploads/profile')
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    return folder

@participant_bp.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        new_username = request.form.get("username")
        new_mobile = request.form.get("mobile")
        new_bio = request.form.get("bio")
        new_linkedin = request.form.get("linkedin_url")
        new_github = request.form.get("github_url")
        new_discord = request.form.get("discord_handle")
        
        # 1. Validate Username Uniqueness (if changed)
        if new_username and new_username != current_user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash("Username already taken!", "danger")
                return render_template("auth/edit_profile.html")
            current_user.username = new_username

        # 2. Handle Profile Image Upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != "":
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                upload_folder = get_upload_folder_profile()
                file.save(os.path.join(upload_folder, filename))
                current_user.profile_image = f"uploads/profile/{filename}"
                current_user.avatar_type = "custom"
                current_user.avatar_filename = filename

        # 3. Update Other Fields
        current_user.mobile_number = new_mobile # Assuming we want to update mobile_number field
        current_user.mobile = new_mobile
        current_user.bio = new_bio
        current_user.linkedin_url = new_linkedin
        current_user.github_url = new_github
        current_user.discord_handle = new_discord
        
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("participant.profile"))

    return render_template("auth/edit_profile.html")

# ---------------- COMPLETE PROFILE ONBOARDING ----------------

@participant_bp.route("/complete-profile", methods=["GET", "POST"])
@login_required
def complete_profile():
    # Legacy onboarding route now redirects directly to the main profile page.
    return redirect(url_for('participant.profile'))



@participant_bp.route("/skip-profile", methods=["POST", "GET"])
@login_required
def skip_profile():
    if not current_user.avatar_filename:
        current_user.avatar_filename = "avatar1.png"
    current_user.avatar_type = "default"
    current_user.profile_completed = True
    db.session.commit()
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json
    if is_ajax:
        return {"success": True, "message": "Onboarding skipped"}
    
    flash("Onboarding skipped. Default settings applied.", "info")
    return redirect(url_for("home"))

# ---------------- EVENTS ----------------

@participant_bp.route("/dashboard/events")
@login_required
def dashboard_events():
    events = Event.query.all()
    regs = EventRegistration.query.filter_by(user_id=current_user.id).all()
    registered_event_ids = [r.event_id for r in regs]
    return render_template("console/events.html", events=events, registered_event_ids=registered_event_ids)

@participant_bp.route("/register-event/<int:event_id>", methods=["POST"])
@login_required
def register_event(event_id):
    event = Event.query.get_or_404(event_id)
    existing = EventRegistration.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if not existing:
        new_reg = EventRegistration(user_id=current_user.id, event_id=event.id)
        db.session.add(new_reg)
        db.session.commit()
    return redirect(url_for('participant.dashboard_events'))

# ---------------- CHALLENGES ----------------

@participant_bp.route("/challenges")
@login_required
def challenges():
    tasks = CTFTask.query.all()
    for task in tasks:
        is_solved = TaskSolve.query.filter_by(user_id=current_user.id, task_id=task.id).first()
        task.is_completed = bool(is_solved)
    return render_template("console/challenges.html", tasks=tasks)

@participant_bp.route("/event/<int:event_id>")
@login_required
def event_tasks(event_id):
    event = Event.query.get_or_404(event_id)
    tasks = CTFTask.query.filter_by(event_id=event.id).all()
    return render_template("console/event_tasks.html", event=event, tasks=tasks)

# ---------------- TASK DETAIL & SUBMISSION ----------------

@participant_bp.route("/task/<int:task_id>", methods=["GET", "POST"])
@login_required
def task_detail(task_id):
    task = CTFTask.query.get_or_404(task_id)
    message = None
    already_solved = TaskSolve.query.filter_by(user_id=current_user.id, task_id=task.id).first()

    if request.method == "POST":
        submitted_flag = request.form.get("flag", "").strip()
        task.submissions_count += 1
        submission = TaskSubmission(user_id=current_user.id, task_id=task.id, submitted_flag=submitted_flag)

        if submitted_flag == task.flag:
            submission.is_correct = True
            if not already_solved:
                solve = TaskSolve(user_id=current_user.id, task_id=task.id)
                db.session.add(solve)
                task.solved_count += 1
                
                # Update XP
                current_user.xp += task.points
                
                # Activity Log
                activity = Activity(user_id=current_user.id, action=f"Solved challenge \"{task.title}\"", type="solve")
                db.session.add(activity)
                
                message = "✅ Correct Flag! Task Solved."
            else:
                message = "⚠️ You already solved this task."
        else:
            submission.is_correct = False
            message = "❌ Wrong Flag, try again."

        db.session.add(submission)
        db.session.commit()

    likes = TaskLike.query.filter_by(task_id=task.id, is_like=True).count()
    dislikes = TaskLike.query.filter_by(task_id=task.id, is_like=False).count()

    return render_template("console/task_detail.html", task=task, message=message, already_solved=already_solved, 
                           likes=likes, dislikes=dislikes, solved_count=task.solved_count, submissions_count=task.submissions_count)

# ---------------- TEAMS ----------------

@participant_bp.route("/teams")
@login_required
def teams():
    my_teams = Team.query.join(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    pending_requests = TeamRequest.query.join(Team).filter(Team.captain_id == current_user.id, TeamRequest.status == "pending").all()
    my_team_request = TeamRequest.query.filter_by(user_id=current_user.id).order_by(TeamRequest.id.desc()).first()
    return render_template("console/teams.html", my_teams=my_teams, pending_requests=pending_requests, my_team_request=my_team_request)

@participant_bp.route("/create-team", methods=["GET", "POST"])
@login_required
def create_team():
    if request.method == "POST":
        team = Team(name=request.form.get("team_name"), captain_id=current_user.id, invite_code=generate_invite_code())
        db.session.add(team)
        db.session.commit()
        member = TeamMember(team_id=team.id, user_id=current_user.id)
        db.session.add(member)
        
        activity = Activity(user_id=current_user.id, action=f"Created team \"{team.name}\"", type="team_join")
        db.session.add(activity)
        db.session.commit()
        return redirect(url_for("participant.teams"))
    return render_template("console/create_team.html")

@participant_bp.route("/join-team", methods=["POST"])
@login_required
def join_team():
    invite_code = request.form.get("invite_code")
    team = Team.query.filter_by(invite_code=invite_code).first()
    if not team or TeamMember.query.filter_by(user_id=current_user.id, team_id=team.id).first():
        return redirect(url_for("participant.teams"))
    
    old_req = TeamRequest.query.filter_by(user_id=current_user.id, team_id=team.id).first()
    if old_req:
        if old_req.status == "rejected":
            db.session.delete(old_req)
            db.session.commit()
        else:
            return redirect(url_for("participant.teams"))

    req = TeamRequest(team_id=team.id, user_id=current_user.id, status="pending")
    db.session.add(req)
    db.session.commit()
    return redirect(url_for("participant.teams"))

@participant_bp.route("/approve-request/<int:req_id>", methods=["POST"])
@login_required
def approve_request(req_id):
    req = TeamRequest.query.get_or_404(req_id)
    team = Team.query.get(req.team_id)
    if team.captain_id != current_user.id:
        abort(403)
    member = TeamMember(team_id=req.team_id, user_id=req.user_id)
    db.session.add(member)
    db.session.delete(req)
    activity = Activity(user_id=req.user_id, action=f"Joined team \"{team.name}\"", type="team_join")
    db.session.add(activity)
    db.session.commit()
    return redirect(url_for("participant.teams"))

@participant_bp.route("/reject-request/<int:req_id>", methods=["POST"])
@login_required
def reject_request(req_id):
    req = TeamRequest.query.get_or_404(req_id)
    team = Team.query.get(req.team_id)
    if team.captain_id != current_user.id:
        abort(403)
    db.session.delete(req)
    db.session.commit()
    return redirect(url_for("participant.teams"))

# ---------------- ORGANIZATIONS ----------------

@participant_bp.route("/organizations")
@login_required
def organizations():
    return render_template("console/organizations.html")

# ---------------- API DATA ----------------

@participant_bp.route("/api/dashboard/stats")
@login_required
def api_dashboard_stats():
    user = current_user
    solved_count = TaskSolve.query.filter_by(user_id=user.id).count()
    teams_count = TeamMember.query.filter_by(user_id=user.id).count()
    
    # Simple rank logic
    if user.xp < 1000:
        rank, next_xp = "Beginner", 1000
    elif user.xp < 3000:
        rank, next_xp = "Intermediate", 3000
    else:
        rank, next_xp = "Advanced", 10000
        
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

@participant_bp.route("/api/dashboard/activity")
@login_required
def api_dashboard_activity():
    activities = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.created_at.desc()).limit(15).all()
    output = []
    for act in activities:
        delta = datetime.utcnow() - act.created_at
        if delta.days > 0:
            time_str = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds // 3600 > 0:
            time_str = f"{delta.seconds // 3600} hours ago"
        elif delta.seconds // 60 > 0:
            time_str = f"{delta.seconds // 60} mins ago"
        else:
            time_str = "just now"
        output.append({"action": act.action, "type": act.type, "time_ago": time_str})
    return {"activities": output}

@participant_bp.route("/api/task/<int:task_id>")
@login_required
def api_task_detail(task_id):
    task = CTFTask.query.get_or_404(task_id)
    solved = TaskSolve.query.filter_by(user_id=current_user.id, task_id=task.id).first()
    return {
        "id": task.id, "title": task.title, "description": task.description, "category": task.category,
        "points": task.points, "level": task.level, "hint": task.hint, "solved_count": task.solved_count,
        "submissions_count": task.submissions_count, "already_solved": bool(solved),
        "challenge_file": task.challenge_file, "preview_image": task.preview_image
    }

@participant_bp.route("/api/task/submit", methods=["POST"])
@login_required
def api_submit_flag():
    data = request.get_json()
    task_id = data.get("task_id")
    submitted_flag = data.get("flag", "").strip()
    task = CTFTask.query.get_or_404(task_id)
    
    already_solved = TaskSolve.query.filter_by(user_id=current_user.id, task_id=task.id).first()
    task.submissions_count += 1
    submission = TaskSubmission(user_id=current_user.id, task_id=task.id, submitted_flag=submitted_flag)

    success = False
    if submitted_flag == task.flag:
        submission.is_correct = True
        if not already_solved:
            solve = TaskSolve(user_id=current_user.id, task_id=task.id)
            db.session.add(solve)
            task.solved_count += 1
            current_user.xp += task.points
            activity = Activity(user_id=current_user.id, action=f"Solved challenge \"{task.title}\"", type="solve")
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
    return {"success": success, "message": message, "already_solved": bool(already_solved)}

# ---------------- SCOREBOARD API ----------------

@participant_bp.route("/api/scoreboard")
@login_required
def api_scoreboard():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    total_users = User.query.count()
    total_pages = max(1, -(-total_users // per_page))  # ceiling division

    users = (
        User.query
        .order_by(User.xp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    output = []
    for idx, user in enumerate(users, start=(page - 1) * per_page + 1):
        solved_count = TaskSolve.query.filter_by(user_id=user.id).count()
        output.append({
            "rank": idx,
            "username": user.username,
            "xp": user.xp or 0,
            "challenges_solved": solved_count,
            "is_current_user": user.id == current_user.id,
        })

    return {
        "users": output,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "total_users": total_users,
    }
