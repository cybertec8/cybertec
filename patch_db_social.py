import sqlite3
import os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ctf.db')

def patch_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add new social columns if they don't exist
    columns_to_add = [
        ("linkedin_url", "TEXT DEFAULT ''"),
        ("github_url", "TEXT DEFAULT ''"),
        ("discord_handle", "TEXT DEFAULT ''")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding column {col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Patching complete.")

if __name__ == "__main__":
    patch_db()
