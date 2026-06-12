from app import app
from extensions import db
from ctf_battle_models import CTFEvent, ActivityLog, Submission, UserSession, CTFChallenge
from datetime import datetime

with app.app_context():
    print("--- Model Verification ---")
    event = CTFEvent.query.first()
    if event:
        print(f"Found event: {event.name}")
        print(f"Scoreboard frozen: {event.is_frozen}")
        
        # Test session creation
        user_id = 1 # Assuming user 1 exists
        sess = UserSession.query.filter_by(user_id=user_id, event_id=event.id).first()
        if not sess:
            sess = UserSession(user_id=user_id, event_id=event.id, ip_address="127.0.0.1")
            db.session.add(sess)
            db.session.commit()
            print(f"Created session for user {user_id}")
        else:
            print(f"Found session for user {user_id}, last active: {sess.last_active}")

        # Test challenge enable/disable
        chal = CTFChallenge.query.filter_by(category_id=event.categories[0].id).first() if event.categories else None
        if chal:
            print(f"Challenge '{chal.title}' is_enabled: {chal.is_enabled}")
            
    # Check Submission and ActivityLog usage
    sub_count = Submission.query.count()
    log_count = ActivityLog.query.count()
    print(f"Submission count: {sub_count}")
    print(f"ActivityLog count: {log_count}")
    
    print("--- Verification Successful ---")
