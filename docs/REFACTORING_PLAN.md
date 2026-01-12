# Code Refactoring Plan
**Goal**: Clean, modular, configuration-driven architecture without breaking existing functionality

---

## Current Structure Analysis

### Existing Files
```
learn_flow/
├── app.py (UI + depth calculation logic)
├── job_parser.py (Agent 1)
├── topic_assessor.py (Agent 2)
├── content_generator.py (Agent 3 + resources hardcoded)
├── langgraph_workflow.py (Orchestrator)
├── database.py
├── llm_engine.py
├── config.py
├── config/
│   ├── llm.yaml (all prompts in one file)
│   ├── fields.yaml
│   ├── golden_sources.yaml
│   └── admin_users.yaml
├── scripts/ (admin + phase tests)
└── test_*.py (20+ test files in root)
```

### Issues to Fix
1. ❌ Depth calculation logic embedded in app.py
2. ❌ Learning resources hardcoded in content_generator.py
3. ❌ All LLM prompts in single llm.yaml file
4. ❌ Test files scattered in root directory
5. ❌ No clear separation between agent configs
6. ❌ Threshold values hardcoded in functions

---

## Target Structure

```
learn_flow/
├── src/                              # NEW: Source code
│   ├── agents/                       # Agent implementations
│   │   ├── __init__.py
│   │   ├── job_parser.py            (Agent 1)
│   │   ├── topic_assessor.py        (Agent 2)
│   │   └── content_generator.py     (Agent 3)
│   ├── workflow/
│   │   ├── __init__.py
│   │   └── orchestrator.py          (langgraph_workflow.py)
│   ├── core/                         # Core utilities
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── llm_engine.py
│   │   └── config_loader.py         (NEW: loads configs)
│   └── ui/
│       ├── __init__.py
│       └── app.py                    (Streamlit UI)
│
├── config/                           # Configuration files
│   ├── agents/                       # NEW: Per-agent configs
│   │   ├── agent1_job_parser.yaml
│   │   ├── agent2_topic_assessor.yaml
│   │   └── agent3_content_generator.yaml
│   ├── prompts/                      # NEW: Separate prompt files
│   │   ├── agent1_prompts.yaml
│   │   ├── agent2_prompts.yaml
│   │   └── agent3_prompts.yaml
│   ├── resources/                    # NEW: Learning resources
│   │   └── learning_resources.yaml
│   ├── thresholds.yaml               # NEW: All thresholds
│   ├── fields.yaml                   (keep)
│   ├── golden_sources.yaml           (keep)
│   └── admin_users.yaml              (keep)
│
├── tests/                            # Test files organized
│   ├── unit/
│   │   ├── test_job_parser.py
│   │   ├── test_topic_assessor.py
│   │   └── test_content_generator.py
│   ├── integration/
│   │   ├── test_workflow.py
│   │   ├── test_phase2d.py
│   │   └── test_all_agents_comprehensive.py
│   └── validation/
│       ├── test_foundations_fix.py
│       ├── test_statistical_basis.py
│       ├── test_advanced_content.py
│       └── test_reference_system_comprehensive.py
│
├── scripts/                          # Admin & setup scripts
│   ├── admin.py
│   └── populate_test_data.py
│
├── docs/                             # NEW: Documentation
│   ├── FINAL_REFERENCE_SOURCES.md
│   ├── REFERENCE_VALIDATION_COMPLETE.md
│   ├── TEST_RESULTS_SUMMARY.md
│   └── ...
│
├── database/                         (keep)
├── requirements.txt                  (keep)
├── .env.example                      (keep)
└── README.md                         (keep)
```

---

## Task Breakdown

### **TASK 1: Create Configuration Files**
**Duration**: Low risk - No code changes

#### 1.1 Create `config/thresholds.yaml`
Extract all hardcoded thresholds:
- Depth score calculation parameters
- Seniority mapping
- Module progression weights
- Mastery thresholds

#### 1.2 Create `config/resources/learning_resources.yaml`
Extract learning resources from `content_generator.py`:
- Fallback reference map
- Topic-specific resources
- Default resources

#### 1.3 Create `config/agents/agent1_job_parser.yaml`
Agent 1 configuration:
- Input parameters
- LLM model settings
- Skill extraction rules

