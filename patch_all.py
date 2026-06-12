import sqlite3
import os

def patch_file(db_path):
    print(f"Patching: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(event)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'date' not in columns:
            print("Adding 'date'...")
            cursor.execute("ALTER TABLE event ADD COLUMN date TEXT")
        
        if 'status' not in columns:
            print("Adding 'status'...")
            cursor.execute("ALTER TABLE event ADD COLUMN status TEXT DEFAULT 'Upcoming'")
            
        if 'image' not in columns:
            print("Adding 'image'...")
            cursor.execute("ALTER TABLE event ADD COLUMN image TEXT")
            
        conn.commit()
        conn.close()
        print("Success.")
    except Exception as e:
        print(f"Failed to patch {db_path}: {e}")

def patch_all():
    print(f"Scanning from: {os.getcwd()}")
    for root, dirs, files in os.walk(os.getcwd()):
        if "ctf.db" in files:
            path = os.path.join(root, "ctf.db")
            patch_file(path)

if __name__ == "__main__":
    patch_all()
