# Beta Deployment Plan - SkillBridge

## Current Status
- ✅ Core functionality complete (multi-path learning, mastery tracking, content generation)
- ✅ Authentication system working
- ✅ All major bugs fixed (mastery consistency, module navigation, dashboard updates)
- ✅ UI polished (My Learning Paths, sidebar organization, analytics)
- 🔄 Running locally on SQLite

---

## Deployment Strategy: Streamlit Cloud

### **Phase 1: Pre-Deployment Checklist** (Local Testing)

#### 1. Code Cleanup & Organization
- [ ] Remove all test files from root directory
  - `test_mastery_tracking.py`
  - `test_multi_path.py`
  - `test_four_fixes.py`
  - `test_dashboard_update.py`
  - Move to `/tests` directory or delete
- [ ] Clean up analysis documents
  - `MASTERY_CALCULATION_ANALYSIS.md`
  - `FIXES_SUMMARY.md`
  - Move to `/docs` directory
- [ ] Remove unused code/commented sections
- [ ] Verify all `# TODO` comments are resolved or documented

#### 2. Database Migration Plan
**Current**: SQLite (`learnflow.db`)
**Target**: PostgreSQL on Streamlit Cloud

**Migration Steps**:
- [ ] Create PostgreSQL schema migration script
- [ ] Export existing user data (if any beta users already exist)
- [ ] Update `database.py` to support both SQLite (local) and PostgreSQL (production)
- [ ] Add environment variable for database connection string
- [ ] Test connection to Streamlit Cloud PostgreSQL

#### 3. Environment Variables & Secrets
Create `.streamlit/secrets.toml` for:
- [ ] Database credentials (PostgreSQL)
- [ ] LLM API keys (OpenAI/Anthropic/Ollama endpoint)
- [ ] Any other API keys

**Example structure**:
```toml
[database]
host = "xxx.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "xxx"

[llm]
api_key = "xxx"
api_base = "xxx"
model = "gpt-4o-mini"
```

#### 4. Dependencies & Requirements
- [ ] Verify `requirements.txt` is complete and up-to-date
- [ ] Pin all package versions for stability
- [ ] Test fresh install in clean environment
- [ ] Check for security vulnerabilities: `pip-audit`

#### 5. Configuration Review
- [ ] Review all config files in `/config`:
  - Agent prompts (agent1/2/3_prompts.yaml)
  - LLM settings (llm.yaml)
  - Golden resources (golden_resources_by_role.yaml)
- [ ] Ensure no hardcoded credentials
- [ ] Set appropriate LLM temperature/max_tokens for production

#### 6. Performance & Limits
- [ ] Review and adjust content generation timeouts
- [ ] Implement rate limiting for API calls if needed
- [ ] Add error handling for API failures
- [ ] Test with slow network connections

#### 7. User Experience Polish
- [ ] Add loading spinners for all long operations
- [ ] Improve error messages (user-friendly, actionable)
- [ ] Add success confirmations for key actions
- [ ] Test full user journey from signup to module completion

#### 8. Data Validation & Security
- [ ] Validate all user inputs
- [ ] Prevent SQL injection (parameterized queries)
- [ ] Sanitize file paths
- [ ] Review password hashing (currently SHA256 - consider bcrypt for production)
- [ ] Add CSRF protection if needed

---

### **Phase 2: Streamlit Cloud Deployment**

#### 1. Prepare Repository
- [ ] Create GitHub repository (public or private)
- [ ] Add `.gitignore` for:
  ```
  learnflow.db
  *.pyc
  __pycache__/
  .env
  .streamlit/secrets.toml
  .DS_Store
  *.log
  ```
- [ ] Push clean codebase to main branch
- [ ] Add README.md with setup instructions

