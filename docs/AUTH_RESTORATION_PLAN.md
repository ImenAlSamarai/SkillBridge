# User Authentication Restoration Plan

**Date**: 2026-01-11
**Status**: 📋 IMPLEMENTATION PLAN
**Estimated Effort**: 3-4 hours
**Risk Level**: LOW (Additive changes only)

---

## Executive Summary

This document outlines the step-by-step plan to restore the Phase 1 user authentication system that was removed to focus on core platform features. The authentication infrastructure remains intact in the database and utility functions - we only need to add the UI layer and session management.

---

## Current State Analysis

### ✅ What Already Exists

**1. Database Schema (COMPLETE)**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**2. Database Functions (src/core/database.py)**
```python
✅ hash_password(password: str) -> str
✅ create_user(name, email, password, is_admin) -> int
✅ get_user(user_id) -> Optional[Dict]
✅ get_user_by_email(email) -> Optional[Dict]
✅ list_all_users() -> List[Dict]
✅ delete_user(user_id) -> bool
```

**3. Test Users in Database**
```
ID | Name          | Email                  | Admin
1  | Alex Student  | alex@student.edu       | No
2  | Sarah Analyst | sarah@analyst.com      | No
3  | Mike ML       | mike@ml.com            | No
4  | Emma Quant    | emma@quant.com         | No
5  | Tom Physics   | tom@physics.edu        | No
```

**4. Admin Tools**
```bash
✅ scripts/admin.py list_users
✅ scripts/admin.py delete_user <user_id>
✅ scripts/populate_test_data.py --all
```

**5. Configuration**
```yaml
✅ config/admin_users.yaml - Admin email whitelist
✅ config/fields.yaml - Form field options
```

### ❌ What's Missing

**1. Authentication Function**
```python
❌ authenticate_user(email, password) -> Optional[Dict]  # NEED TO ADD
```

**2. UI Screens**
```python
❌ screen_0_login() - Login/Signup screen  # NEED TO ADD
```

**3. Session Management**
```python
❌ st.session_state.current_user - User session  # NEED TO ADD
❌ st.session_state.authenticated - Auth flag   # NEED TO ADD
```

**4. Hardcoded User ID (6 locations in app.py)**
```python
❌ Line 187: run_full_workflow(user_id=1, form_data=form_data)
❌ Line 216: user_id = 1  # Hardcoded for MVP
❌ Line 366: user_id = 1  # Hardcoded for MVP
❌ Line 382: user_id = 1  # Hardcoded for MVP
❌ Line 722: user_id = 1  # Hardcoded for MVP
❌ Line 738: user_id = 1  # Hardcoded for MVP
```

---

## Implementation Plan

### Phase 1: Add Missing Database Function (15 minutes)

**File**: `src/core/database.py`

**Add after `get_user_by_email()` function (after line 179)**:

```python
def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user by email and password

    Args:
        email: User email address
        password: Plain text password

    Returns:
        User dict if authentication successful, None otherwise
    """
    if not email or not password:
        return None

    # Get user by email
    user = get_user_by_email(email)
    if not user:
        return None

    # Verify password
    password_hash = hash_password(password)
    if user['password_hash'] != password_hash:
        return None

    # Authentication successful - return user (without password hash)
    user_copy = dict(user)
    del user_copy['password_hash']  # Don't expose password hash
    return user_copy
```

**Testing**:
```python
# Test script
user = authenticate_user("alex@student.edu", "password123")
assert user is not None
assert user['name'] == "Alex Student"
assert 'password_hash' not in user  # Verify hash not exposed
```

---

### Phase 2: Add Session Management Helpers (20 minutes)

**File**: `src/ui/app.py`

**Add after imports section (after line 19)**:

```python
# ============================================================
# SESSION MANAGEMENT
# ============================================================

def init_session_state():
    """Initialize session state variables for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'path_data' not in st.session_state:
        st.session_state.path_data = None
    if 'selected_topic_id' not in st.session_state:
        st.session_state.selected_topic_id = None
    if 'module_cache' not in st.session_state:
        st.session_state.module_cache = {}
    if 'module_names_cache' not in st.session_state:
        st.session_state.module_names_cache = {}


def get_current_user_id() -> int:
    """Get current authenticated user's ID"""
    if st.session_state.authenticated and st.session_state.current_user:
        return st.session_state.current_user['id']
    return 1  # Fallback to user 1 if not authenticated (backward compatibility)


def logout():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.path_data = None
    st.query_params["screen"] = "login"
    st.rerun()
```

