import sqlite3
import os

def patch_db():
    db_path = 'ctf.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Patching ctf_battle_activity...")
    columns_to_add = [
        ("city", "TEXT"),
        ("region", "TEXT"),
        ("country", "TEXT"),
        ("lat", "REAL"),
        ("lon", "REAL")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE ctf_battle_activity ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to ctf_battle_activity.")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists in ctf_battle_activity.")

    print("Creating ctf_battle_submission table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ctf_battle_submission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            flag TEXT NOT NULL,
            is_correct BOOLEAN DEFAULT 0,
            ip_address TEXT,
            user_agent TEXT,
            city TEXT,
            region TEXT,
            country TEXT,
            lat REAL,
            lon REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES ctf_battle_event (id),
            FOREIGN KEY (challenge_id) REFERENCES ctf_battle_challenge (id),
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database patch completed.")

if __name__ == "__main__":
    patch_db()
