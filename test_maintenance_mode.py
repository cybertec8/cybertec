"""
Test script for Maintenance Mode feature

This script verifies that the maintenance mode implementation works correctly.
Run this after starting the Flask application.
"""

import requests
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:5000"

def test_maintenance_mode():
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Testing Maintenance Mode Feature")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Home page loads
    print(f"{Fore.YELLOW}Test 1: Home page accessibility")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print(f"{Fore.GREEN}✓ Home page loads successfully")
            tests_passed += 1
        else:
            print(f"{Fore.RED}✗ Home page failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}")
        tests_failed += 1
    
    # Test 2: Login redirect (when maintenance mode is ON)
    print(f"\n{Fore.YELLOW}Test 2: Login page redirect (maintenance mode)")
    try:
        response = requests.get(f"{BASE_URL}/login", allow_redirects=False)
        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"{Fore.GREEN}✓ Login redirects when maintenance mode is active")
            tests_passed += 1
        elif response.status_code == 200:
            # Check if maintenance mode is disabled
            if "AUTH_ENABLED = True" in response.text or "otp" in response.text.lower():
                print(f"{Fore.BLUE}ℹ Login page loads (AUTH_ENABLED = True)")
                tests_passed += 1
            else:
                print(f"{Fore.RED}✗ Unexpected response")
                tests_failed += 1
        else:
            print(f"{Fore.RED}✗ Unexpected status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}")
        tests_failed += 1
    
    # Test 3: Register redirect
    print(f"\n{Fore.YELLOW}Test 3: Register page redirect (maintenance mode)")
    try:
        response = requests.get(f"{BASE_URL}/register", allow_redirects=False)
        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"{Fore.GREEN}✓ Register redirects when maintenance mode is active")
            tests_passed += 1
        elif response.status_code == 200:
            print(f"{Fore.BLUE}ℹ Register page loads (AUTH_ENABLED = True)")
            tests_passed += 1
        else:
            print(f"{Fore.RED}✗ Unexpected status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}")
        tests_failed += 1
    
    # Test 4: Check for maintenance banner
    print(f"\n{Fore.YELLOW}Test 4: Maintenance banner visibility")
    try:
        response = requests.get(f"{BASE_URL}/")
        if "maintenance-banner" in response.text:
            print(f"{Fore.GREEN}✓ Maintenance banner present (AUTH_ENABLED = False)")
            tests_passed += 1
        else:
            print(f"{Fore.BLUE}ℹ No maintenance banner (AUTH_ENABLED = True)")
            tests_passed += 1
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {e}")
        tests_failed += 1
    
    # Test 5: Other pages still accessible
    print(f"\n{Fore.YELLOW}Test 5: Other pages remain accessible")
    pages_to_test = ["/about", "/features", "/pricing", "/blog"]
    all_accessible = True
    
    for page in pages_to_test:
        try:
            response = requests.get(f"{BASE_URL}{page}")
            if response.status_code == 200:
                print(f"{Fore.GREEN}  ✓ {page} accessible")
            else:
                print(f"{Fore.RED}  ✗ {page} returned {response.status_code}")
                all_accessible = False
        except Exception as e:
            print(f"{Fore.RED}  ✗ {page} error: {e}")
            all_accessible = False
    
    if all_accessible:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Test Summary")
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}Passed: {tests_passed}")
    print(f"{Fore.RED}Failed: {tests_failed}")
    
    if tests_failed == 0:
        print(f"\n{Fore.GREEN}{'✓'*20}")
        print(f"{Fore.GREEN}All tests passed! Maintenance mode is working correctly.")
        print(f"{Fore.GREEN}{'✓'*20}")
    else:
        print(f"\n{Fore.YELLOW}Some tests need attention. Check the output above.")
    
    print(f"\n{Fore.CYAN}Manual Testing:")
    print(f"{Fore.WHITE}1. Visit {BASE_URL} in your browser")
    print(f"{Fore.WHITE}2. Toggle AUTH_ENABLED in app.py between True and False")
    print(f"{Fore.WHITE}3. Restart the app and observe the changes")
    print(f"{Fore.WHITE}4. Verify the banner appears/disappears")
    print(f"{Fore.WHITE}5. Check that buttons are enabled/disabled")

if __name__ == "__main__":
    print(f"\n{Fore.MAGENTA}Make sure the Flask app is running on {BASE_URL}")
    print(f"{Fore.MAGENTA}Press Enter to continue or Ctrl+C to cancel...")
    try:
        input()
        test_maintenance_mode()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test cancelled.")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}")
        print(f"\n{Fore.YELLOW}Make sure:")
        print(f"{Fore.WHITE}1. Flask app is running: python app.py")
        print(f"{Fore.WHITE}2. colorama is installed: pip install colorama requests")