**Update existing session initialization (around line 92)**:

Replace:
```python
# Initialize session state
if 'path_data' not in st.session_state:
    st.session_state.path_data = None
# ... etc
```

With:
```python
# Initialize session state
init_session_state()
```

---

### Phase 3: Add Login/Signup Screen (60 minutes)

**File**: `src/ui/app.py`

**Add new function after `init_session_state()` section**:

```python
def screen_0_login():
    """Screen 0: Login/Signup Screen"""
    st.title(":material/rocket_launch: Welcome to SkillBridge")

    st.markdown("""
    **SkillBridge** transforms your current role into a personalized career path to any target job—
    extracting skill gaps, adapting content to your level, and preparing you for success.
    """)

    st.markdown("---")

    # Toggle between Login and Signup
    tab1, tab2 = st.tabs(["🔑 Login", "✍️ Sign Up"])

    # ============================================================
    # LOGIN TAB
    # ============================================================
    with tab1:
        st.subheader("Login to Your Account")

        with st.form("login_form"):
            login_email = st.text_input(
                "Email",
                placeholder="your.email@example.com",
                key="login_email_input"
            )
            login_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password_input"
            )

            login_submit = st.form_submit_button(
                "🔐 Login",
                type="primary",
                use_container_width=True
            )

            if login_submit:
                if not login_email or not login_password:
                    st.error("❌ Please enter both email and password")
                else:
                    # Authenticate user
                    user = database.authenticate_user(login_email, login_password)

                    if user:
                        # Login successful
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.success(f"✅ Welcome back, {user['name']}!")
                        st.query_params["screen"] = "form"
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password")

    # ============================================================
    # SIGNUP TAB
    # ============================================================
    with tab2:
        st.subheader("Create Your Account")

        with st.form("signup_form"):
            signup_name = st.text_input(
                "Full Name",
                placeholder="John Doe",
                key="signup_name_input"
            )
            signup_email = st.text_input(
                "Email",
                placeholder="your.email@example.com",
                key="signup_email_input"
            )
            signup_password = st.text_input(
                "Password",
                type="password",
                placeholder="Minimum 6 characters",
                key="signup_password_input"
            )
            signup_password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                key="signup_password_confirm_input"
            )

            signup_submit = st.form_submit_button(
                "✍️ Create Account",
                type="primary",
                use_container_width=True
            )

            if signup_submit:
                # Validation
                if not signup_name or not signup_email or not signup_password:
                    st.error("❌ Please fill in all fields")
                elif signup_password != signup_password_confirm:
                    st.error("❌ Passwords do not match")
                elif len(signup_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    try:
                        # Create user
                        user_id = database.create_user(
                            name=signup_name,
                            email=signup_email,
                            password=signup_password,
                            is_admin=False
                        )

                        # Auto-login after signup
                        user = database.get_user(user_id)
                        if user:
                            user_copy = dict(user)
                            del user_copy['password_hash']  # Don't expose hash
                            st.session_state.authenticated = True
                            st.session_state.current_user = user_copy
                            st.success(f"✅ Account created! Welcome, {signup_name}!")
                            st.query_params["screen"] = "form"
                            st.rerun()
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("❌ Email already registered. Please login instead.")
                        else:
                            st.error(f"❌ Error creating account: {str(e)}")

    # ============================================================
    # DEMO MODE
    # ============================================================
    st.markdown("---")
    st.info("💡 **Demo Mode**: Click below to continue without login (uses test user)")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Continue as Guest", use_container_width=True, type="secondary"):
            # Use test user (ID 1)
            user = database.get_user(1)
            if user:
                user_copy = dict(user)
                del user_copy['password_hash']
                st.session_state.authenticated = True
                st.session_state.current_user = user_copy
                st.query_params["screen"] = "form"
                st.rerun()
```

---

### Phase 4: Add Logout Button to Sidebar (15 minutes)

**File**: `src/ui/app.py`

**Update all sidebar sections** to include user info and logout button at the top:

**In `screen_2_new()` function sidebar (around line 402)**:

