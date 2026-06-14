import os
import uuid
from flask import render_template, redirect, url_for, request, flash, current_app
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from extensions import db
from models import User, Team, TeamMember, Event, CTFTask, TaskSubmission, Activity, Blog
from decorators import admin_required
from . import admin_bp

@admin_bp.route("/")
def admin_root():
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    total_events = Event.query.count()
    total_tasks = CTFTask.query.count()
    active_users = User.query.count()
    total_submissions = TaskSubmission.query.count()
    recent_activities = Activity.query.order_by(Activity.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html",
        total_events=total_events,
        total_tasks=total_tasks,
        active_users=active_users,
        total_submissions=total_submissions,
        recent_activities=recent_activities
    )

@admin_bp.route("/users")
def manage_users():
    users = User.query.all()
    return render_template("admin/manage_users.html", users=users)

@admin_bp.route("/user/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete yourself!", "danger")
        return redirect(url_for("admin.manage_users"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.manage_users"))

# ---------------- ADMIN BLOG MANAGEMENT ----------------

@admin_bp.route("/blogs")
def admin_blogs():
    blogs = Blog.query.order_by(Blog.published_at.desc()).all()
    return render_template("admin/blogs.html", blogs=blogs)

@admin_bp.route("/add-blog", methods=["GET", "POST"])
def admin_add_blog():
    upload_folder = os.path.join(current_app.static_folder, "uploads/blogs")
    if request.method == "POST":
        title = request.form.get("title")
        short_description = request.form.get("short_description")
        category = request.form.get("category")
        read_time = request.form.get("read_time")
        external_url = request.form.get("external_url")

        thumbnail_filename = None
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
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
        return redirect(url_for("admin.admin_blogs"))

    return render_template("admin/add_blog.html")

@admin_bp.route("/edit-blog/<int:blog_id>", methods=["GET", "POST"])
def admin_edit_blog(blog_id):
    blog_item = Blog.query.get_or_404(blog_id)
    upload_folder = os.path.join(current_app.static_folder, "uploads/blogs")

    if request.method == "POST":
        blog_item.title = request.form.get("title")
        blog_item.short_description = request.form.get("short_description")
        blog_item.category = request.form.get("category")
        blog_item.read_time = request.form.get("read_time")
        blog_item.external_url = request.form.get("external_url")

        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
                blog_item.thumbnail = filename

        db.session.commit()
        return redirect(url_for("admin.admin_blogs"))

    return render_template("admin/add_blog.html", blog=blog_item)

@admin_bp.route("/delete-blog/<int:blog_id>", methods=["POST"])
def admin_delete_blog(blog_id):
    blog_item = Blog.query.get_or_404(blog_id)
    db.session.delete(blog_item)
    db.session.commit()
    return redirect(url_for("admin.admin_blogs"))

# ---------------- ADMIN EVENTS LIST ----------------

@admin_bp.route("/events")
def admin_events():
    events = Event.query.all()
    return render_template("admin/events.html", events=events)

@admin_bp.route("/create-event", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_events"))

    return render_template("admin/create_event.html")

# ---------------- ADMIN TASKS ----------------

@admin_bp.route("/add-task", methods=["GET", "POST"])
def admin_add_task():
    events = Event.query.all()

    if request.method == "POST":
        event_id = request.form.get("event_id")
        if not event_id or event_id == "":
            event_id = None
        else:
            event = Event.query.get(event_id)
            if not event:
                flash("Selected event not found.", "warning")
                event_id = None

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

        form_level = request.form.get("level")
        task = CTFTask(
            title=request.form.get("title"),
            category=request.form.get("category"),
            description=request.form.get("description"),
            flag=request.form.get("flag"),
            points=int(request.form.get("points", 100)),
            level=form_level or "Easy",
            event_id=event_id,
            hint=request.form.get("hint", ""),
            challenge_file=challenge_file_path,
            preview_image=preview_image_path
        )
        db.session.add(task)
        db.session.commit()
        flash("Task added successfully!", "success")
        return redirect(url_for("admin.admin_manage_tasks"))

    return render_template("admin/add_task.html", events=events)

@admin_bp.route("/manage-tasks")
def admin_manage_tasks():
    tasks = CTFTask.query.all()
    return render_template("admin/manage_tasks.html", tasks=tasks)

@admin_bp.route("/manage-teams")
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

@admin_bp.route("/delete-team/<int:team_id>")
def admin_delete_team(team_id):
    TeamMember.query.filter_by(team_id=team_id).delete()
    # If TeamRequest exists, delete it too
    from models import TeamRequest
    TeamRequest.query.filter_by(team_id=team_id).delete()
    Team.query.filter_by(id=team_id).delete()
    db.session.commit()
    flash("Team decommissioned successfully.", "success")
    return redirect(url_for("admin.admin_manage_teams"))

@admin_bp.route("/delete-event/<int:event_id>", methods=["POST"])
def admin_delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    # Delete associated tasks first
    from models import CTFTask
    CTFTask.query.filter_by(event_id=event.id).delete()
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully.", "success")
    return redirect(url_for("admin.admin_events"))

@admin_bp.route("/delete-task/<int:task_id>", methods=["POST"])
def admin_delete_task(task_id):
    task = CTFTask.query.get_or_404(task_id)
    # Related records delete karo
    from models import TaskSolve, TaskSubmission, TaskLike
    TaskSolve.query.filter_by(task_id=task.id).delete()
    TaskSubmission.query.filter_by(task_id=task.id).delete()
    TaskLike.query.filter_by(task_id=task.id).delete()
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully.", "success")
    return redirect(url_for("admin.admin_manage_tasks"))
