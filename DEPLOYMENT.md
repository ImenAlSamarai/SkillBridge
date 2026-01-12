# SkillBridge - Deployment Guide

## Quick Start for Streamlit Cloud

### Prerequisites
- GitHub account
- Streamlit Cloud account (https://streamlit.io/cloud)
- LLM provider API key (Groq recommended for production)

### Step 1: Prepare Repository

1. **Create GitHub repository** (if not already done)
   ```bash
   git init
   git add .
   git commit -m "Initial commit - SkillBridge app"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/skillbridge.git
   git push -u origin main
   ```

2. **Verify .gitignore** is properly configured (already done)
   - Excludes `learnflow.db`, `*.db`, `.streamlit/secrets.toml`

### Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: https://streamlit.io/cloud
2. **Click "New app"**
3. **Configure deployment**:
   - Repository: `YOUR_USERNAME/skillbridge`
   - Branch: `main`
   - Main file path: `src/ui/app.py`
   - Python version: `3.11`

4. **Advanced Settings** (optional):
   - Custom subdomain: `skillbridge` → https://skillbridge.streamlit.app

### Step 3: Configure Secrets

In Streamlit Cloud dashboard, go to **Settings → Secrets** and paste:

```toml
[database]
type = "sqlite"
path = "database/learnflow.db"

[llm]
provider = "groq"
groq_api_key = "YOUR_GROQ_API_KEY"
model = "mixtral-8x7b-32768"

[app]
max_paths_per_user = 3
modules_per_topic = 8
```

**For PostgreSQL (production-ready)**:
```toml
[database]
type = "postgresql"
host = "your-db-host.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "your-password"

[llm]
provider = "groq"
groq_api_key = "YOUR_GROQ_API_KEY"
model = "mixtral-8x7b-32768"

[app]
max_paths_per_user = 3
modules_per_topic = 8
```

### Step 4: Deploy & Test

1. **Click "Deploy"** - Streamlit Cloud will install dependencies and start the app
2. **Monitor logs** for any errors
3. **Test critical flows**:
   - User signup
   - Path generation
   - Module completion
   - Multi-path creation
   - Logout/login persistence

---

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/skillbridge.git
cd skillbridge
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the secrets template:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your LLM provider credentials.

### 5. Initialize Database
```bash
mkdir -p database
```

The database will be automatically created on first run.

### 6. Run Application
```bash
streamlit run src/ui/app.py
```

Or use the provided run script:
```bash
./run.sh
```

---

## Database Migration (SQLite → PostgreSQL)

### Why PostgreSQL?
- SQLite is great for local development
- PostgreSQL is required for production (persistence, concurrency, scalability)

### Migration Steps

1. **Set up PostgreSQL instance**
   - Option A: Streamlit Cloud built-in PostgreSQL
   - Option B: Supabase (recommended): https://supabase.com
   - Option C: Railway: https://railway.app

2. **Update database.py** to support PostgreSQL
   ```python
   # Check st.secrets for database type
   if st.secrets.get("database", {}).get("type") == "postgresql":
       # Use psycopg2 connection
   else:
       # Use SQLite connection
   ```

3. **Export existing data** (if any):
   ```bash
   sqlite3 database/learnflow.db .dump > backup.sql
   ```

4. **Create PostgreSQL schema**
   ```bash
   psql -h your-host -U your-user -d your-db -f backup.sql
   ```

---

## Configuration Files

### Agent Prompts
- `/config/prompts/agent1_prompts.yaml` - Job Parser prompts
- `/config/prompts/agent2_prompts.yaml` - Topic Assessor prompts
- `/config/prompts/agent3_prompts.yaml` - Content Generator prompts

### LLM Settings
- `/config/llm.yaml` - Model settings, temperature, max tokens

### Golden Resources
- `/config/golden_resources_by_role.yaml` - Role-specific learning resources

---

## Environment Variables

The app uses Streamlit secrets (`.streamlit/secrets.toml`) for configuration.

**Required secrets**:
- `llm.provider` - LLM provider: "groq", "ollama", or "openai"
- `llm.[provider]_api_key` - API key for chosen provider
- `llm.model` - Model name

**Optional secrets**:
- `database.type` - "sqlite" (default) or "postgresql"
- `database.host` - PostgreSQL host (if using PostgreSQL)
- `database.port` - PostgreSQL port (default: 5432)
- `database.user` - PostgreSQL user
- `database.password` - PostgreSQL password
- `app.max_paths_per_user` - Max paths per user (default: 3)
- `app.modules_per_topic` - Modules per topic (default: 8)

---

## LLM Provider Setup

### Groq (Recommended for Production)
1. Sign up at https://console.groq.com
2. Create API key
3. Add to secrets: `groq_api_key = "gsk_..."`
4. Set model: `model = "mixtral-8x7b-32768"`

**Advantages**: Fast inference, generous free tier, production-ready

### Ollama (Local Development)
1. Install Ollama: https://ollama.ai
2. Pull model: `ollama pull llama3.2`
3. Start server: `ollama serve`
4. Add to secrets: `provider = "ollama"`, `model = "llama3.2"`

**Advantages**: Free, private, no API keys needed

### OpenAI
1. Sign up at https://platform.openai.com
2. Create API key
3. Add to secrets: `openai_api_key = "sk-..."`
4. Set model: `model = "gpt-4o-mini"`

**Advantages**: High quality, well-tested

---

## Monitoring & Logging

### Streamlit Cloud Logs
- Access logs via Streamlit Cloud dashboard → Logs tab
- Monitor for errors, performance issues

### Key Metrics to Track
- User signups
- Paths created
- Modules completed
- Average session time
- Error rates

### Error Tracking
- Check logs daily (first week)
- Look for patterns in errors
- Monitor API rate limits

---

## Security Checklist

- [x] Secrets not committed to version control
- [x] `.gitignore` excludes sensitive files
- [x] Input validation for all user inputs
- [x] Parameterized SQL queries (no SQL injection)
- [ ] Consider upgrading password hashing (SHA256 → bcrypt)
- [ ] Add rate limiting for API calls
- [ ] Review CORS settings if using external APIs

---

## Performance Optimization

### Current Settings
- Content generation timeout: ~30s per module
- Modules per topic: 8
- Max paths per user: 3

### Optimization Tips
1. **Cache generated content** (already implemented)
2. **Use faster LLM models** for better UX
3. **Implement rate limiting** to prevent API overuse
4. **Monitor database size** and add pagination if needed

---

## Troubleshooting

### App won't start
- Check Streamlit Cloud logs for import errors
- Verify all dependencies in requirements.txt
- Ensure Python version is 3.11

### Database errors
- SQLite: Check `database/` directory exists
- PostgreSQL: Verify connection credentials in secrets
- Check database schema is up-to-date

### LLM errors
- Verify API key is correct in secrets
- Check API rate limits
- Ensure model name is correct
- Test API connection separately

### Module generation fails
- Check LLM provider status
- Verify API key has sufficient credits
- Review error logs for specific issues
- Check network connectivity

---

## Rollback Plan

If critical issues occur:

1. **Pause new signups** - Add maintenance message
2. **Notify beta testers** - Send status update
3. **Rollback to previous version**:
   ```bash
   git revert HEAD
   git push
   ```
4. **Fix issue locally**
5. **Test thoroughly**
6. **Redeploy with fix**
7. **Resume beta testing**

---

## Support & Feedback

### For Beta Testers
- Report issues via [GitHub Issues](https://github.com/YOUR_USERNAME/skillbridge/issues)
- Share feedback via [feedback form/email]
- Join [Discord/Slack community]

### For Developers
- Documentation: `/docs`
- Tests: `/tests`
- Configuration: `/config`

---

## Next Steps After Deployment

1. **Invite 2-3 initial beta testers**
2. **Monitor closely for first week**
3. **Collect feedback systematically**
4. **Fix critical bugs immediately**
5. **Gradual rollout to more users**
6. **Iterate based on feedback**

---

## Project Structure

```
skillbridge/
├── src/
│   ├── ui/
│   │   └── app.py              # Main Streamlit app
│   ├── core/
│   │   ├── database.py         # Database operations
│   │   ├── llm_engine.py       # LLM interface
│   │   └── config_loader.py    # Configuration loader
│   ├── agents/
│   │   ├── job_parser.py       # Agent 1: Job/skill parser
│   │   ├── topic_assessor.py   # Agent 2: Topic assessor
│   │   └── content_generator.py # Agent 3: Content generator
│   └── workflow/
│       └── orchestrator.py     # LangGraph workflow
├── config/
│   ├── prompts/                # Agent prompts
│   ├── llm.yaml               # LLM settings
│   └── golden_resources_by_role.yaml
├── tests/                      # Test files
├── docs/                       # Documentation
├── .streamlit/
│   └── secrets.toml.example   # Secrets template
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
└── DEPLOYMENT.md              # This file
```

---

**Ready to deploy!** Follow the Quick Start guide above to get your app live.
