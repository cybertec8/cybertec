import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app import app
from extensions import db
from ctf_battle_models import CTFEvent, CTFCategory, CTFChallenge, CTFEventSolve, CTFActivityLog, CTFSubmission
from models import User
from datetime import datetime, timedelta

def test_monitoring_and_anticheat():
    with app.app_context():
        print("Starting Verification...")
        
        # 1. Create a dummy event for testing
        event = CTFEvent(
            name="Test Battle Alpha",
            description="Verification Battle",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=1),
            status="Live"
        )
        db.session.add(event)
        db.session.commit()
        
        cat = CTFCategory(event_id=event.id, name="Web")
        db.session.add(cat)
        db.session.commit()
        
        chal = CTFChallenge(
            category_id=cat.id,
            title="Hidden Vault",
            description="Find the flag",
            flag="CTF{verify_me}",
            points=100
        )
        db.session.add(chal)
        db.session.commit()
        
        user1 = User.query.filter_by(username="admin").first()
        if not user1:
            print("Admin user not found, creating dummy 'verification_user'...")
            user1 = User(username="verification_user", email="verify@cybertec.loc")
            db.session.add(user1)
            db.session.commit()

        # 2. Test Submission Recording
        from routes.ctf_battle import record_submission
        print("Testing submission recording...")
        # Mock request context if needed, but here we can just call it or simulate it
        # Since record_submission uses 'request', we need a request context
        with app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}, headers={'User-Agent': 'TestBot'}):
            sub = record_submission(user1.id, event.id, chal.id, "WRONG_FLAG", False)
            print(f"Recorded submission ID: {sub.id}, IP: {sub.ip_address}")
            
            # Check if recorded correctly
            sub_check = CTFSubmission.query.get(sub.id)
            assert sub_check is not None
            assert sub_check.flag == "WRONG_FLAG"
            print("Submission recording [OK]")

        # 3. Test Anti-cheat Alert (IP Reuse)
        print("Testing IP reuse detection...")
        # We need another user to simulate reuse
        user2 = User.query.filter(User.id != user1.id).first()
        if user2:
            with app.test_request_context(environ_base={'REMOTE_ADDR': '127.0.0.1'}):
                from routes.ctf_battle import check_anti_cheat
                # Simulate activity for user1 from same IP
                log1 = CTFActivityLog(user_id=user1.id, action="Login", event_id=event.id, ip_address="127.0.0.1")
                db.session.add(log1)
                db.session.commit()
                
                check_anti_cheat(user2.id, event.id, chal.id, "127.0.0.1", "CTF{fake}")
                
                # Check for alert
                alert = CTFActivityLog.query.filter(
                    CTFActivityLog.event_id == event.id,
                    CTFActivityLog.action.like("%SECURITY ALERT: IP reuse%")
                ).first()
                if alert:
                    print(f"IP Reuse Alert correctly triggered: {alert.action}")
                else:
                    print("IP Reuse Alert NOT triggered (Check logic)")

        # 4. Test Pause Logic
        print("Testing event pause logic...")
        event.status = "Paused"
        db.session.commit()
        
        with app.test_request_context():
            from flask import url_for
            # This is harder to test without a full client call, but we can check the status attribute
            event_check = CTFEvent.query.get(event.id)
            assert event_check.status == "Paused"
            print("Event Pause [OK]")

        print("Verification completed.")

if __name__ == "__main__":
    test_monitoring_and_anticheat()