```python
with st.sidebar:
    # User info section (NEW)
    if st.session_state.authenticated and st.session_state.current_user:
        st.markdown(f"### 👤 {st.session_state.current_user['name']}")
        st.caption(st.session_state.current_user['email'])
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            logout()
        st.markdown("---")

    st.markdown("### :material/rocket_launch: SkillBridge")
    st.markdown("---")

    # ... rest of sidebar code
```

**Repeat for all other screen functions**:
- `screen_2_graph()` (around line 257)
- `screen_3_topics()` (around line 791)

---

### Phase 5: Replace Hardcoded User IDs (30 minutes)

**File**: `src/ui/app.py`

**Replace all 6 occurrences of `user_id = 1`**:

**1. Line 187 in `screen_1_form()`**:
```python
# Before:
result = run_full_workflow(user_id=1, form_data=form_data)

# After:
result = run_full_workflow(user_id=get_current_user_id(), form_data=form_data)
```

**2. Line 216 in `screen_2_graph()`**:
```python
# Before:
user_id = 1  # Hardcoded for MVP

# After:
user_id = get_current_user_id()
```

**3. Lines 366, 382 in `screen_2_new()`**:
```python
# Before:
user_id = 1  # Hardcoded for MVP

# After:
user_id = get_current_user_id()
```

**4. Lines 722, 738 in `screen_3_topics()`**:
```python
# Before:
user_id = 1  # Hardcoded for MVP

# After:
user_id = get_current_user_id()
```

---

### Phase 6: Update Screen Routing (15 minutes)

**File**: `src/ui/app.py`

**Update the routing logic at the bottom of the file (around line 1137)**:

```python
# Route to appropriate screen
if screen == "login" or not st.session_state.authenticated:
    # Force login screen if not authenticated
    screen_0_login()
elif screen == "form":
    screen_1_form()
elif screen == "graph":
    screen_2_graph()
elif screen == "graph_new":
    screen_2_new()
elif screen == "topics":
    screen_3_topics()
else:
    # Default to login if not authenticated, form if authenticated
    if st.session_state.authenticated:
        st.query_params["screen"] = "form"
    else:
        st.query_params["screen"] = "login"
    st.rerun()
```

---

### Phase 7: Add Authentication Bypass Toggle (10 minutes)

**File**: `src/ui/app.py`

**Add environment variable check at top of routing section**:

```python
import os

# Development mode - bypass authentication
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

if DEV_MODE and not st.session_state.authenticated:
    # Auto-login with test user in dev mode
    user = database.get_user(1)
    if user:
        user_copy = dict(user)
        del user_copy['password_hash']
        st.session_state.authenticated = True
        st.session_state.current_user = user_copy

# Route to appropriate screen
# ... (rest of routing code)
```

**Update `.env` file**:
```bash
# Development mode - bypasses login (set to false in production)
DEV_MODE=true
```

---

## Testing Checklist

### Unit Tests

```bash
# Test authentication function
python << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.core import database

# Test 1: Successful authentication
user = database.authenticate_user("alex@student.edu", "password123")
assert user is not None, "Authentication failed"
assert user['name'] == "Alex Student", "Wrong user returned"
assert 'password_hash' not in user, "Password hash exposed"
print("✅ Test 1: Successful authentication")

# Test 2: Wrong password
user = database.authenticate_user("alex@student.edu", "wrongpassword")
assert user is None, "Authentication should fail with wrong password"
print("✅ Test 2: Wrong password rejected")

# Test 3: Non-existent email
user = database.authenticate_user("nonexistent@test.com", "password123")
assert user is None, "Authentication should fail with non-existent email"
print("✅ Test 3: Non-existent email rejected")

# Test 4: Empty credentials
user = database.authenticate_user("", "")
assert user is None, "Authentication should fail with empty credentials"
print("✅ Test 4: Empty credentials rejected")

print("\n✅ All authentication tests passed!")
EOF
```

### Integration Tests

```bash
# Test 1: App launches with login screen
DEV_MODE=false ./run.sh
# Expected: Shows login/signup screen

# Test 2: Login with test user
# Email: alex@student.edu
# Password: password123
# Expected: Redirects to form screen

# Test 3: Create new account
# Name: Test User
# Email: test@example.com
# Password: test123
# Expected: Account created, auto-logged in

# Test 4: Logout
# Click logout button
# Expected: Returns to login screen

# Test 5: Dev mode bypass
DEV_MODE=true ./run.sh
# Expected: Auto-logged in as Alex Student
```

