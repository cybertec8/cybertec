"""
Admin Management Script for Cybertec8 CTF Platform

Usage:
    python promote_admin.py promote <email>   # Grant admin privileges
    python promote_admin.py revoke <email>    # Revoke admin privileges
    python promote_admin.py list              # List all admins
    python promote_admin.py users             # List all users
    python promote_admin.py check <email>     # Check if user is admin
"""

import sys
from app import app, db, User


def promote_user(email, force=False):
    """Grant is_admin=True to a user."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"❌ User '{email}' not found.")
            list_all_users()
            return False

        if user.is_admin:
            print(f"⚠️  '{user.username}' ({email}) is already an admin.")
            return True

        if not force:
            print(f"\n⚠️  You are about to grant ADMIN access to '{user.username}' ({email}).")
            print("Admins have full access to /admin/* routes.")
            confirm = input("\nConfirm? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("❌ Cancelled.")
                return False

        user.is_admin = True
        db.session.commit()
        print(f"\n✅ Done: '{user.username}' ({email}) is now an admin.")
        print("ℹ️  User must log out and log back in for changes to take effect.")
        return True


def revoke_admin(email, force=False):
    """Revoke is_admin from a user."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"❌ User '{email}' not found.")
            return False

        if not user.is_admin:
            print(f"⚠️  '{user.username}' ({email}) is not an admin.")
            return True

        if not force:
            print(f"\n⚠️  You are about to revoke admin access from '{user.username}' ({email}).")
            confirm = input("Confirm? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("❌ Cancelled.")
                return False

        user.is_admin = False
        db.session.commit()
        print(f"\n✅ Done: Admin access revoked from '{user.username}' ({email}).")
        return True


def list_admins():
    """List all admin users."""
    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()
        if not admins:
            print("📋 No admin users found.")
            return
        print(f"\n📋 Admin Users ({len(admins)} total):")
        print("-" * 50)
        for u in admins:
            print(f"  • [{u.id}] {u.username} — {u.email}")


def list_all_users():
    """List all users."""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found.")
            return
        print(f"\n👥 All Users ({len(users)} total):")
        print("-" * 50)
        for u in users:
            badge = " [ADMIN]" if u.is_admin else ""
            print(f"  • [{u.id}] {u.username} — {u.email}{badge}")


def check_status(email):
    """Check a user's admin status."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"❌ User '{email}' not found.")
            return
        status = "✅ ADMIN" if user.is_admin else "👤 Normal User"
        print(f"\n{status}")
        print(f"  Name  : {user.username}")
        print(f"  Email : {user.email}")
        print(f"  ID    : {user.id}")


def print_usage():
    print(__doc__)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    force = "--force" in sys.argv or "-f" in sys.argv

    if command == "promote":
        if len(sys.argv) < 3:
            print("❌ Email required.  Usage: python promote_admin.py promote <email>")
            sys.exit(1)
        promote_user(sys.argv[2], force=force)

    elif command == "revoke":
        if len(sys.argv) < 3:
            print("❌ Email required.  Usage: python promote_admin.py revoke <email>")
            sys.exit(1)
        revoke_admin(sys.argv[2], force=force)

    elif command == "list":
        list_admins()

    elif command == "users":
        list_all_users()

    elif command == "check":
        if len(sys.argv) < 3:
            print("❌ Email required.  Usage: python promote_admin.py check <email>")
            sys.exit(1)
        check_status(sys.argv[2])

    else:
        print(f"❌ Unknown command '{command}'")
        print_usage()
        sys.exit(1)
