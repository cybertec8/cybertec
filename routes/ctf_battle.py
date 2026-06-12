from functools import wraps
import json
import requests
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, current_app, Blueprint, abort
from flask_login import current_user, login_required
from extensions import db
from models import User
from ctf_battle_models import CTFEvent, CTFCategory, CTFChallenge, CTFEventSolve, ActivityLog, Submission, UserSession

from decorators import admin_required
from . import ctf_battle_bp, battle_bp

# ---------------- UTILS ----------------

def log_battle_activity(user_id, action, event_id=None):
    ip = request.remote_addr
    # In production with proxy, use request.headers.get('X-Forwarded-For', request.remote_addr)
    
    geo_data = {}
    try:
        # Using ip-api.com (free demo, limited to 45 req/min)
        # For production use a paid service or local MaxMind database
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        if response.status_code == 200:
            geo_data = response.json()
    except Exception as e:
        print(f"GeoIP error: {e}")

    log = ActivityLog(
        user_id=user_id,
        action=action,
        event_id=event_id,
        ip_address=ip,
        user_agent=request.headers.get('User-Agent'),
        city=geo_data.get('city'),
        region=geo_data.get('regionName'),
        country=geo_data.get('country'),
        lat=geo_data.get('lat'),
        lon=geo_data.get('lon')
    )
    db.session.add(log)
    
    # Update or create session
    if event_id:
        sess = UserSession.query.filter_by(user_id=user_id, event_id=event_id).first()
        if not sess:
            sess = UserSession(user_id=user_id, event_id=event_id)
            db.session.add(sess)
        sess.ip_address = ip
        sess.user_agent = request.headers.get('User-Agent')
        sess.last_active = datetime.utcnow()

    db.session.commit()

def record_submission(user_id, event_id, challenge_id, flag, is_correct):
    ip = request.remote_addr
    geo_data = {}
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        if response.status_code == 200:
            geo_data = response.json()
    except:
        pass

    sub = Submission(
        user_id=user_id,
        event_id=event_id,
        challenge_id=challenge_id,
        flag=flag,
        is_correct=is_correct,
        ip_address=ip,
        user_agent=request.headers.get('User-Agent'),
        city=geo_data.get('city'),
        region=geo_data.get('regionName'),
        country=geo_data.get('country'),
        lat=geo_data.get('lat'),
        lon=geo_data.get('lon')
    )
    db.session.add(sub)
    db.session.commit()
    return sub

def check_anti_cheat(user_id, event_id, challenge_id, ip_address, flag):
    # 1. Same IP Check: Multiple users from same IP
    same_ip_count = User.query.join(ActivityLog).filter(
        ActivityLog.ip_address == ip_address,
        ActivityLog.event_id == event_id,
        User.id != user_id
    ).distinct().count()
    
    if same_ip_count > 0:
        log_battle_activity(user_id, f"SECURITY ALERT: IP reuse detected ({ip_address})", event_id=event_id)

    # 2. Flag Sharing Check: Rapid solves of the same flag
    recent_solves = CTFEventSolve.query.filter(
        CTFEventSolve.challenge_id == challenge_id,
        CTFEventSolve.solved_at > datetime.utcnow() - timedelta(minutes=5)
    ).count()
    
    if recent_solves > 3: # threshold for "rapid" solves
        log_battle_activity(user_id, f"SECURITY ALERT: Rapid solve pattern for challenge {challenge_id}", event_id=event_id)

# ---------------- ADMIN ROUTES ----------------

@ctf_battle_bp.route("/")
@admin_required
def admin_dashboard():
    events = CTFEvent.query.order_by(CTFEvent.created_at.desc()).all()
    return render_template("admin/ctf_battle/dashboard.html", events=events)

@ctf_battle_bp.route("/event/create", methods=["GET", "POST"])
@admin_required
def admin_create_event():
    if request.method == "POST":
        start_time = datetime.strptime(request.form.get("start_time"), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get("end_time"), '%Y-%m-%dT%H:%M')
        
        event = CTFEvent(
            name=request.form.get("name"),
            description=request.form.get("description"),
            start_time=start_time,
            end_time=end_time,
            visibility=request.form.get("visibility", "Public")
        )
        db.session.add(event)
        db.session.commit()
        flash("CTF Battle Event created successfully!", "success")
        return redirect(url_for("ctf_battle.admin_dashboard"))
    
    return render_template("admin/ctf_battle/create_event.html")