### User Flow Tests

1. **New User Signup Flow**:
   - [ ] Visit login screen
   - [ ] Click "Sign Up" tab
   - [ ] Fill in name, email, password
   - [ ] Submit form
   - [ ] Verify account created
   - [ ] Verify auto-logged in
   - [ ] Verify redirected to form screen

2. **Returning User Login Flow**:
   - [ ] Visit login screen
   - [ ] Enter email and password
   - [ ] Click "Login"
   - [ ] Verify logged in
   - [ ] Verify user name shown in sidebar
   - [ ] Create a learning path
   - [ ] Navigate to dashboard
   - [ ] Verify path belongs to logged-in user

3. **Guest Mode Flow**:
   - [ ] Visit login screen
   - [ ] Click "Continue as Guest"
   - [ ] Verify logged in as Alex Student
   - [ ] Create learning path
   - [ ] Verify functionality works

4. **Logout Flow**:
   - [ ] Login as any user
   - [ ] Navigate to any screen
   - [ ] Click "Logout" in sidebar
   - [ ] Verify returned to login screen
   - [ ] Verify session cleared

5. **Multi-User Flow**:
   - [ ] Login as User A
   - [ ] Create learning path
   - [ ] Logout
   - [ ] Login as User B
   - [ ] Verify User B doesn't see User A's path
   - [ ] Create different learning path
   - [ ] Logout
   - [ ] Login as User A again
   - [ ] Verify User A's path still exists

---

## Backward Compatibility

### Development Mode (DEV_MODE=true)
- Auto-logs in as test user (ID 1)
- No login screen shown
- Exactly like current behavior
- **Use during development to skip login**

### Production Mode (DEV_MODE=false)
- Login screen required
- Multi-user support enabled
- Proper authentication
- **Use for beta testing and production**

### Fallback Behavior
```python
def get_current_user_id() -> int:
    """Get current authenticated user's ID"""
    if st.session_state.authenticated and st.session_state.current_user:
        return st.session_state.current_user['id']
    return 1  # Fallback to user 1 if not authenticated
```

This ensures:
- If auth system fails, app still works with user ID 1
- No breaking changes to existing functionality
- Graceful degradation

---

## Security Considerations

### Current (Phase 1) Security
- ✅ SHA256 password hashing
- ✅ Email validation
- ✅ Password minimum length (6 chars)
- ✅ SQL injection prevention (parameterized queries)
- ✅ Password hash not exposed in API responses

### Future Improvements (Phase 2+)
- 🔄 Upgrade to bcrypt password hashing
- 🔄 Add password strength requirements
- 🔄 Add session timeouts
- 🔄 Add rate limiting for login attempts
- 🔄 Add email verification
- 🔄 Add password reset functionality
- 🔄 Add 2FA support

### Notes
- Current SHA256 is **acceptable for beta/MVP**
- README already notes: "Auth: SHA256 (Phase 1 only - upgrade for production)"
- Upgrade to bcrypt before public launch

---

## Database Migration

### No Migration Needed! ✅

The `users` table already exists with all required fields:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

