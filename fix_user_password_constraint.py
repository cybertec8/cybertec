
import sqlite3
import os

# Path to the database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'ctf.db')

def migrate_database():
    print(f"Connecting to database at {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print("Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Step 1: Rename existing table
        print("Renaming 'user' table to 'user_old'...")
        cursor.execute("ALTER TABLE user RENAME TO user_old")

        # Step 2: Create new table with nullable password
        # I'll use the schema from the check_schema.py output
        print("Creating new 'user' table with nullable password...")
        cursor.execute("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(150) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password VARCHAR(150),
                is_admin BOOLEAN DEFAULT 0,
                mobile VARCHAR(15) DEFAULT '',
                teams VARCHAR(150) DEFAULT '',
                events VARCHAR(150) DEFAULT '',
                bio TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                xp INTEGER DEFAULT 0,
                google_id TEXT UNIQUE
            )
        """)

        # Step 3: Copy data from old table to new table
        print("Copying data from 'user_old' to 'user'...")
        # Note: mapping columns carefully based on schema output
        cursor.execute("""
            INSERT INTO user (
                id, username, email, password, is_admin, 
                mobile, teams, events, bio, created_at, xp, google_id
            )
            SELECT 
                id, username, email, password, is_admin, 
                mobile, teams, events, bio, created_at, xp, google_id
            FROM user_old
        """)

        # Step 4: Drop old table
        print("Dropping 'user_old' table...")
        cursor.execute("DROP TABLE user_old")

        conn.commit()
        print("Database migration completed successfully.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        # Try to restore if possible
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE name='user_old'")
            if cursor.fetchone():
                print("Attempting to restore 'user' table from 'user_old'...")
                cursor.execute("DROP TABLE IF EXISTS user")
                cursor.execute("ALTER TABLE user_old RENAME TO user")
                conn.commit()
                print("Restore successful.")
        except Exception as restore_e:
            print(f"Restore failed: {restore_e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
