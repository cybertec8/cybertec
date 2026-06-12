import requests

def verify_refactor():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    # In DEV_MODE, accessing any route should auto-login DevAdmin
    routes_to_check = [
        # New CTF Blueprints
        ("/admin/ctf/tasks/manage", "Manage Tasks"),
        ("/admin/ctf/tasks/add", "Add New Task"),
        ("/admin/ctf/teams/manage", "Manage Teams"),
        # Existing Admin Routes
        ("/admin/events", "Manage Events"),
        ("/admin/blogs", "Admin - Manage Blogs"),
        ("/admin", "Admin Command Center")
    ]
    
    print("Verifying Admin Module Refactor...")
    
    all_passed = True
    for route, expected_text in routes_to_check:
        try:
            url = f"{base_url}{route}"
            print(f"Checking {url}...", end=" ")
            response = session.get(url)
            
            if response.status_code == 200:
                if expected_text in response.text:
                    print("SUCCESS")
                else:
                    print(f"FAILURE (Expected text '{expected_text}' not found)")
                    all_passed = False
            else:
                print(f"FAILURE (Status Code: {response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"ERROR: {e}")
            all_passed = False
            
    if all_passed:
        print("\nALL ADMIN ROUTES VERIFIED SUCCESSFULLY!")
    else:
        print("\nSOME ROUTES FAILED VERIFICATION.")

if __name__ == "__main__":
    verify_refactor()