Foreign key constraints already in place:
```sql
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

All 5 test users already exist in database.

---

## File Changes Summary

### Files to Modify

**1. src/core/database.py**
- Add `authenticate_user()` function (15 lines)
- Location: After `get_user_by_email()` function

**2. src/ui/app.py**
- Add `init_session_state()` helper (20 lines)
- Add `get_current_user_id()` helper (5 lines)
- Add `logout()` helper (8 lines)
- Add `screen_0_login()` function (150 lines)
- Update `screen_2_graph()` sidebar (10 lines)
- Update `screen_2_new()` sidebar (10 lines)
- Update `screen_3_topics()` sidebar (10 lines)
- Replace 6 hardcoded `user_id = 1` lines
- Update routing logic (15 lines)
- Add DEV_MODE bypass (10 lines)

**3. .env**
- Add `DEV_MODE=true` line (1 line)

### Files to Create

**4. tests/test_authentication.py** (NEW)
- Unit tests for `authenticate_user()`
- Integration tests for login/signup flow

### Total Changes
- Lines added: ~250
- Lines modified: ~50
- Files created: 1
- Files modified: 3

---

## Implementation Order

### Recommended Sequence

1. **Step 1**: Add `authenticate_user()` to database.py
   - Test immediately with unit test
   - Verify no breaking changes

2. **Step 2**: Add session management helpers to app.py
   - `init_session_state()`
   - `get_current_user_id()`
   - `logout()`

3. **Step 3**: Add DEV_MODE bypass
   - Update .env
   - Add bypass logic
   - Test app still works in dev mode

4. **Step 4**: Replace hardcoded user IDs
   - Use `get_current_user_id()` everywhere
   - Test app still works (uses fallback)

5. **Step 5**: Add `screen_0_login()` function
   - Test login functionality
   - Test signup functionality

6. **Step 6**: Update routing logic
   - Add login screen routing
   - Test authentication flow

7. **Step 7**: Add sidebar user info
   - Add to all screen functions
   - Test logout functionality

8. **Step 8**: Comprehensive testing
   - All user flows
   - Multi-user scenarios
   - Dev mode vs production mode

---

## Rollback Plan

If issues occur, rollback is simple:

```bash
# Set DEV_MODE=true to bypass authentication
echo "DEV_MODE=true" >> .env

# Or revert to hardcoded user_id = 1
# Replace get_current_user_id() with 1
```

The app will continue working with user ID 1 as before.

---

## Success Criteria

### Must Have ✅
- [ ] Users can sign up with email/password
- [ ] Users can login with credentials
- [ ] Users can logout
- [ ] Each user sees only their own learning paths
- [ ] Guest mode works (bypass login)
- [ ] DEV_MODE bypasses authentication
- [ ] All existing tests pass
- [ ] No breaking changes to existing functionality

### Nice to Have 🎁
- [ ] Remember me functionality
- [ ] Password reset
- [ ] Email verification
- [ ] Profile editing
- [ ] Admin panel for user management

---

## Post-Implementation Tasks

1. **Documentation Updates**:
   - Update README.md with new login instructions
   - Update QUICK_START.md with authentication steps
   - Document DEV_MODE usage

2. **Test Data**:
   - Verify all 5 test users can login
   - Create test script for common scenarios

3. **Configuration**:
   - Update .env.example with DEV_MODE
   - Document environment variables

4. **Monitoring**:
   - Add logging for authentication attempts
   - Track failed login attempts
   - Monitor user creation

---

## Questions for User

Before implementation, please confirm:

1. **Development Mode**: Do you want DEV_MODE=true by default for easier development?
2. **Guest Mode**: Should "Continue as Guest" be available in production, or dev only?
3. **Admin Users**: Should we implement admin user features from config/admin_users.yaml?
4. **Password Reset**: Is password reset functionality needed for MVP, or can we defer?
5. **Email Verification**: Required for MVP or can we add later?

---

## Estimated Timeline

- **Phase 1**: Add authenticate_user() - 15 min
- **Phase 2**: Add session helpers - 20 min
- **Phase 3**: Add login screen - 60 min
- **Phase 4**: Add logout buttons - 15 min
- **Phase 5**: Replace hardcoded IDs - 30 min
- **Phase 6**: Update routing - 15 min
- **Phase 7**: Add DEV_MODE bypass - 10 min
- **Testing**: Comprehensive tests - 60 min
- **Documentation**: Update docs - 30 min

**Total**: ~3.5-4 hours

---

## Risk Assessment

**Risk Level**: LOW

**Reasons**:
- Database schema already exists ✅
- All CRUD functions already exist ✅
- Changes are additive (not modifying existing code) ✅
- DEV_MODE provides fallback ✅
- `get_current_user_id()` has fallback to user 1 ✅
- Test users already in database ✅

**Mitigation**:
- Implement in sequence with testing at each step
- Keep DEV_MODE enabled during development
- Test with multiple users before disabling dev mode
- Have rollback plan ready

---

**Status**: 📋 READY FOR IMPLEMENTATION
**Approval Needed**: YES
**Breaking Changes**: NONE
**Backward Compatible**: YES

---

*Generated: 2026-01-11*
*Estimated Implementation Time: 3-4 hours*