#### 1.4 Create `config/agents/agent2_topic_assessor.yaml`
Agent 2 configuration:
- Module count (default 8)
- Mastery estimation rules
- Difficulty levels

#### 1.5 Create `config/agents/agent3_content_generator.yaml`
Agent 3 configuration:
- Content structure settings
- Reference validation rules
- Foundational keywords

#### 1.6 Split `config/llm.yaml` into `config/prompts/`
- `agent1_prompts.yaml` - Job parser prompts
- `agent2_prompts.yaml` - Topic assessor prompts
- `agent3_prompts.yaml` - Content generator prompts

**Test After Task 1**: Verify config files load correctly (no code changes yet)

---

### **TASK 2: Create Config Loader**
**Duration**: Low risk - New utility, doesn't break existing code

#### 2.1 Create `src/core/config_loader.py`
Functions:
- `load_agent_config(agent_name: str) -> dict`
- `load_prompts(agent_name: str) -> dict`
- `load_thresholds() -> dict`
- `load_learning_resources() -> dict`

**Test After Task 2**: Unit test config loader

---

### **TASK 3: Refactor Agents to Use Configs**
**Duration**: Medium risk - Changes agent code

#### 3.1 Update `content_generator.py`
- Replace hardcoded `fallback_map` with `load_learning_resources()`
- Replace hardcoded `foundational_keywords` with config
- Replace prompt loading from single llm.yaml to agent3_prompts.yaml

#### 3.2 Update `job_parser.py`
- Load config from `agent1_job_parser.yaml`
- Load prompts from `agent1_prompts.yaml`

#### 3.3 Update `topic_assessor.py`
- Load config from `agent2_topic_assessor.yaml`
- Load prompts from `agent2_prompts.yaml`

**Test After Task 3**: Run `scripts/test_phase2d.py` to verify agents still work

---

### **TASK 4: Refactor Depth Calculation**
**Duration**: Low risk - Extract function to utility

#### 4.1 Create `src/core/calculators.py`
Move `calculate_depth_score()` from `app.py`:
- Load thresholds from `config/thresholds.yaml`
- Keep same logic, just configuration-driven

#### 4.2 Update `app.py`
- Import from `src.core.calculators`

**Test After Task 4**: Run UI, verify depth calculation works

---

### **TASK 5: Reorganize File Structure**
**Duration**: Medium risk - File moves, import updates

#### 5.1 Create `src/` directory structure
```bash
mkdir -p src/agents src/workflow src/core src/ui
```

#### 5.2 Move files to `src/`
- `job_parser.py` → `src/agents/`
- `topic_assessor.py` → `src/agents/`
- `content_generator.py` → `src/agents/`
- `langgraph_workflow.py` → `src/workflow/orchestrator.py`
- `database.py` → `src/core/`
- `llm_engine.py` → `src/core/`
- `app.py` → `src/ui/`

#### 5.3 Update all imports
- Update import paths in all files
- Update `sys.path` in scripts and tests

#### 5.4 Add `__init__.py` files
- Make all directories proper Python packages

**Test After Task 5**: Run all tests to verify imports work

---

### **TASK 6: Reorganize Tests**
**Duration**: Low risk - File moves only

#### 6.1 Create test directory structure
```bash
mkdir -p tests/unit tests/integration tests/validation
```

#### 6.2 Move test files
**Unit tests** (agent-specific):
- `test_content_generator_adaptation.py` → `tests/unit/`
- `test_topic_assessor_adaptation.py` → `tests/unit/`

**Integration tests** (workflow):
- `scripts/test_phase2d.py` → `tests/integration/`
- `test_all_agents_comprehensive.py` → `tests/integration/`

**Validation tests** (content quality):
- `test_foundations_fix.py` → `tests/validation/`
- `test_statistical_basis.py` → `tests/validation/`
- `test_advanced_content.py` → `tests/validation/`
- `test_reference_system_comprehensive.py` → `tests/validation/`
- All other `test_*.py` → `tests/validation/`

#### 6.3 Update test imports
- Update import paths in test files

**Test After Task 6**: Run all tests from new locations

---

### **TASK 7: Move Documentation**
**Duration**: Zero risk - File moves only

#### 7.1 Create `docs/` directory
```bash
mkdir -p docs
```

#### 7.2 Move markdown files
- All `*.md` files (except README.md) → `docs/`

**No testing needed**

---

## Migration Safety

