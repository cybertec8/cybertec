import sqlite3
import os

# Root directory to search from (up one level from this script)
SEARCH_ROOT = os.path.dirname(os.path.abspath(__file__))
# Go up one more level to search the whole download folder if possible, 
# or just stick to current package + parent.
# Let's search the CWD recursively.

def get_columns(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(event)")
        cols = [r[1] for r in cursor.fetchall()]
        conn.close()
        return cols
    except Exception as e:
        return f"Error: {e}"

def find_and_check_dbs():
    print(f"Scanning for ctf.db starting from: {os.getcwd()}")
    found = []
    for root, dirs, files in os.walk(os.getcwd()):
        if "ctf.db" in files:
            path = os.path.join(root, "ctf.db")
            found.append(path)
    
    print(f"Found {len(found)} databases.")
    for path in found:
        print(f"\n--- Checking: {path} ---")
        cols = get_columns(path)
        print(f"Columns in 'event' table: {cols}")
        if 'date' in cols:
            print("✅ 'date' column present")
        else:
            print("❌ 'date' column MISSING")

if __name__ == "__main__":
    find_and_check_dbs()