#### 2. Streamlit Cloud Setup
- [ ] Sign up for Streamlit Cloud (https://streamlit.io/cloud)
- [ ] Connect GitHub account
- [ ] Create new app from repository
- [ ] Configure deployment settings:
  - Python version: 3.11
  - Main file: `src/ui/app.py`
  - Advanced settings: Custom subdomain

#### 3. Database Setup on Streamlit Cloud
**Option A: Streamlit Cloud PostgreSQL**
- [ ] Enable PostgreSQL in Streamlit Cloud settings
- [ ] Get connection credentials
- [ ] Update secrets.toml

**Option B: External PostgreSQL (Supabase/Render/Railway)**
- [ ] Create PostgreSQL instance
- [ ] Get connection string
- [ ] Whitelist Streamlit Cloud IPs

#### 4. Configure Secrets
- [ ] Add secrets in Streamlit Cloud dashboard
- [ ] Test database connection
- [ ] Verify LLM API access

#### 5. Deploy & Test
- [ ] Deploy app to Streamlit Cloud
- [ ] Run smoke tests:
  - User signup
  - Path generation
  - Module completion
  - Multi-path management
  - Logout/login persistence
- [ ] Monitor logs for errors
- [ ] Check performance/response times

---

### **Phase 3: Beta Testing Preparation**

#### 1. Create Beta Testing Guide
- [ ] Write welcome email template
- [ ] Create user onboarding doc:
  - How to sign up
  - How to create first path
  - How to track progress
  - How to provide feedback
- [ ] Prepare feedback form/survey
- [ ] Set up feedback channel (email/Discord/Slack)

#### 2. Monitoring & Analytics
- [ ] Set up error tracking (Sentry or Streamlit native)
- [ ] Create basic analytics dashboard:
  - User signups
  - Paths created
  - Modules completed
  - Average session time
- [ ] Add logging for critical operations
- [ ] Monitor database size/growth

#### 3. Beta Tester Management
- [ ] Create list of beta testers (contacts)
- [ ] Prepare invitation emails
- [ ] Create beta tester accounts OR share signup link
- [ ] Set up regular check-ins schedule

#### 4. Known Issues & Limitations
Document for beta testers:
- [ ] 3-path limit per user
- [ ] SQLite → PostgreSQL differences (if any)
- [ ] Expected response times
- [ ] LLM generation limits
- [ ] Any feature not yet implemented

---

### **Phase 4: Launch to Beta Testers**

#### 1. Soft Launch (2-3 testers)
- [ ] Send invitations to 2-3 initial testers
- [ ] Monitor their usage closely
- [ ] Fix critical bugs immediately
- [ ] Collect initial feedback

#### 2. Gradual Rollout
- [ ] Week 1: Invite 5 more testers
- [ ] Week 2: Invite 10 more testers
- [ ] Week 3+: Open to wider beta group

#### 3. Feedback Collection
- [ ] Weekly feedback surveys
- [ ] Track common issues
- [ ] Prioritize feature requests
- [ ] Document user pain points

#### 4. Iterate & Improve
- [ ] Hot fixes for critical bugs
- [ ] Weekly minor improvements
- [ ] Monthly major feature releases
- [ ] Regular communication with beta testers

---

## Critical Files to Review Before Deployment

### Database
- `/Users/imenalsamarai/Documents/projects_MCP/learn_flow/src/core/database.py`
  - Add PostgreSQL support
  - Connection pooling
  - Migration script

### Configuration
- `/Users/imenalsamarai/Documents/projects_MCP/learn_flow/config/llm.yaml`
  - Set production model
  - Adjust temperature/tokens
- `/Users/imenalsamarai/Documents/projects_MCP/learn_flow/config/prompts/`
  - Review all agent prompts
  - Ensure quality content generation

### Security
- `/Users/imenalsamarai/Documents/projects_MCP/learn_flow/src/core/auth.py`
  - Upgrade password hashing to bcrypt
  - Add rate limiting

### UI
- `/Users/imenalsamarai/Documents/projects_MCP/learn_flow/src/ui/app.py`
  - Remove debug code
  - Improve error handling
  - Add user feedback messages

---

## Post-Deployment Monitoring

### Daily (First Week)
- [ ] Check error logs
- [ ] Monitor user signups
- [ ] Track module completion rates
- [ ] Respond to feedback

### Weekly
- [ ] Review usage analytics
- [ ] Analyze user behavior patterns
- [ ] Identify bottlenecks
- [ ] Plan improvements

### Monthly
- [ ] Comprehensive performance review
- [ ] Beta tester survey
- [ ] Roadmap updates
- [ ] Cost analysis (API usage)

---

## Rollback Plan

If critical issues occur:
1. **Immediate**: Pause new signups
2. **Notify** beta testers of issue
3. **Rollback** to previous working version
4. **Fix** issue locally
5. **Test** thoroughly
6. **Redeploy** with fix
7. **Resume** beta testing

---

## Success Metrics for Beta

### Week 1-2 (Stability)
- [ ] 0 critical bugs
- [ ] < 5 minor bugs
- [ ] 100% uptime
- [ ] All beta testers can complete signup

### Week 3-4 (Engagement)
- [ ] 80% of testers create at least 1 path
- [ ] 50% of testers complete at least 3 modules
- [ ] < 5-minute average path generation time
- [ ] Positive feedback from 70%+ of testers

### Month 2 (Validation)
- [ ] 80% retention rate
- [ ] 2+ paths per active user
- [ ] Feature requests prioritized
- [ ] Clear product-market fit signals

---

## Timeline Estimate

**Week 1**: Pre-deployment checklist + code cleanup
**Week 2**: Database migration + Streamlit Cloud setup
**Week 3**: Soft launch (2-3 testers) + immediate fixes
**Week 4**: Gradual rollout to 15-20 beta testers
**Month 2+**: Iterate based on feedback

---

## Next Immediate Steps

1. **Review this plan** - Confirm approach
2. **Run pre-deployment checklist** - Fix any issues
3. **Create requirements.txt** - Ensure all dependencies listed
4. **Add PostgreSQL support** - Database migration
5. **Set up GitHub repo** - Push clean code
6. **Deploy to Streamlit Cloud** - Initial deployment
7. **Invite first beta testers** - Soft launch

---

## Questions to Answer Before Deployment

1. **LLM Provider**: Which LLM will be used in production? (OpenAI, Anthropic, local Ollama?)
2. **Database**: Streamlit Cloud PostgreSQL or external (Supabase/Railway)?
3. **Beta Tester Count**: How many beta testers for initial launch?
4. **Feedback Channel**: Email, Discord, Slack, or form?
5. **Monitoring**: Basic logging or full analytics setup?
6. **Budget**: Any API cost limits to set?

---

Ready to proceed? Let me know which phase you'd like to start with!
