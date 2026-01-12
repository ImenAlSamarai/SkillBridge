# Mastery Calculation Flow Analysis

**Test User Journey**: test124 (fresh signup → fresh path)

---

## USER JOURNEY STEP-BY-STEP

### STEP 1: Signup → Generate Learning Path → WHERE DOES USER LAND?

**Code Flow:**
```
screen_1_form() line 385:
    result = run_full_workflow(...)
    st.session_state.path_data = result
    st.query_params["screen"] = "graph_new"  ← REDIRECTS TO DASHBOARD
    st.rerun()
```

**Expected**: User lands on **Dashboard** page
**Actual (reported)**: User lands on **Learn** page

**INCONSISTENCY #1**: ❌ **Fresh user after path generation goes to wrong screen**

**Possible Cause**: Check if `st.session_state.dashboard_tab` is being set to 'Learn' somewhere during path generation

---

### STEP 2: Dashboard Page - Initial Mastery Display

**Code Flow (screen_2_new - Dashboard tab):**
```python
# Line 660-668: Calculate mastery for each topic
for topic in topics:
    topic_id = topic['topic_id']
    initial_mastery = topic.get('mastery', 0)
    completed_modules = database.get_completed_modules(user_id, path_id, topic_id)
    points_per_module = (100 - initial_mastery) / 8.0
    mastery_from_modules = len(completed_modules) * points_per_module
    updated_mastery = min(int(initial_mastery + mastery_from_modules), 100)
    topic['mastery'] = updated_mastery  # ← UPDATES IN-MEMORY ONLY

# Line 671: Calculate average
avg_mastery = sum(t['mastery'] for t in topics) / len(topics)
```

**Calculation Method:**
- **Formula**: `updated_mastery = initial_mastery + (completed_modules × points_per_module)`
- **Points per module**: `(100 - initial_mastery) / 8.0`
- **Average**: Sum of all topic masteries / number of topics

**For test124** (21.7% shown):
- Initial assessment scores from run_full_workflow
- 0 modules completed
- Display = Average of initial scores

✅ **This calculation is correct**

---

### STEP 3: Click "Start Learning Now" → Learn Tab

**Code Flow:**
```python
# Line 802-805:
if st.button("Start Learning Now"):
    st.session_state.tabs_unlocked = True
    st.session_state.dashboard_tab = 'Learn'  ← SWITCHES TO LEARN TAB
    st.rerun()
```

**Expected**: Opens **Learn tab** (Kanban board)
**Actual**: ✅ Correct

---

### STEP 4: Learn Tab - Select "Basic Python" → Click Continue

**Code Flow:**
```python
# Line 895-897:
if st.button("▶ Continue", key=f"cont_{topic['topic_id']}"):
    st.session_state.selected_topic_id = topic['topic_id']
    st.query_params["screen"] = "topics"  ← GOES TO TOPICS SCREEN
    st.rerun()
```

**Expected**: Opens **screen_3_topics()** with selected topic
**Actual**: ✅ Opens topics screen

---

### STEP 5: Topics Screen - Which Module Opens?

**Code Flow:**
```python
# Line 1184-1189: AUTO-OPEN logic
if 'auto_open_module' in st.session_state and st.session_state.auto_open_module:
    next_module = len(completed_modules) + 1  # ← CALCULATES NEXT MODULE
    if next_module <= 8:
        st.session_state.current_module = next_module
```

**INCONSISTENCY #2**: ❌ **User sees Module 4 content instead of Module 1**

**Problem**: `len(completed_modules)` returns 3 instead of 0

**Possible Causes:**
1. Module completion records already exist for test124 (data pollution)
2. `auto_open_module` flag is incorrectly set
3. `st.session_state.current_module` is preset to 4

**Need to verify**:
```sql
SELECT * FROM user_topic_modules
WHERE user_id = [test124_id]
AND path_id = [test124_path_id]
AND topic_id = 'python';
```

---

### STEP 6: Module Completion Message

**Code Flow:**
```python
# Line 1265-1275: After answering questions
if all_correct:
    st.success(f"Perfect! {correct_count}/{total_questions} correct! Module {module_id} completed!")
    database.complete_module(user_id, path_id, selected_topic_id, module_id, mastery_bonus=0)
```

**INCONSISTENCY #3**: ❌ **"Perfect! 3/3 correct! Module 4 completed!" shown WITHOUT user answering**

**Problem**: Success message displayed before user interaction

**Possible Causes:**
1. Session state persists from previous interaction
2. Module was already marked as completed
3. Questions are pre-answered in cache

---

### STEP 7: Complete 2 Modules → Dashboard Shows 22.9%

**Calculation:**
- **Initial**: 21.7% average mastery
- **After 2 modules**: 22.9%
- **Increase**: +1.2%

**For a topic with X% initial mastery:**
- Points per module: (100 - X) / 8
- After 2 modules: X + (2 × points_per_module)

**Dashboard Calculation (line 660-671):**
```python
for topic in topics:
    initial_mastery = topic.get('mastery', 0)
    completed_modules = database.get_completed_modules(user_id, path_id, topic_id)
    points_per_module = (100 - initial_mastery) / 8.0
    updated_mastery = min(int(initial_mastery + len(completed_modules) * points_per_module), 100)
    topic['mastery'] = updated_mastery

avg_mastery = sum(t['mastery'] for t in topics) / len(topics)
```

