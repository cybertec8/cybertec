import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'ctf.db')

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if google_id already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'google_id' not in columns:
            print("Adding google_id column to user table...")
            # SQLite does not allow adding UNIQUE column via ALTER TABLE
            cursor.execute("ALTER TABLE user ADD COLUMN google_id TEXT")
            conn.commit()
            print("Successfully added google_id column.")
        else:
            print("google_id column already exists.")
            
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_db()
