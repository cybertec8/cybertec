import requests

def verify_final_restoration():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("--- Final Panel Isolation Verification ---")
    
    # 1. Verify /admin/ (Main Admin)
    try:
        url = f"{base_url}/admin/"
        res = session.get(url)
        print(f"\n[Main Admin Panel (/admin/)]")
        print(f"Status: {res.status_code}")
        
        # Check Navbar items
        items = ["Events", "Create Event", "Blogs", "Exit"]
        for item in items:
            if item in res.text:
                print(f"PASS: Navbar contains '{item}'")
            else:
                print(f"FAIL: Navbar MISSING '{item}'")
                
        # Ensure CTF items are NOT present
        ctf_items = ["CTF Dashboard", "Teams", "Manage Tasks"]
        for item in ctf_items:
            if item in res.text:
                # Need to be careful, some items like "Teams" might be common, 
                # but "CTF Dashboard" should definitely be gone.
                if item == "Teams" and "/admin/ctf/teams" in res.text:
                    print(f"FAIL: /admin/ contains CTF link: '{item}'")
                elif item != "Teams":
                     print(f"FAIL: /admin/ contains CTF item: '{item}'")
            else:
                print(f"PASS: /admin/ does NOT contain CTF item: '{item}'")

    except Exception as e:
        print(f"ERROR on /admin/: {e}")

    # 2. Verify /ctf-admin/ (CTF Admin)
    try:
        url = f"{base_url}/ctf-admin/"
        res = session.get(url)
        print(f"\n[CTF Admin Panel (/ctf-admin/)]")
        print(f"Status: {res.status_code}")
        if "Challenges" in res.text and "Scoreboard" in res.text:
            print("PASS: CTF Admin Panel features confirmed.")
        else:
            print("FAIL: CTF Admin Panel features MISSING.")
    except Exception as e:
        print(f"ERROR on /ctf-admin/: {e}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_final_restoration()
