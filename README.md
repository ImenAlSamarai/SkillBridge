# learn_flow - AI Interview Prep

Phase 1: Database layer + Streamlit onboarding form for quant/ML interview preparation.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python database.py

# 3. Populate test users (optional)
python scripts/populate_test_data.py --all

# 4. Launch app
streamlit run app.py
```

Visit: http://localhost:8501

## Project Structure

```
learn_flow/
├── app.py                      # Streamlit onboarding form
├── database.py                 # SQLite CRUD operations
├── config.py                   # YAML config loader
├── requirements.txt            # Python dependencies
├── config/
│   ├── fields.yaml            # Dropdown options
│   ├── admin_users.yaml       # Admin email list
│   └── golden_sources.yaml    # Reference books
├── scripts/
│   ├── populate_test_data.py  # Load 5 test users
│   └── admin.py               # User management CLI
├── tests/
│   └── test_users.json        # Test user profiles
└── learnflow.db               # SQLite database
```

## Database Schema

- **users**: Authentication and profile
- **paths**: Career progression goals (current → target role)
- **user_skills**: Topic mastery tracking

## Admin Commands

```bash
# List all users
python scripts/admin.py list_users

# Delete user by ID
python scripts/admin.py delete_user <user_id>
```

## Testing

### Automated Tests

```bash
# Test 1: Database operations
python database.py

# Test 2: Populate test data
python scripts/populate_test_data.py --all

# Test 3: List users
python scripts/admin.py list_users

# Test 4: Verify database
sqlite3 learnflow.db "SELECT COUNT(*) FROM users;"
sqlite3 learnflow.db "SELECT COUNT(*) FROM paths;"
```

### Frontend Test

```bash
# Launch Streamlit app
streamlit run app.py

# 1. Verify blue theme (#10B981)
# 2. Fill form with test data
# 3. Submit and check success message
# 4. Verify in database:
sqlite3 learnflow.db "SELECT * FROM paths ORDER BY created_at DESC LIMIT 1;"
```

## Phase 1 Scope

✅ **Complete**:
- SQLite database with 3 tables
- Streamlit 2-column onboarding form (12 fields)
- User authentication (SHA256 hashing)
- Admin CLI tools
- Test data utilities

⏳ **Future (Phase 2)**:
- LLM integration for personalized learning
- Module generation and progress tracking
- Interview practice scenarios

## Tech Stack

- **Backend**: Python 3.x + SQLite
- **Frontend**: Streamlit
- **Config**: YAML
- **Auth**: SHA256 (Phase 1 only - upgrade for production)

## Development Notes

- **Code Budget**: 806 lines (exceeded 500-line target for complete functionality)
- **Dependencies**: Minimal (streamlit + pyyaml)
- **Database**: Foreign key CASCADE for data integrity
- **Security**: Parameterized queries, email normalization
