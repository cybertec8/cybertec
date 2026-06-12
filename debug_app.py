import sys
import traceback

with open("traceback.txt", "w") as f:
    try:
        from app import app
        f.write("App started successfully")
    except Exception:
        traceback.print_exc(file=f)
