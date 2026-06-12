import sqlite3
import os

# Database file path
DB_FILE = "ctf.db"

def add_columns():
    if not os.path.exists(DB_FILE):
        print(f"Error: Database file '{DB_FILE}' not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Add challenge_file column
        try:
            cursor.execute("ALTER TABLE ctf_task ADD COLUMN challenge_file VARCHAR(500)")
            print("Added 'challenge_file' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("'challenge_file' column already exists.")
            else:
                print(f"Error adding 'challenge_file': {e}")

        # Add preview_image column
        try:
            cursor.execute("ALTER TABLE ctf_task ADD COLUMN preview_image VARCHAR(500)")
            print("Added 'preview_image' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("'preview_image' column already exists.")
            else:
                print(f"Error adding 'preview_image': {e}")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_columns()
