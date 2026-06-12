"""
Quick test script to verify scoreboard API endpoint
"""
import requests

try:
    # Test the scoreboard API endpoint
    response = requests.get('http://localhost:5000/api/scoreboard')
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Scoreboard API is working!")
        print(f"Total users: {data.get('total_users', 0)}")
        print(f"Page: {data.get('page', 1)} of {data.get('total_pages', 1)}")
        print(f"Users on this page: {len(data.get('users', []))}")
        
        if data.get('users'):
            print("\nTop 5 users:")
            for user in data['users'][:5]:
                current = " (YOU)" if user.get('is_current_user') else ""
                print(f"  #{user['rank']} - {user['username']}: {user['xp']} XP, {user['challenges_solved']} challenges{current}")
    else:
        print(f"❌ API returned status code: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Flask server. Is it running on http://localhost:5000?")
except Exception as e:
    print(f"❌ Error: {e}")