@ctf_battle_bp.route("/event/<int:event_id>/manage", methods=["GET", "POST"])
@admin_required
def admin_manage_event(event_id):
    # This route is now a legacy pointer to the Hub
    return redirect(url_for("ctf_battle.event_hub", event_id=event_id))

@ctf_battle_bp.route("/event/<int:event_id>/update", methods=["POST"])
@admin_required
def admin_update_event_info(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    event.name = request.form.get("name")
    event.description = request.form.get("description")
    event.start_time = datetime.strptime(request.form.get("start_time"), '%Y-%m-%dT%H:%M')
    event.end_time = datetime.strptime(request.form.get("end_time"), '%Y-%m-%dT%H:%M')
    event.visibility = request.form.get("visibility", "Public")
    db.session.commit()
    flash("Event parameters updated successfully.", "success")
    return redirect(url_for("ctf_battle.event_hub", event_id=event.id, tab='settings'))

@ctf_battle_bp.route("/event/<int:event_id>/category/add", methods=["POST"])
@admin_required
def admin_add_category(event_id):
    cat = CTFCategory(event_id=event_id, name=request.form.get("cat_name"))
    db.session.add(cat)
    db.session.commit()
    flash(f"Category '{cat.name}' added.", "success")
    return redirect(url_for("ctf_battle.event_hub", event_id=event_id, tab='challenges'))

@ctf_battle_bp.route("/event/<int:event_id>/challenge/add", methods=["POST"])
@admin_required
def admin_add_challenge(event_id):
    chal = CTFChallenge(
        category_id=request.form.get("category_id"),
        title=request.form.get("title"),
        description=request.form.get("description"),
        flag=request.form.get("flag"),
        points=int(request.form.get("points", 100)),
        hint=request.form.get("hint", "")
    )
    db.session.add(chal)
    db.session.commit()
    flash(f"Challenge '{chal.title}' deployed.", "success")
    return redirect(url_for("ctf_battle.event_hub", event_id=event_id, tab='challenges'))

@ctf_battle_bp.route("/event/<int:event_id>/bulk-upload", methods=["POST"])
@admin_required
def admin_bulk_upload(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    file = request.files.get("json_file")
    if file:
        data = json.load(file)
        # Expected format: [{"category": "Web", "challenges": [...]}, ...]
        for item in data:
            cat = CTFCategory.query.filter_by(event_id=event.id, name=item['category']).first()
            if not cat:
                cat = CTFCategory(event_id=event.id, name=item['category'])
                db.session.add(cat)
                db.session.commit()
            
            for chal_data in item.get('challenges', []):
                chal = CTFChallenge(
                    category_id=cat.id,
                    title=chal_data['title'],
                    description=chal_data['description'],
                    flag=chal_data['flag'],
                    points=chal_data.get('points', 100),
                    hint=chal_data.get('hint', "")
                )
                db.session.add(chal)
        db.session.commit()
        flash("Bulk upload successful.", "success")
    return redirect(url_for("ctf_battle.event_hub", event_id=event.id, tab='challenges'))

@ctf_battle_bp.route("/event/<int:event_id>")
@admin_required
def event_hub(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    tab = request.args.get('tab', 'overview')
    
    # Common stats
    total_participants = db.session.query(db.func.count(db.distinct(UserSession.user_id))).filter_by(event_id=event.id).scalar() or 0
    total_solves = CTFEventSolve.query.filter_by(event_id=event.id).count()
    
    # Tab specific data
    data = {}
    if tab == 'challenges':
        data['categories'] = event.categories
    elif tab == 'participants':
        data['participants'] = UserSession.query.filter_by(event_id=event.id).order_by(UserSession.last_active.desc()).all()
    elif tab == 'submissions':
        data['submissions'] = Submission.query.filter_by(event_id=event.id).order_by(Submission.created_at.desc()).limit(100).all()
    elif tab == 'scoreboard':
        data['scores'] = db.session.query(
            User.username, 
            db.func.sum(CTFEventSolve.points).label('total_points'),
            db.func.max(CTFEventSolve.solved_at).label('last_solve')
        ).join(CTFEventSolve, User.id == CTFEventSolve.user_id)\
         .filter(CTFEventSolve.event_id == event.id)\
         .group_by(User.id)\
         .order_by(db.desc('total_points'), 'last_solve')\
         .all()
    elif tab == 'security':
        # Detective queries
        data['alerts'] = ActivityLog.query.filter(
            ActivityLog.event_id == event.id,
            ActivityLog.action.like("SECURITY ALERT%")
        ).order_by(ActivityLog.created_at.desc()).all()
        
        # IP Reuse Detection
        data['ip_reuse'] = db.session.query(
            ActivityLog.ip_address,
            db.func.count(db.distinct(ActivityLog.user_id)).label('user_count')
        ).filter(ActivityLog.event_id == event.id)\
         .group_by(ActivityLog.ip_address)\
         .having(db.func.count(db.distinct(ActivityLog.user_id)) > 1)\
         .all()

    return render_template("admin/ctf_battle/event_manage_hub.html", 
                           event=event, 
                           tab=tab, 
                           total_participants=total_participants,
                           total_solves=total_solves,
                           **data)

@ctf_battle_bp.route("/event/<int:event_id>/challenge/toggle/<int:chal_id>", methods=["POST"])
@admin_required
def admin_toggle_challenge(event_id, chal_id):
    chal = CTFChallenge.query.get_or_404(chal_id)
    chal.is_enabled = not chal.is_enabled
    db.session.commit()
    flash(f"Challenge '{chal.title}' {'enabled' if chal.is_enabled else 'disabled'}.", "success")
    return redirect(url_for("ctf_battle.event_hub", event_id=event_id, tab='challenges'))

@ctf_battle_bp.route("/event/<int:event_id>/freeze", methods=["POST"])
@admin_required
def admin_freeze_scoreboard(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    event.is_frozen = not event.is_frozen
    db.session.commit()
    status = "FROZEN" if event.is_frozen else "UNFROZEN"
    flash(f"Scoreboard is now {status}.", "success")
    return redirect(url_for("ctf_battle.event_hub", event_id=event.id, tab='scoreboard'))

@ctf_battle_bp.route("/event/<int:event_id>/export-csv")
@admin_required
def admin_export_scoreboard_csv(event_id):
    import io, csv
    from flask import Response
    
    event = CTFEvent.query.get_or_404(event_id)
    scores = db.session.query(
        User.username, 
        User.email,
        db.func.sum(CTFEventSolve.points).label('total_points')
    ).join(CTFEventSolve, User.id == CTFEventSolve.user_id)\
     .filter(CTFEventSolve.event_id == event.id)\
     .group_by(User.id)\
     .order_by(db.desc('total_points'))\
     .all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Rank', 'Username', 'Email', 'Total Points'])
    for i, s in enumerate(scores):
        cw.writerow([i+1, s.username, s.email, s.total_points])
    
    output.headers["Content-Disposition"] = f"attachment; filename=scoreboard_event_{event_id}.csv"
    return output

@ctf_battle_bp.route("/event/<int:event_id>/toggle-status", methods=["POST"])
@admin_required
def admin_toggle_event_status(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    new_status = request.form.get("status")
    if new_status in ["Live", "Paused", "Ended", "Upcoming"]:
        event.status = new_status
        db.session.commit()
        log_battle_activity(current_user.id, f"Changed event status to: {new_status}", event_id=event.id)
        flash(f"Event status updated to {new_status}.", "success")
    return redirect(url_for("ctf_battle.event_hub", event_id=event.id))

# --- Legacy Route Redirects for Hub Integration ---

@ctf_battle_bp.route("/event/<int:event_id>/scoreboard")
@admin_required
def admin_scoreboard(event_id):
    return redirect(url_for("ctf_battle.event_hub", event_id=event_id, tab='scoreboard'))

@ctf_battle_bp.route("/event/<int:event_id>/logs")
@admin_required
def admin_event_logs(event_id):
    return redirect(url_for("ctf_battle.event_hub", event_id=event_id, tab='security')) # Logs are now in Security/Submissions

@ctf_battle_bp.route("/event/<int:event_id>/delete", methods=["POST"])
@admin_required
def admin_delete_event(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    name = event.name
    db.session.delete(event)
    db.session.commit()
    flash(f"Operation '{name}' has been terminated and all data purged.", "danger")
    return redirect(url_for("ctf_battle.admin_dashboard"))

@ctf_battle_bp.route("/event/<int:event_id>/monitoring")
@admin_required
def admin_monitoring(event_id):
    return redirect(url_for("ctf_battle.event_hub", event_id=event_id, tab='overview')) # Central monitoring is Overview

# ---------------- USER ROUTES ----------------

@battle_bp.route("/")
@login_required
def portal():
    events = CTFEvent.query.filter(CTFEvent.visibility == "Public").order_by(CTFEvent.start_time.asc()).all()
    if events:
        return redirect(url_for("battle.event_view", event_id=events[0].id))
    
    # If no events, show empty battle home
    return render_template("ctf_battle/battle_home.html", events=[], json_events=[], now=datetime.utcnow())

@battle_bp.route("/event/<int:event_id>")
@login_required
def event_view(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    now = datetime.utcnow()
    
    # Calculate status
    if now < event.start_time:
        calc_status = "UPCOMING"
    elif now > event.end_time:
        calc_status = "ENDED"
    else:
        calc_status = "LIVE"
    
    event.calculated_status = calc_status
    
    # Create serialized version for JS countdown
    json_events = [event.to_dict()]
    json_events[0]['calculated_status'] = calc_status
    
    # Always show the tactical status page (battle_home style)
    return render_template("ctf_battle/battle_home.html", events=[event], json_events=json_events, now=now)

@battle_bp.route("/event/<int:event_id>/arena")
@login_required
def event_arena(event_id):
    event = CTFEvent.query.get_or_404(event_id)
    now = datetime.utcnow()
    
    if now < event.start_time:
        flash("Operational window is not yet open.", "warning")
        return redirect(url_for("battle.event_view", event_id=event.id))
    
    if now > event.end_time:
        # Scoreboard final view
        scores = db.session.query(
            User.username, 
            db.func.sum(CTFEventSolve.points).label('total_points'),
            db.func.max(CTFEventSolve.solved_at).label('last_solve')
        ).join(CTFEventSolve, User.id == CTFEventSolve.user_id)\
         .filter(CTFEventSolve.event_id == event.id)\
         .group_by(User.id)\
         .order_by(db.desc('total_points'), 'last_solve')\
         .all()
        return render_template("ctf_battle/event_ended.html", event=event, scores=scores)
    
    # Live event view
    log_battle_activity(current_user.id, "Entered Arena", event_id=event.id)
    user_solves = [s.challenge_id for s in CTFEventSolve.query.filter_by(user_id=current_user.id, event_id=event.id).all()]
    return render_template("ctf_battle/event_live.html", event=event, user_solves=user_solves)

@battle_bp.route("/submit", methods=["POST"])
@login_required
def submit_flag():
    challenge_id = request.form.get("challenge_id")
    submitted_flag = request.form.get("flag").strip()
    
    challenge = CTFChallenge.query.get_or_404(challenge_id)
    event = challenge.category_rel.event
    now = datetime.utcnow()
    
    if now < event.start_time or now > event.end_time:
        flash("Event is not live.", "danger")
        return redirect(url_for("battle.event_arena", event_id=event.id))
    
    if event.status == "Paused":
        flash("Event is currently paused by administrator.", "warning")
        return redirect(url_for("battle.event_arena", event_id=event.id))
    
    existing_solve = CTFEventSolve.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first()
    if existing_solve:
        flash("Already solved.", "warning")
        return redirect(url_for("battle.event_arena", event_id=event.id))
    
    is_correct = (submitted_flag == challenge.flag)
    
    # Record everything for monitoring
    record_submission(current_user.id, event.id, challenge.id, submitted_flag, is_correct)
    
    # Perform Anti-cheat check
    check_anti_cheat(current_user.id, event.id, challenge.id, request.remote_addr, submitted_flag)

    if is_correct:
        solve = CTFEventSolve(
            event_id=event.id,
            challenge_id=challenge.id,
            user_id=current_user.id,
            points=challenge.points
        )
        db.session.add(solve)
        log_battle_activity(current_user.id, f"Solved challenge: {challenge.title}", event_id=event.id)
        db.session.commit()
        flash("Correct flag!", "success")
    else:
        log_battle_activity(current_user.id, f"Incorrect flag submission for: {challenge.title}", event_id=event.id)
        flash("Wrong flag.", "danger")
        
    return redirect(url_for("battle.event_arena", event_id=event.id))