✅ **This calculation is correct** (22.9% matches expected)

---

### STEP 8: Click "My Learning Paths" → Shows 22.9%

**Calculation Flow:**
```python
# screen_0_my_paths() line 246:
mastery = database.calculate_path_mastery(path)

# database.py calculate_path_mastery() line 322-338:
for topic in topics:
    initial_mastery = topic.get('mastery', 0)
    completed_modules = get_completed_modules(user_id, path_id, topic_id)
    points_per_module = (100 - initial_mastery) / 8.0
    updated_mastery = min(int(initial_mastery + len(completed_modules) * points_per_module), 100)
    updated_mastery_scores.append(updated_mastery)

return round(sum(updated_mastery_scores) / len(updated_mastery_scores), 1)
```

**Expected**: 22.9%
**Actual**: ✅ 22.9% (matches dashboard)

---

### STEP 9: Complete More Modules → Dashboard 26.2%, My Paths 24.2%

**Dashboard Calculation**: 26.2% ✅ (real-time from line 660-671)

**My Learning Paths Calculation**: 24.2% ❌

**INCONSISTENCY #4**: ❌ **2% discrepancy between Dashboard and My Learning Paths**

---

## ROOT CAUSE ANALYSIS

### Issue #1: Fresh User Lands on Wrong Screen
**Location**: `screen_1_form()` line 393
```python
st.query_params["screen"] = "graph_new"  # Correct - should go to dashboard
```

**But check**: Does `screen_2_new()` initialization (line 603-604) reset tab?
```python
if 'tabs_unlocked' not in st.session_state:
    st.session_state.tabs_unlocked = False
if 'dashboard_tab' not in st.session_state:
    st.session_state.dashboard_tab = 'Dashboard'  # ← SHOULD be 'Dashboard'
```

**Potential Issue**: Somewhere between lines 385-658, `dashboard_tab` is being set to 'Learn'

---

### Issue #2: Module 4 Opens Instead of Module 1
**Location**: `screen_3_topics()` line 1184-1189

**Debug needed**:
1. Check `completed_modules` count when user first arrives
2. Check if `auto_open_module` flag is correctly set
3. Verify no pre-existing completion records

---

### Issue #3: Pre-Completed Module Message
**Location**: `screen_3_topics()` line 1265-1275

**Likely cause**: Module completion persists in session state or database from previous run

**Check**:
- Is module already in `user_topic_modules` table?
- Is success message displayed from cached state?

---

### Issue #4: Dashboard 26.2% vs My Paths 24.2% (2% Discrepancy)

**Key Difference**:

**Dashboard** (line 668):
```python
topic['mastery'] = updated_mastery  # Modifies st.session_state.path_data
```
This **MUTATES** the in-memory `topics` array in `st.session_state.path_data`

**My Learning Paths** (line 246):
```python
paths = database.get_paths_by_user(user_id)  # Fresh from database
mastery = database.calculate_path_mastery(path)
```
This reads **FRESH** from database - does NOT see in-memory updates

**PROBLEM**: Dashboard updates `st.session_state.path_data['topics'][i]['mastery']` in memory, but this is **NEVER SAVED TO DATABASE**.

When user clicks "My Learning Paths", it loads fresh from database and recalculates, but the in-memory updates are lost.

---

## EXPECTED BEHAVIOR

1. ✅ Fresh user → Dashboard (not Learn tab)
2. ✅ Dashboard shows 21.7% (initial assessment average)
3. ✅ Click "Start Learning Now" → Learn tab (Kanban)
4. ✅ Select "Basic Python" → Opens Topics screen
5. ✅ Opens Module 1 (not Module 4)
6. ❌ No pre-completion message
7. ✅ Complete modules → Dashboard updates correctly
8. ✅ My Learning Paths shows **SAME** mastery as Dashboard

---

## MASTERY CALCULATION SUMMARY

### Formula (Consistent Everywhere):
```
topic_mastery = initial_mastery + (completed_modules × points_per_module)
points_per_module = (100 - initial_mastery) / 8.0
path_mastery = average(all topic_mastery scores)
```

### Calculation Locations:
1. **Dashboard tab** (line 660-671): ✅ Correct, updates in-memory
2. **Learn tab** (line 826-834): ✅ Correct, reads fresh each time
3. **My Learning Paths** (database.py line 322-338): ✅ Correct formula, but stale data

### The Core Issue:
**Dashboard modifies in-memory state, but NEVER persists to database**

The `topics` array in `st.session_state.path_data` is updated with new mastery scores, but the `paths` table in the database still has the original assessment scores.

When "My Learning Paths" loads, it reads from database → gets stale initial scores → recalculates → gets lower number.

---

## RECOMMENDATIONS

### Fix #1: Landing Screen
Check why fresh path goes to Learn instead of Dashboard

### Fix #2: Module Opening
Investigate why Module 4 opens instead of Module 1

### Fix #3: Pre-Completion Message
Verify no stale completion records exist

### Fix #4: Mastery Persistence (CRITICAL)
**Option A**: Save updated mastery to database after each module completion
**Option B**: Always recalculate mastery from completed modules (no caching)
**Option C**: Use in-memory state consistently (don't mix with DB reads)

**Recommended**: Option B - Always calculate from `user_topic_modules` table (single source of truth)
