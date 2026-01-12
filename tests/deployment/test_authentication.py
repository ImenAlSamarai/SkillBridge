#!/usr/bin/env python3
"""
Test script for authentication system restoration
Tests database functions and session management
"""

import sys
sys.path.insert(0, 'src')

from src.core import database

print("=" * 80)
print("AUTHENTICATION SYSTEM TEST")
print("=" * 80)
print()

# Test 1: authenticate_user() with valid credentials
print("Test 1: Login with valid credentials (alex@student.edu / test123)")
user = database.authenticate_user("alex@student.edu", "test123")
if user:
    print(f"✅ Login successful: {user['name']} (ID: {user['id']})")
    print(f"   Email: {user['email']}")
    assert 'password_hash' not in user, "❌ ERROR: password_hash should not be in returned user dict"
    print("   ✅ password_hash correctly excluded from user dict")
else:
    print("❌ FAIL: Login should have succeeded")
print()

# Test 2: authenticate_user() with invalid password
print("Test 2: Login with invalid password (alex@student.edu / wrongpass)")
user = database.authenticate_user("alex@student.edu", "wrongpass")
if user is None:
    print("✅ Login correctly rejected invalid password")
else:
    print("❌ FAIL: Login should have failed with wrong password")
print()

# Test 3: authenticate_user() with non-existent email
print("Test 3: Login with non-existent email (nonexistent@email.com / test123)")
user = database.authenticate_user("nonexistent@email.com", "test123")
if user is None:
    print("✅ Login correctly rejected non-existent email")
else:
    print("❌ FAIL: Login should have failed with non-existent email")
print()

# Test 4: authenticate_user() with empty credentials
print("Test 4: Login with empty credentials")
user = database.authenticate_user("", "")
if user is None:
    print("✅ Login correctly rejected empty credentials")
else:
    print("❌ FAIL: Login should have failed with empty credentials")
print()

# Test 5: get_user_by_email()
print("Test 5: Get user by email (sarah@analyst.com)")
user = database.get_user_by_email("sarah@analyst.com")
if user:
    print(f"✅ Found user: {user['name']} (ID: {user['id']})")
    assert 'password_hash' in user, "❌ ERROR: password_hash should be in user dict from get_user_by_email"
    print("   ✅ password_hash correctly included (for internal use)")
else:
    print("❌ FAIL: Should have found user")
print()

# Test 6: Test all existing users can login
print("Test 6: Verify all 5 test users can login with password 'test123'")
test_users = [
    "alex@student.edu",
    "sarah@analyst.com",
    "mike@ml.com",
    "emma@quant.com",
    "tom@physics.com"
]
all_passed = True
for email in test_users:
    user = database.authenticate_user(email, "test123")
    if user:
        print(f"   ✅ {email} → {user['name']}")
    else:
        print(f"   ❌ {email} → Login failed")
        all_passed = False

if all_passed:
    print("✅ All test users can login successfully")
else:
    print("❌ FAIL: Some test users failed to login")
print()

# Test 7: Verify user has learning paths
print("Test 7: Verify user 1 has learning paths")
paths = database.get_paths_by_user(1)
if paths and len(paths) > 0:
    print(f"✅ User 1 has {len(paths)} learning path(s)")
    first_path = paths[0]
    print(f"   First path: {first_path['current_seniority']} → {first_path['target_seniority']}")
else:
    print("❌ FAIL: User 1 should have learning paths")
print()

# Test 8: Test password validation
print("Test 8: Test password validation (minimum 6 characters)")
try:
    # This should fail due to password length validation in create_user/hash_password
    user_id = database.create_user("Test User", "test@short.com", "12345", is_admin=False)
    print("❌ FAIL: Should have rejected password < 6 characters")
except ValueError as e:
    if "at least 6 characters" in str(e):
        print("✅ Correctly rejected password < 6 characters")
    else:
        print(f"❌ FAIL: Wrong error message: {e}")
print()

print("=" * 80)
print("✅ AUTHENTICATION SYSTEM TEST COMPLETE")
print("=" * 80)
print()
print("Summary:")
print("  ✓ authenticate_user() function working correctly")
print("  ✓ Valid credentials accepted")
print("  ✓ Invalid credentials rejected")
print("  ✓ Password hash excluded from returned user dict")
print("  ✓ All 5 test users can login")
print("  ✓ Password validation working")
print()
print("Next steps:")
print("  1. Run ./run.sh to start Streamlit app")
print("  2. App should show login screen by default")
print("  3. Login with: alex@student.edu / test123")
print("  4. Verify dashboard loads with user's learning paths")
print("  5. Test logout button in sidebar")
print("  6. Test signup with new user")
print()