### What NOT to Change
- ✅ Business logic in agents
- ✅ LangGraph workflow logic
- ✅ Database schema
- ✅ LLM prompts content (just move to separate files)
- ✅ UI functionality

### Safety Measures
1. **After Each Task**: Run test suite
2. **Git Commits**: Commit after each successful task
3. **Rollback Plan**: Keep original files until all tests pass
4. **Import Validation**: Test imports before testing functionality

---

## Testing Checklist

After each task:
- [ ] Config files load correctly
- [ ] Unit tests pass
- [ ] Integration tests pass (`test_phase2d.py`)
- [ ] Content validation tests pass
- [ ] Reference quality tests pass
- [ ] UI loads without errors
- [ ] Database operations work

---

## Configuration Examples

### `config/thresholds.yaml`
```yaml
depth_calculation:
  seniority_levels:
    Student: 0.15
    Junior: 0.25
    Intermediate: 0.50
    Senior: 0.75
    Advanced: 1.00

  weights:
    target_seniority: 0.7
    mastery: 0.3

  module_progression:
    total_modules: 8
    max_bonus: 0.25

foundational_threshold: 0.3
reframing_threshold: 0.5
```

### `config/resources/learning_resources.yaml`
```yaml
prestigious_institutions:
  - MIT
  - Yale
  - Harvard
  - Stanford
  - 3Blue1Brown
  - StatQuest
  - Coursera
  - edX

fallback_references:
  machine_learning:
    - text: "Coursera: Machine Learning by Andrew Ng (Stanford) - FREE to audit"
      url: "https://www.coursera.org/learn/machine-learning"
    - text: "Neural Networks and Deep Learning by Michael Nielsen (FREE Online Book)"
      url: "http://neuralnetworksanddeeplearning.com/"

  statistics:
    - text: "StatQuest: Statistics Fundamentals Playlist (FREE)"
      url: "https://www.youtube.com/playlist?list=PLblh5JKOoLUK0FLuzwntyYI10UQFUhsY9"
    - text: "OpenIntro Statistics (FREE Online Book)"
      url: "https://www.openintro.org/book/os/"
```

### `config/agents/agent3_content_generator.yaml`
```yaml
agent_name: "Content Generator"
model: "llama-3.3-70b-versatile"
temperature: 0.4
max_tokens: 4000

content_structure:
  sections: [3, 4]  # Min 3, max 4 sections
  word_count: [400, 500]  # Min 400, max 500 words
  bold_terms: [15, 25]  # Aim for 15-25 bold terms

foundational_keywords:
  - "foundations"
  - "basics"
  - "introduction"
  - "basis"
  - "fundamentals"
  - "overview"
  - "essentials"

reference_validation:
  required_count: 2
  required_types: ["video", "book"]
  blocked_sources:
    - "khanacademy.org"
    - "youtube.com/results?search_query="
    - "youtube.com/@"  # channel homepages

  allowed_sources:
    - "ocw.mit.edu"
    - "oyc.yale.edu"
    - "online.stanford.edu"
    - "online-learning.harvard.edu"
    - "coursera.org"
    - "edx.org"
```

---

## Benefits

### For Developers
- 🔧 Change thresholds without touching code
- 📝 Update prompts in YAML files
- 🎓 Add/edit learning resources easily
- 🧪 Test with different configurations
- 📂 Clear project structure

### For System
- ✅ Separation of concerns
- ✅ Easy to test and maintain
- ✅ Configuration versioning
- ✅ No breaking changes
- ✅ Professional architecture

---

## Timeline

| Task | Risk | Est. Time | Testing |
|------|------|-----------|---------|
| 1. Create configs | Low | 1-2 hours | Config loading |
| 2. Config loader | Low | 30 min | Unit tests |
| 3. Refactor agents | Medium | 1-2 hours | Agent tests |
| 4. Refactor depth calc | Low | 30 min | UI test |
| 5. Reorganize files | Medium | 1 hour | All tests |
| 6. Reorganize tests | Low | 30 min | Run tests |
| 7. Move docs | Zero | 10 min | None |

**Total**: 4-6 hours of careful, incremental work

---

## Success Criteria

✅ All test scripts pass
✅ UI works without changes
✅ Developers can edit configs without code changes
✅ Clear, professional project structure
✅ Zero functionality broken
✅ Git history preserved

---

**Ready to proceed with Task 1?**
