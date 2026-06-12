import sqlite3
import os

# Path to the database file
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
        # 1. Disable Foreign Keys
        cursor.execute("PRAGMA foreign_keys=OFF")

        # 2. Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ctf_task'")
        if not cursor.fetchone():
            print("Table 'ctf_task' does not exist. Migration skipped.")
            return

        print("Starting migration to make event_id nullable...")

        # 3. Rename old table
        cursor.execute("ALTER TABLE ctf_task RENAME TO ctf_task_old")

        # 4. Create new table with nullable event_id
        create_table_sql = """
        CREATE TABLE ctf_task (
            id INTEGER NOT NULL, 
            event_id INTEGER, 
            title VARCHAR(150) NOT NULL, 
            category VARCHAR(50), 
            description TEXT, 
            flag VARCHAR(150), 
            points INTEGER, 
            level VARCHAR(50) NOT NULL, 
            challenge_file VARCHAR(500), 
            preview_image VARCHAR(500), 
            hint TEXT, 
            solved_count INTEGER, 
            submissions_count INTEGER, 
            created_at DATETIME, 
            PRIMARY KEY (id), 
            FOREIGN KEY(event_id) REFERENCES event (id)
        );
        """
        cursor.execute(create_table_sql)

        # 5. Copy data (preserving IDs)
        # Note: If validation fails for existing data (e.g. strict NOT NULL is removed but data is fine), copying is safe.
        cursor.execute("""
            INSERT INTO ctf_task (
                id, event_id, title, category, description, flag, points, level, 
                challenge_file, preview_image, hint, solved_count, submissions_count, created_at
            )
            SELECT 
                id, event_id, title, category, description, flag, points, level, 
                challenge_file, preview_image, hint, solved_count, submissions_count, created_at
            FROM ctf_task_old
        """)

        # 6. Drop old table
        cursor.execute("DROP TABLE ctf_task_old")

        # 7. Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")

        conn.commit()
        print("Migration successful: event_id is now nullable in ctf_task.")

    except Exception as e:
        print(f"Error migrating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    patch_database()
