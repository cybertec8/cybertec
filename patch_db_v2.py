import sqlite3
import os

def patch_db():
    db_path = 'ctf.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Adding is_frozen to ctf_battle_event...")
    try:
        cursor.execute("ALTER TABLE ctf_battle_event ADD COLUMN is_frozen BOOLEAN DEFAULT 0")
        print("Added column is_frozen to ctf_battle_event.")
    except sqlite3.OperationalError:
        print("Column is_frozen already exists in ctf_battle_event.")

    print("Adding is_enabled to ctf_battle_challenge...")
    try:
        cursor.execute("ALTER TABLE ctf_battle_challenge ADD COLUMN is_enabled BOOLEAN DEFAULT 1")
        print("Added column is_enabled to ctf_battle_challenge.")
    except sqlite3.OperationalError:
        print("Column is_enabled already exists in ctf_battle_challenge.")

    print("Creating ctf_battle_session table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ctf_battle_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (event_id) REFERENCES ctf_battle_event (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database patch v2 completed.")

if __name__ == "__main__":
    patch_db()
