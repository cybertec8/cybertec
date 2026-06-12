import sqlite3
import os

db_path = "ctf.db"

def patch_db():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Checking for 'role' column in 'user' table...")
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'role' not in columns:
            print("Adding 'role' column to 'user' table...")
            cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(50) DEFAULT 'user'")
            conn.commit()
            print("Successfully added 'role' column.")
        else:
            print("'role' column already exists.")
            
    except Exception as e:
        print(f"Error patching database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_db()
