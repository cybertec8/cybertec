import sqlite3
import os

# Path to the database file (SAME AS app.py BASE_DIR)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'ctf.db')

def patch_database():
    print(f"Connecting to database at {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print("Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(event)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Current columns in 'event': {columns}")

        # Add 'date' column
        if 'date' not in columns:
            print("Adding 'date' column...")
            cursor.execute("ALTER TABLE event ADD COLUMN date TEXT")
        else:
            print("'date' column already exists.")

        # Add 'status' column
        if 'status' not in columns:
            print("Adding 'status' column...")
            cursor.execute("ALTER TABLE event ADD COLUMN status TEXT DEFAULT 'Upcoming'")
        else:
            print("'status' column already exists.")

        # Add 'image' column
        if 'image' not in columns:
            print("Adding 'image' column...")
            cursor.execute("ALTER TABLE event ADD COLUMN image TEXT")
        else:
            print("'image' column already exists.")

        conn.commit()
        print("Database patched successfully.")

    except Exception as e:
        print(f"Error patching database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_database()
