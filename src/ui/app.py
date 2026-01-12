#!/usr/bin/env python3
"""
learn_flow Streamlit App
Phase 3.1: 4-Screen MVP (Form → Graph → Topic → Dashboard)
"""
import sys
from pathlib import Path

# Add project root to Python path (MUST be before other imports)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
from src.workflow import run_full_workflow
from src.core import database
from src.core.llm_engine import call_llm
from src.core import calculate_depth_score

# ============================================================
# AUTHENTICATION & SESSION MANAGEMENT
# ============================================================

def init_auth_session_state():
    """Initialize authentication session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None


def get_current_user_id() -> int:
    """Get current authenticated user's ID (with fallback for backward compatibility)"""
    if st.session_state.get('authenticated') and st.session_state.get('current_user'):
        return st.session_state.current_user['id']
    return 1  # Fallback to user 1 if not authenticated (backward compatibility)


def logout():
    """Logout current user and clear session"""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.path_data = None
    st.query_params["screen"] = "login"
    st.rerun()

# Page config
st.set_page_config(
    page_title="learn_flow - AI Career Path",
    page_icon=":material/rocket_launch:",
    layout="wide"
)

# Pure Streamlit defaults - no custom CSS (like Stock Peers template)

def evaluate_answer(user_answer: str, correct_answer: str, question_text: str = None) -> bool:
    """
    Evaluate if user's multiple choice answer is correct.

    Args:
        user_answer: User's selected option (A, B, C, or D)
        correct_answer: The correct option letter (A, B, C, or D)
        question_text: Unused, kept for backward compatibility

    Returns:
        True if answer matches, False otherwise
    """
    if not user_answer or not user_answer.strip():
        return False

    # Normalize both answers (uppercase, strip whitespace)
    user = user_answer.strip().upper()
    correct = correct_answer.strip().upper()

    # For multiple choice, just compare the letter
    # Handle cases like "A" or "A)" or "(A)" or "a"
    user_letter = user[0] if user else ""
    correct_letter = correct[0] if correct else ""

    return user_letter == correct_letter and user_letter in ["A", "B", "C", "D"]

# def evaluate_answer(user_answer: str, correct_answer: str, question_text: str) -> bool:
#     """
#     Use LLM to evaluate if user's answer is semantically correct
#
#     Args:
#         user_answer: User's response
#         correct_answer: Expected answer
#         question_text: The question being answered
#
#     Returns:
#         True if answer is semantically correct, False otherwise
#     """
#     if not user_answer or not user_answer.strip():
#         return False
#
#     # Quick exact match check first (optimization)
#     if user_answer.strip().lower() == correct_answer.strip().lower():
#         return True
#
#     # Check for obviously wrong answers first
#     wrong_indicators = ["i don't know", "idk", "no idea", "not sure", "dont know", "dunno", "?"]
#     if user_answer.strip().lower() in wrong_indicators or len(user_answer.strip()) < 3:
#         return False
#
#     # Use LLM for semantic evaluation
#     prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
#
# You are a STRICT answer evaluation agent. Grade student answers rigorously.
#
# **TASK**: Compare student's answer to expected answer. Return "CORRECT" ONLY if the student demonstrates actual understanding.
#
# **STRICT RULES**:
# - Answer MUST convey the SAME core concept and meaning
# - Vague answers like "I don't know", "something", "things" are INCORRECT
# - Incomplete answers are INCORRECT
# - Random guesses are INCORRECT
# - Accept paraphrases ONLY if they show true understanding
# - When in doubt, mark INCORRECT
# - Return ONLY "CORRECT" or "INCORRECT" (one word, nothing else)
#
# <|eot_id|><|start_header_id|>user<|end_header_id|>
#
# Question: {question_text}
#
# Expected answer: {correct_answer}
#
# Student's answer: {user_answer}
#
# Evaluate strictly. Is this CORRECT or INCORRECT?<|eot_id|><|start_header_id|>assistant<|end_header_id|>
#
# """
#
#     try:
#         response, _ = call_llm(prompt, temperature=0.1, max_tokens=10)
#         return "CORRECT" in response.strip().upper()
#     except Exception:
#         # Fallback to exact match if LLM fails
#         return user_answer.strip().lower() == correct_answer.strip().lower()


# Initialize session state
init_auth_session_state()  # Initialize auth first
if 'path_data' not in st.session_state:
    st.session_state.path_data = None
if 'selected_topic_id' not in st.session_state:
    st.session_state.selected_topic_id = None
if 'module_cache' not in st.session_state:
    st.session_state.module_cache = {}  # Cache: {(topic_id, module_id): content_data}
if 'module_names_cache' not in st.session_state:
    st.session_state.module_names_cache = {}  # Cache: {topic_id: {1: "name", 2: "name", ...}}

# Get current screen from query params (default to login for unauthenticated users)
screen = st.query_params.get("screen", "login")


# ============================================================
# SCREEN 0: LOGIN/SIGNUP
# ============================================================

def screen_0_login():
    """Screen 0: Login/Signup Screen"""
    st.title(":material/lock: SkillBridge Login")

    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # ===== LOGIN TAB =====
    with tab1:
        st.subheader("Login to Your Account")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    # Authenticate user
                    user = database.authenticate_user(email, password)
                    if user:
                        # Login successful
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.success(f"Welcome back, {user['name']}!")

                        # Check if user has existing paths
                        user_paths = database.get_paths_by_user(user['id'])
                        if user_paths:
                            # Has paths → Go to path selection screen
                            st.query_params["screen"] = "my_paths"
                        else:
                            # No paths → Go to form to create first path
                            st.query_params["screen"] = "form"
                        st.rerun()
                    else:
                        st.error("Invalid email or password")

    # ===== SIGNUP TAB =====
    with tab2:
        st.subheader("Create New Account")

        with st.form("signup_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
            submit = st.form_submit_button("Sign Up", use_container_width=True)

            if submit:
                # Validation
                if not name or not email or not password or not confirm_password:
                    st.error("Please fill in all fields")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    # Check if email already exists
                    existing_user = database.get_user_by_email(email)
                    if existing_user:
                        st.error("Email already registered. Please login instead.")
                    else:
                        # Create new user
                        try:
                            user_id = database.create_user(name, email, password, is_admin=False)
                            if user_id:
                                # Auto-login after signup
                                user = database.get_user(user_id)
                                if user:
                                    # Remove password_hash from user dict
                                    user_copy = dict(user)
                                    del user_copy['password_hash']
                                    st.session_state.authenticated = True
                                    st.session_state.current_user = user_copy
                                    st.success(f"Account created successfully! Welcome, {name}!")
                                    st.query_params["screen"] = "form"
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error creating account: {str(e)}")


# ============================================================
# SCREEN 0.5: MY LEARNING PATHS (Path Selection)
# ============================================================

def screen_0_my_paths():
    """Screen 0.5: My Learning Paths - Select or create learning path"""
    user_id = get_current_user_id()

    # Get user's paths
    paths = database.get_paths_by_user(user_id)
    path_count = len(paths)

    st.title(":material/school: My Learning Paths")

    # Show path counter
    if path_count == 0:
        st.info("You don't have any learning paths yet. Create your first path to get started!")
    else:
        st.markdown(f"**{path_count}/3 paths used**")

    st.markdown("---")

    # Display each path as a card
    for path in paths:
        path_id = path['id']
        mastery = database.calculate_path_mastery(path)
        topics = path.get('topics', [])

        # Calculate metrics
        total_modules_completed = database.get_total_completed_modules(user_id, path_id)
        total_modules = len(topics) * 8

        # Path card
        with st.container(border=True):
            # Path title - clearer format (with safe defaults)
            current_role = path.get('current_job_title') or path.get('current_description', 'Unknown')
            target_role = path.get('target_job_title') or path.get('target_description', 'Unknown')
            current_level = path.get('current_seniority', 'Unknown')
            target_level = path.get('target_seniority', 'Unknown')
            target_company = path.get('target_company', '')

            # Build title
            if target_company and target_company.lower() not in ['none', 'n/a', '']:
                company_part = f" at **{target_company}**"
            else:
                company_part = ""

            st.markdown(f"### :material/trending_up: Skills Building: {current_role} ({current_level}) → {target_role} ({target_level}){company_part}")

            # Progress bar with metrics
            col_progress, col_metrics = st.columns([2, 1])

            with col_progress:
                st.progress(mastery / 100.0, text=f"Overall Mastery: {mastery}%")

            with col_metrics:
                st.metric("Progress", f"{total_modules_completed}/{total_modules} modules")

            # Action buttons
            col1, col2 = st.columns([1, 5])

            with col1:
                if mastery >= 100:
                    button_label = "✅ Review"
                    button_type = "primary"
                else:
                    button_label = "▶ Resume"
                    button_type = "primary"

                if st.button(button_label, key=f"resume_{path_id}", use_container_width=True, type=button_type):
                    # Load path into session (add computed fields for dashboard)
                    path['topics_count'] = len(topics)
                    st.session_state.path_data = path
                    # Update last_accessed
                    database.update_path_last_accessed(path_id)
                    # Redirect to dashboard
                    st.query_params["screen"] = "graph_new"
                    st.rerun()

            # Collapsible Analytics section
            with st.expander("📊 Analytics", expanded=False):
                # Get activity data
                analytics_col1, analytics_col2 = st.columns(2)

                with analytics_col1:
                    st.caption("**Path Overview**")
                    created = path.get('created_at')
                    if created:
                        st.text(f"Created: {created[:10]}")
                    else:
                        st.text("Created: Unknown")
                    last_accessed = path.get('last_accessed')
                    if last_accessed:
                        st.text(f"Last accessed: {last_accessed[:10]}")
                    else:
                        st.text("Last accessed: Never")
                    st.text(f"Topics: {len(topics)}")

                with analytics_col2:
                    st.caption("**Learning Stats**")
                    total_hours = sum(t.get('estimated_hours', 0) for t in topics)
                    completed_percent = (total_modules_completed / total_modules * 100) if total_modules > 0 else 0
                    remaining_hours = int(total_hours * (1 - completed_percent / 100))
                    st.text(f"Est. total: {total_hours}h")
                    st.text(f"Remaining: ~{remaining_hours}h")
                    st.text(f"Completion: {completed_percent:.0f}%")

                # Activity heatmap - simple text-based representation
                st.caption("**Recent Activity (Last 7 Days)**")
                # Get recent activity from database
                with database.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DATE(completed_date) as date, COUNT(*) as count
                        FROM user_topic_modules
                        WHERE user_id = ? AND path_id = ?
                        AND completed_date >= date('now', '-7 days')
                        GROUP BY DATE(completed_date)
                        ORDER BY date
                    """, (user_id, path_id))
                    activity = cursor.fetchall()

                if activity:
                    # Create simple text heatmap
                    activity_dict = {row[0]: row[1] for row in activity}
                    from datetime import datetime, timedelta

                    heatmap_str = ""
                    for i in range(7):
                        date = (datetime.now() - timedelta(days=6-i)).strftime('%Y-%m-%d')
                        count = activity_dict.get(date, 0)
                        # Use blocks to represent activity level
                        if count == 0:
                            block = "░"
                        elif count <= 2:
                            block = "▒"
                        elif count <= 4:
                            block = "▓"
                        else:
                            block = "█"
                        heatmap_str += block

                    st.text(f"Activity: {heatmap_str} (7 days)")
                    total_last_7 = sum(row[1] for row in activity)
                    st.text(f"Modules completed: {total_last_7}")
                else:
                    st.text("No activity in last 7 days")

            st.markdown("")  # Spacing

    # Start New Path button
    st.markdown("### Create New Path")

    if path_count >= 3:
        st.button("➕ Start New Path", disabled=True, use_container_width=True)
        st.warning("⚠️ Maximum 3 paths reached. Resume an existing path to continue learning.")
    else:
        if st.button("➕ Start New Path", use_container_width=True, type="primary"):
            st.query_params["screen"] = "form"
            st.rerun()


def screen_1_form():
    """Screen 1: Career Path Form (12 fields)"""
    st.title(":material/rocket_launch: SkillBridge")
    st.markdown("SkillBridge transforms your current role description into a personalized career path to any target job—extracting explicit and implicit skill gaps, adapting content to your exact level, and preparing you for hard skills, soft skills, and company-specific interviews.")

    # Target role options
    TARGET_ROLES = [
        # Research
        "Quant Researcher",
        "Quant Analyst",
        "Quant Strategist",

        # Trading
        "Quant Trader",
        "Systematic Trader",
        "Algorithmic Trader",

        # Development
        "Quant Developer",
        "Algo Developer",
        "Trading Systems Engineer",

        # Data/ML
        "Data Scientist (Finance)",
        "ML Engineer (Finance)",

        # Risk
        "Risk Quant",
        "Risk Analyst",

        # Entry Level
        "Quant Intern",
        "Trading Intern",
    ]

    # Value proposition - collapsible
    with st.expander(":material/info: How SkillBridge Works", expanded=False):
        st.markdown(
            "**Copy your daily work description + paste any job spec → SkillBridge instantly reveals your precise skill gaps.** "
            "Using proprietary depth scoring, we generate adaptive content that matches your current mastery level, progressively increasing difficulty as you learn. "
            "Unlike generic courses, SkillBridge covers **hard skills (SDEs→HFT), soft skills (brainteasers→collaboration), and company-specific interview styles (Jane Street puzzles, Google system design)**—delivering a complete roadmap from your current reality to target role mastery."
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader(":material/person: Current Role")
            current_job_title = st.text_input(
                "Job Title",
                value="Undergrad Math Student",
                key="current_title"
            )
            current_seniority = st.selectbox(
                "Seniority Level",
                options=["Student", "Junior", "Intermediate", "Senior", "Advanced"],
                index=0,
                key="current_seniority"
            )
            current_description = st.text_area(
                "Current Skills & Experience",
                value="Calculus, linear algebra, basic Python",
                height=150,
                key="current_desc"
            )

    with col2:
        with st.container(border=True):
            st.subheader(":material/flag: Target Role")
            target_job_title = st.selectbox(
                "Job Title",
                options=TARGET_ROLES,
                index=0,  # Default to "Quant Researcher"
                key="target_title"
            )
            target_seniority = st.selectbox(
                "Seniority Level",
                options=["Junior", "Intermediate", "Senior", "Advanced"],
                index=0,
                key="target_seniority"
            )
            target_company = st.text_input(
                "Target Company (optional)",
                value="Jane Street",
                key="target_company"
            )
            target_description = st.text_area(
                "Required Skills & Responsibilities",
                value="Statistical arbitrage, derivatives pricing, Python backtesting",
                height=150,
                key="target_desc"
            )

    st.markdown("---")

    if st.button(":material/rocket_launch: Generate Learning Path", type="primary", use_container_width=True):
        with st.spinner("🤖 AI analyzing skill gap and building your path..."):
            # Prepare form data
            form_data = {
                "current_job_title": current_job_title,
                "current_description": current_description,
                "current_seniority": current_seniority,
                "target_job_title": target_job_title,
                "target_description": target_description,
                "target_seniority": target_seniority,
                "target_company": target_company,
                "target_industry": "Finance"  # Default for now
            }

            try:
                # Call Phase 2D workflow
                result = run_full_workflow(user_id=get_current_user_id(), form_data=form_data)

                if result.get("error"):
                    st.error(f"❌ Error: {result['error']}")
                else:
                    st.session_state.path_data = result
                    st.session_state.dashboard_tab = 'Dashboard'  # FIX #1: Force Dashboard for fresh path
                    st.session_state.tabs_unlocked = False  # Keep tabs locked initially
                    st.snow()  # Fireworks-style celebration animation
                    st.success(f"✅ Path generated! {result['topics_count']} topics, {result['global_readiness']}% readiness")
                    st.query_params["screen"] = "graph_new"
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error generating path: {e}")


def screen_2_graph():
    """Screen 2: Radar Chart + Progress Bars Dashboard"""
    import plotly.graph_objects as go

    st.title("📊 Mastery Mapping")

    if not st.session_state.path_data:
        st.warning("⚠️ No path data. Please generate a path first.")
        if st.button("← Back to Form"):
            st.query_params["screen"] = "form"
            st.rerun()
        return

    path_data = st.session_state.path_data
    topics = path_data.get('assessed_topics', [])
    user_id = get_current_user_id()
    path_id = path_data.get('path_id', '')

    # Update mastery for each topic based on completed modules
    for topic in topics:
        topic_id = topic['topic_id']
        initial_mastery = topic.get('mastery', 0)
        completed_modules = database.get_completed_modules(user_id, path_id, topic_id)
        points_per_module = (100 - initial_mastery) / 8.0
        mastery_from_modules = len(completed_modules) * points_per_module
        updated_mastery = min(int(initial_mastery + mastery_from_modules), 100)
        topic['mastery'] = updated_mastery

    # Calculate average mastery
    avg_mastery = sum(t['mastery'] for t in topics) / len(topics) if topics else 0

    # Display average mastery
    st.metric(
        label="Average Mastery Level",
        value=f"{avg_mastery:.1f}%",
        help="Average of all topic mastery scores. Each topic starts with a calculated baseline based on the gap between your profile and the target role, and increases as you progress through your learning."
    )

    # Determine stage
    if avg_mastery < 25:
        stage = "🔴 Early Stage"
        explanation = "Low overlap between your current skills and target role requirements."
    elif avg_mastery < 50:
        stage = "🟡 Building Phase"
        explanation = "Moderate overlap between your current skills and target role requirements."
    elif avg_mastery < 75:
        stage = "🟢 Advanced Stage"
        explanation = "Strong overlap between your current skills and target role requirements."
    else:
        stage = "✅ Final Polish"
        explanation = "Excellent overlap between your current skills and target role requirements."

    st.info(f"{stage}: {explanation}")
    st.markdown("---")

    with st.sidebar:
        # User info and logout
        if st.session_state.get('current_user'):
            user = st.session_state.current_user
            st.markdown(f"👤 **{user['name']}**")
            st.caption(user['email'])

            # Path counter
            path_count = database.get_path_count(user['id'])
            st.caption(f"📊 {path_count}/3 paths used")

            if st.button("🚪 Logout", use_container_width=True, key="logout_graph"):
                logout()
            st.markdown("---")

        st.metric("📚 Total Topics", path_data['topics_count'])
        st.metric("⏱️ Total Hours", f"{sum(t.get('estimated_hours', 0) for t in topics)}h")
        st.markdown("---")

        # NEW: Test new dashboard button
        if st.button("🆕 Try New Dashboard", use_container_width=True, type="primary"):
            st.query_params["screen"] = "graph_new"
            st.rerun()

        st.markdown("---")
        if st.button("📚 My Learning Paths", use_container_width=True):
            st.query_params["screen"] = "my_paths"
            st.rerun()
        if st.button("📚 Learn & Practice", use_container_width=True):
            st.query_params["screen"] = "topics"
            st.rerun()

    # Format topic names
    def format_topic_name(topic_id):
        return topic_id.replace('_', ' ').title()

    # TWO-COLUMN LAYOUT: Progress + Radar
    col_left, col_right = st.columns([1, 1])

    # LEFT: Detailed Progress
    with col_left:
        st.subheader("📈 Detailed Progress")
        st.caption("Sorted by mastery (focus on bottom items)")

        sorted_topics = sorted(topics, key=lambda x: x.get('mastery', 0))

        for topic in sorted_topics:
            mastery = topic.get('mastery', 0)
            topic_id = topic.get('topic_id', 'unknown')
            formatted_name = format_topic_name(topic_id)
            hours = topic.get('estimated_hours', 0)
            subtopics_count = len(topic.get('subtopics', []))

            if mastery >= 80:
                emoji = "🟢"
            elif mastery >= 50:
                emoji = "🟡"
            elif mastery >= 20:
                emoji = "🟠"
            else:
                emoji = "⬜"

            col_topic, col_info = st.columns([3, 1])
            with col_topic:
                st.markdown(f"**{emoji} {formatted_name}**")
            with col_info:
                st.caption(f"{hours}h · {subtopics_count} subtopics")

            st.progress(mastery / 100, text=f"{mastery}%")
            st.markdown("")

    # RIGHT: Radar Chart
    with col_right:
        st.subheader("📊 Knowledge Profile")

        topic_names = [format_topic_name(t.get('topic_id', 'unknown')) for t in topics]
        mastery_values = [t.get('mastery', 0) for t in topics]

        hover_texts = [
            f"<b>Topic:</b> {format_topic_name(t.get('topic_id', 'unknown'))}<br>"
            f"<b>Progress:</b> {t.get('mastery', 0):.1f}%<br>"
            f"<b>Hours:</b> {t.get('estimated_hours', 0)}h<br>"
            f"<b>Subtopics:</b> {len(t.get('subtopics', []))}"
            for t in topics
        ]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=mastery_values,
            theta=topic_names,
            fill='toself',
            fillcolor='rgba(99, 110, 250, 0.3)',
            line=dict(color='rgb(99, 110, 250)', width=3),
            marker=dict(size=8, color='rgb(99, 110, 250)'),
            hovertext=hover_texts,
            hoverinfo='text',
            name='Current Mastery'
        ))

        fig_radar.update_layout(
            polar=dict(
                bgcolor='rgba(240, 240, 240, 0.5)',
                radialaxis=dict(visible=True, range=[0, 100], ticksuffix='%', gridcolor='rgba(128, 128, 128, 0.4)', tickfont=dict(size=12, color='#333333'), tickmode='linear', tick0=0, dtick=20),
                angularaxis=dict(gridcolor='rgba(128, 128, 128, 0.4)', linecolor='rgba(128, 128, 128, 0.6)', tickfont=dict(size=11, color='#333333'))
            ),
            showlegend=False,
            height=500,
            margin=dict(l=80, r=80, t=40, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white'
        )

        st.plotly_chart(fig_radar, use_container_width=True)
        st.info(f"💡 Average mastery: {avg_mastery:.1f}%")


def screen_2_new():
    """Screen 2 NEW: Tabbed Dashboard (Dashboard/Learn/Analytics)"""
    import plotly.graph_objects as go

    # Load path data from session state or database
    if not st.session_state.path_data:
        # Try to load most recent path from database
        user_id = get_current_user_id()
        paths = database.get_paths_by_user(user_id)
        if paths:
            # Get most recent path
            most_recent = paths[0]
            st.session_state.path_data = most_recent
        else:
            st.warning("⚠️ No path data. Please generate a path first.")
            if st.button("← Back to Form"):
                st.query_params["screen"] = "form"
                st.rerun()
            return

    path_data = st.session_state.path_data
    # Handle both 'assessed_topics' (from workflow) and 'topics' (from database)
    topics = path_data.get('assessed_topics', path_data.get('topics', []))
    user_id = get_current_user_id()
    path_id = path_data.get('path_id', path_data.get('id', ''))

    # Format topic names helper
    def format_topic_name(topic_id):
        return topic_id.replace('_', ' ').title()

    # Initialize session state for tab selection and unlock status
    if 'dashboard_tab' not in st.session_state:
        st.session_state.dashboard_tab = 'Dashboard'
    if 'tabs_unlocked' not in st.session_state:
        st.session_state.tabs_unlocked = False  # Locked initially

    # Clear any previous topic selection when entering dashboard
    if 'selected_topic_id' in st.session_state:
        del st.session_state.selected_topic_id

    # SIDEBAR: Cleaner Navigation
    with st.sidebar:
        st.markdown("### :material/rocket_launch: SkillBridge")
        st.markdown("---")

        # VIEWS Section
        st.caption("VIEWS")

        # Tab navigation with radio-style indicators
        # Show only Dashboard initially, unlock Learn after "Start Learning Now" clicked
        tabs_to_show = ['Dashboard']
        if st.session_state.tabs_unlocked:
            tabs_to_show.append('Learn')

        for tab in tabs_to_show:
            is_active = st.session_state.dashboard_tab == tab
            indicator = "●" if is_active else "○"

            if st.button(f"{indicator} {tab}", key=f"tab_{tab}", use_container_width=True,
                        type="primary" if is_active else "secondary"):
                st.session_state.dashboard_tab = tab
                st.rerun()

        st.markdown("---")

        # My Learning Paths button
        if st.button("← My Learning Paths", use_container_width=True, type="secondary"):
            st.query_params["screen"] = "my_paths"
            st.rerun()

        # Spacer to push user info to bottom
        st.markdown("<br>" * 10, unsafe_allow_html=True)

        # User info and logout at bottom
        if st.session_state.get('current_user'):
            st.markdown("---")
            user = st.session_state.current_user
            st.markdown(f"👤 **{user['name']}**")
            st.caption(user['email'])

            # Path counter
            path_count = database.get_path_count(user['id'])
            st.caption(f"📊 {path_count}/3 paths used")

            if st.button("🚪 Logout", use_container_width=True, key="logout_new"):
                logout()

    # ============================================================
    # DASHBOARD TAB
    # ============================================================
    if st.session_state.dashboard_tab == 'Dashboard':
        st.title(":material/dashboard: Dashboard")

        # Force reload path data to ensure we have latest completion data
        # This ensures Dashboard always shows up-to-date progress
        if user_id:
            paths_fresh = database.get_paths_by_user(user_id)
            if paths_fresh:
                # Find the current path
                for p in paths_fresh:
                    if p['id'] == path_id:
                        # Add computed fields that Dashboard expects
                        p['topics_count'] = len(p.get('assessed_topics', p.get('topics', [])))
                        st.session_state.path_data = p
                        path_data = p
                        topics = p.get('assessed_topics', p.get('topics', []))
                        break

        # FIX #4: Calculate mastery from completed modules (single source of truth)
        # Calculate current mastery for each topic without modifying the topic objects
        topic_masteries = []
        topics_with_updated_mastery = []  # Create new list with updated mastery values

        for topic in topics:
            topic_id = topic['topic_id']
            initial_mastery = topic.get('mastery', 0)
            completed_modules = database.get_completed_modules(user_id, path_id, topic_id)
            points_per_module = (100 - initial_mastery) / 8.0
            mastery_from_modules = len(completed_modules) * points_per_module
            updated_mastery = min(int(initial_mastery + mastery_from_modules), 100)
            topic_masteries.append(updated_mastery)

            # Create a copy of topic with updated mastery for display purposes
            topic_display = topic.copy()
            topic_display['mastery'] = updated_mastery
            topic_display['modules_completed'] = len(completed_modules)
            topics_with_updated_mastery.append(topic_display)

        # Calculate average mastery from computed values (not stored in topics)
        avg_mastery = sum(topic_masteries) / len(topic_masteries) if topic_masteries else 0

        # Determine stage and explanation
        if avg_mastery < 25:
            stage = ":material/radio_button_unchecked: Early Stage"
            stage_name = "Early Stage"
            explanation = "Low overlap between your current skills and target role requirements."
        elif avg_mastery < 50:
            stage = ":material/pending: Building Phase"
            stage_name = "Building Phase"
            explanation = "Moderate overlap between your current skills and target role requirements."
        elif avg_mastery < 75:
            stage = ":material/check_circle_outline: Advanced Stage"
            stage_name = "Advanced Stage"
            explanation = "Strong overlap between your current skills and target role requirements."
        else:
            stage = ":material/check_circle: Final Polish"
            stage_name = "Final Polish"
            explanation = "Excellent overlap between your current skills and target role requirements."

        # HERO CARD - Reorganized for better comprehension
        with st.container(border=True):
            st.subheader("Average Mastery Level")

            # Show percentage and stage side by side
            col_perc, col_stage = st.columns([1, 2])
            with col_perc:
                st.markdown(f"### {avg_mastery:.1f}%")
            with col_stage:
                st.markdown(f"### {stage}")

            st.markdown(explanation)
            st.caption(":material/info: Average of all topic mastery scores. Each topic starts with a calculated baseline and increases as you complete modules.")
            st.markdown(":material/lightbulb: **Tip:** Prioritize topics under 40% for maximum impact")

        # TWO COLUMNS: Radar Chart (left) + Topic List (right)
        col_radar, col_topics = st.columns([1.2, 1])

        with col_radar:
            st.subheader(":material/radar: Knowledge Profile")
            st.caption("Visual overview of your skill coverage")

            topic_names = [format_topic_name(t.get('topic_id', 'unknown')) for t in topics_with_updated_mastery]
            mastery_values = [t.get('mastery', 0) for t in topics_with_updated_mastery]

            hover_texts = [
                f"<b>Topic:</b> {format_topic_name(t.get('topic_id', 'unknown'))}<br>"
                f"<b>Progress:</b> {t.get('mastery', 0):.1f}%<br>"
                f"<b>Modules:</b> {t.get('modules_completed', 0)}/8<br>"
                f"<b>Hours:</b> {t.get('estimated_hours', 0)}h"
                for t in topics_with_updated_mastery
            ]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=mastery_values,
                theta=topic_names,
                fill='toself',
                fillcolor='rgba(156, 163, 175, 0.3)',  # Gray fill with transparency
                line=dict(color='rgb(107, 114, 128)', width=3),  # Medium gray line
                marker=dict(size=8, color='rgb(107, 114, 128)'),  # Medium gray markers
                hovertext=hover_texts,
                hoverinfo='text',
                name='Current Mastery'
            ))

            fig_radar.update_layout(
                polar=dict(
                    bgcolor='rgba(0, 0, 0, 0)',
                    radialaxis=dict(visible=True, range=[0, 100], ticksuffix='%',
                                    gridcolor='rgba(128, 128, 128, 0.3)',
                                    tickfont=dict(size=12),
                                    tickmode='linear', tick0=0, dtick=20),
                    angularaxis=dict(gridcolor='rgba(128, 128, 128, 0.3)',
                                     linecolor='rgba(128, 128, 128, 0.5)',
                                     tickfont=dict(size=11))
                ),
                showlegend=False,
                height=500,
                margin=dict(l=60, r=60, t=20, b=20),
                paper_bgcolor='rgba(0, 0, 0, 0)',
                plot_bgcolor='rgba(0, 0, 0, 0)'
            )

            st.plotly_chart(fig_radar, use_container_width=True)

        with col_topics:
            st.subheader(":material/library_books: Topics by Mastery")
            st.caption("Sorted by progress level")

            # Sort topics by mastery (highest first) - use updated mastery values
            sorted_topics = sorted(topics_with_updated_mastery, key=lambda x: x.get('mastery', 0), reverse=True)

            # Use Streamlit container with height control (500px to match radar)
            with st.container(height=500):
                # Render each topic with text-based progress bar
                for topic in sorted_topics:
                    mastery = topic.get('mastery', 0)
                    topic_name = format_topic_name(topic.get('topic_id', 'unknown'))

                    # Create text-based progress bar (10 blocks total)
                    filled = int(mastery / 10)
                    empty = 10 - filled
                    progress_bar = '█' * filled + '░' * empty

                    # Display: Topic name | progress bar | percentage
                    st.text(f"{topic_name:<20} {progress_bar} {mastery}%")

        # Path summary metrics in one row - centered with border
        st.markdown("")  # Add spacing
        total_modules_completed = database.get_total_completed_modules(user_id, path_id)
        total_modules = len(topics) * 8
        total_hours = sum(t.get('estimated_hours', 0) for t in topics)
        remaining_hours = int(total_hours * (1 - total_modules_completed / total_modules)) if total_modules > 0 else total_hours

        # Center the metrics box
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            with st.container(border=True):
                col_metric1, col_metric2, col_metric3 = st.columns(3)
                with col_metric1:
                    st.metric("Topics", path_data['topics_count'])
                with col_metric2:
                    st.metric("Modules", f"{total_modules_completed}/{total_modules}")
                with col_metric3:
                    st.metric("Remaining", f"~{remaining_hours}h")

        # Centered CTA button
        st.markdown("")  # Add spacing
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(":material/play_arrow: Start Learning Now", use_container_width=True, type="primary"):
                st.session_state.tabs_unlocked = True  # Unlock Learn and Analytics tabs
                st.session_state.dashboard_tab = 'Learn'
                st.rerun()

    # ============================================================
    # LEARN TAB
    # ============================================================
    elif st.session_state.dashboard_tab == 'Learn':
        # Check if user clicked a topic from racing track
        if 'sel_topic' in st.query_params:
            # Navigate to topics screen
            st.session_state.selected_topic_id = st.query_params['sel_topic']
            del st.query_params['sel_topic']
            st.query_params["screen"] = "topics"
            st.rerun()

        st.title(":material/school: Learn")
        st.caption("All topics sorted by priority — Focus on high-priority items for maximum impact")

        # Calculate mastery and gaps for all topics
        topic_data = []
        for topic in topics:
            topic_id = topic['topic_id']
            initial_mastery = topic.get('mastery', 0)

            # Get completed modules
            completed_modules = database.get_completed_modules(user_id, path_id, topic_id)

            # Calculate current mastery
            points_per_module = (100 - initial_mastery) / 8.0
            mastery_from_modules = len(completed_modules) * points_per_module
            current_mastery = min(int(initial_mastery + mastery_from_modules), 100)

            # Target is always 100% (user needs to master everything for target role)
            target_mastery = 100
            gap = target_mastery - current_mastery

            topic_data.append({
                'topic_id': topic_id,
                'name': format_topic_name(topic_id),
                'current': current_mastery,
                'target': target_mastery,
                'gap': gap,
                'hours': topic.get('estimated_hours', 0),
                'modules_done': len(completed_modules),
                'modules_total': 8
            })

        # KANBAN BOARD: Group topics by progress status
        st.subheader(":material/route: Your Learning Path")
        st.caption("Track your progress across all topics — Start with 'To Start' column")

        # Group topics into columns based on mastery
        to_start = [t for t in topic_data if t['current'] <= 25]
        in_progress = [t for t in topic_data if 25 < t['current'] <= 75]
        nearly_done = [t for t in topic_data if 75 < t['current'] < 100]
        mastered = [t for t in topic_data if t['current'] == 100]

        # Sort each group by gap (highest gap = highest priority)
        to_start.sort(key=lambda x: x['gap'], reverse=True)
        in_progress.sort(key=lambda x: x['gap'], reverse=True)
        nearly_done.sort(key=lambda x: x['gap'], reverse=True)
        mastered.sort(key=lambda x: x['gap'], reverse=True)

        # Create 4 columns
        col1, col2, col3, col4 = st.columns(4)

        # Column 1: To Start (0-25%)
        with col1:
            st.markdown("##### :material/radio_button_unchecked: To Start")
            st.caption(f"{len(to_start)} topics")
            st.markdown("---")

            for topic in to_start:
                with st.container(border=True):
                    st.markdown(f"**{topic['name']}**")
                    st.caption(f"{topic['current']}% • {topic['modules_done']}/{topic['modules_total']} modules")
                    if st.button("▶ Start", key=f"start_{topic['topic_id']}", use_container_width=True, type="primary"):
                        st.session_state.selected_topic_id = topic['topic_id']
                        # Set starting module for fresh topics
                        if topic['modules_done'] == 0:
                            st.session_state.current_module = 1
                        else:
                            st.session_state.current_module = topic['modules_done'] + 1
                        # Clear completion state
                        st.session_state.show_completion = False
                        st.session_state.completed_module_id = None
                        st.session_state.user_answers = {}
                        st.query_params["screen"] = "topics"
                        st.rerun()

        # Column 2: In Progress (26-75%)
        with col2:
            st.markdown("##### :material/pending: In Progress")
            st.caption(f"{len(in_progress)} topics")
            st.markdown("---")

            for topic in in_progress:
                with st.container(border=True):
                    st.markdown(f"**{topic['name']}**")
                    st.caption(f"{topic['current']}% • {topic['modules_done']}/{topic['modules_total']} modules")
                    if st.button("▶ Continue", key=f"cont_{topic['topic_id']}", use_container_width=True, type="primary"):
                        st.session_state.selected_topic_id = topic['topic_id']
                        # FIX #2: Set correct starting module
                        if topic['modules_done'] == 0:
                            st.session_state.current_module = 1  # Start at module 1
                        else:
                            st.session_state.current_module = topic['modules_done'] + 1  # Resume at next
                        # Clear completion state when starting a new topic/module
                        st.session_state.show_completion = False
                        st.session_state.completed_module_id = None
                        st.session_state.user_answers = {}
                        st.query_params["screen"] = "topics"
                        st.rerun()

        # Column 3: Nearly Done (76-99%)
        with col3:
            st.markdown("##### :material/check_circle_outline: Nearly Done")
            st.caption(f"{len(nearly_done)} topics")
            st.markdown("---")

            for topic in nearly_done:
                with st.container(border=True):
                    st.markdown(f"**{topic['name']}**")
                    st.caption(f"{topic['current']}% • {topic['modules_done']}/{topic['modules_total']} modules")
                    if st.button("▶ Finish", key=f"finish_{topic['topic_id']}", use_container_width=True, type="secondary"):
                        st.session_state.selected_topic_id = topic['topic_id']
                        # Set module to next uncompleted
                        st.session_state.current_module = topic['modules_done'] + 1
                        # Clear completion state
                        st.session_state.show_completion = False
                        st.session_state.completed_module_id = None
                        st.session_state.user_answers = {}
                        st.query_params["screen"] = "topics"
                        st.rerun()

        # Column 4: Mastered (100%)
        with col4:
            st.markdown("##### :material/check_circle: Mastered")
            st.caption(f"{len(mastered)} topics")
            st.markdown("---")

            for topic in mastered:
                with st.container(border=True):
                    st.markdown(f"**{topic['name']}**")
                    st.caption("✓ Complete • 8/8 modules")
                    if st.button("▶ Review", key=f"review_{topic['topic_id']}", use_container_width=True, type="secondary"):
                        st.session_state.selected_topic_id = topic['topic_id']
                        # For completed topics, don't auto-open a module (let user select from sidebar)
                        st.session_state.current_module = None
                        # Clear completion state
                        st.session_state.show_completion = False
                        st.session_state.completed_module_id = None
                        st.session_state.user_answers = {}
                        st.query_params["screen"] = "topics"
                        st.rerun()

    # ============================================================
    # ANALYTICS TAB
    # ============================================================
    elif st.session_state.dashboard_tab == 'Analytics':
        st.title(":material/analytics: Analytics")
        st.info(":material/info: Analytics tab coming soon! This will show activity heatmap, performance charts, and milestones.")


def screen_3_topics():
    """Screen 3: Learning Module with Questions & Mastery Update"""

    st.title(":material/school: Learn & Practice")

    # Load path data from session state or database
    if not st.session_state.path_data:
        # Try to load most recent path from database
        user_id = get_current_user_id()
        paths = database.get_paths_by_user(user_id)
        if paths:
            # Get most recent path
            most_recent = paths[0]
            st.session_state.path_data = most_recent
        else:
            st.warning("⚠️ No path data. Please generate a path first.")
            if st.button("← Back to Form"):
                st.query_params["screen"] = "form"
                st.rerun()
            return

    path_data = st.session_state.path_data
    # Handle both 'assessed_topics' (from workflow) and 'topics' (from database)
    topics = path_data.get('assessed_topics', path_data.get('topics', []))
    user_id = get_current_user_id()
    path_id = path_data.get('path_id', path_data.get('id', ''))

    # Get target seniority from database for depth calculation
    path_record = database.get_path(path_id) if path_id else None
    target_seniority = path_record.get('target_seniority', 'Intermediate') if path_record else 'Intermediate'

    # Helper function to format topic names
    def format_topic_name(topic_id):
        return topic_id.replace('_', ' ').title()

    # Check if topics exist
    if not topics:
        st.error("No topics found in this learning path.")
        if st.button("← Back to Dashboard"):
            st.query_params["screen"] = "graph_new"
            st.rerun()
        return

    # Get pre-selected topic from query params or session state
    if 'sel_topic' in st.query_params:
        # Coming from racing track or external link
        selected_topic_id = st.query_params['sel_topic']
        st.session_state.selected_topic_id = selected_topic_id
        # Clean up query param
        del st.query_params['sel_topic']
    elif 'selected_topic_id' in st.session_state and st.session_state.selected_topic_id:
        # From session state (Learn tab or sidebar navigation)
        selected_topic_id = st.session_state.selected_topic_id
    else:
        # Default to first topic
        selected_topic_id = topics[0]['topic_id']
        st.session_state.selected_topic_id = selected_topic_id

    # Find selected topic
    selected_topic = next((t for t in topics if t['topic_id'] == selected_topic_id), None)

    if not selected_topic:
        st.error(f"Topic not found: '{selected_topic_id}'")
        st.write("Available topics:", [t['topic_id'] for t in topics])
        if st.button("← Back to Dashboard"):
            st.query_params["screen"] = "graph_new"
            st.rerun()
        return

    # Get current mastery and completed modules
    initial_mastery = selected_topic.get('mastery', 0)  # From assessment
    completed_modules = database.get_completed_modules(user_id, path_id, selected_topic_id)

    # NEW SIDEBAR: Module Navigation
    with st.sidebar:
        st.markdown("### :material/rocket_launch: SkillBridge")
        st.markdown("---")

        # Topic selector at top
        st.caption("CURRENT TOPIC")

        topic_options = {t['topic_id']: format_topic_name(t['topic_id']) for t in topics}
        selected_display = st.selectbox(
            "Select Topic",
            options=list(topic_options.keys()),
            format_func=lambda x: topic_options[x],
            index=list(topic_options.keys()).index(selected_topic_id) if selected_topic_id in topic_options else 0,
            key="topic_selector",
            label_visibility="collapsed"
        )

        # If user changed topic, update and reload
        if selected_display != selected_topic_id:
            st.session_state.selected_topic_id = selected_display
            st.session_state.current_module = None
            st.rerun()

        st.markdown("---")
        st.caption("MODULES")

        # Generate module names if not cached (with user context for role-specific modules)
        # Cache key includes path_id to ensure different paths get different modules
        module_cache_key = (path_id, selected_topic_id)
        if module_cache_key not in st.session_state.module_names_cache:
            from src.agents.content_generator import generate_module_names
            # Pass user context for role-specific module names
            target_role = path_record.get('target_job_title', 'Quant Analyst') if path_record else 'Quant Analyst'
            target_sen = path_record.get('target_seniority', 'Intermediate') if path_record else 'Intermediate'
            module_names = generate_module_names(
                topic_id=selected_topic_id,
                target_role=target_role,
                target_seniority=target_sen,
                mastery=initial_mastery
            )
            st.session_state.module_names_cache[module_cache_key] = module_names
        else:
            module_names = st.session_state.module_names_cache[module_cache_key]

        # Get answers to determine in-progress vs completed
        # A module is "in progress" if it has answers but not all correct
        # A module is "completed" if it's in completed_modules list
        # A module is "todo" if no answers

        for module_id in range(1, 9):
            # Check status
            if module_id in completed_modules:
                status = "✅"
            elif st.session_state.get('current_module') == module_id:
                status = "⏳"
            else:
                status = "○"

            # Module button
            module_name = module_names.get(module_id, f"Module {module_id}")
            if st.button(
                f"{status} {module_id}. {module_name[:20]}{'...' if len(module_name) > 20 else ''}",
                key=f"sidebar_module_{module_id}",
                use_container_width=True,
                type="secondary",
                disabled=(module_id in completed_modules)
            ):
                st.session_state.current_module = module_id
                st.session_state.user_answers = {}
                st.rerun()

        st.markdown("---")

        # Navigation buttons
        if st.button("← My Learning Paths", use_container_width=True, type="secondary"):
            st.query_params["screen"] = "my_paths"
            st.rerun()
        if st.button("📊 Dashboard", use_container_width=True, type="secondary"):
            st.session_state.dashboard_tab = 'Dashboard'
            st.query_params["screen"] = "graph_new"
            st.rerun()

        # Spacer to push user info to bottom
        st.markdown("<br>" * 3, unsafe_allow_html=True)

        # User info and logout at bottom
        if st.session_state.get('current_user'):
            st.markdown("---")
            user = st.session_state.current_user
            st.markdown(f"👤 **{user['name']}**")
            st.caption(user['email'])

            # Path counter
            path_count = database.get_path_count(user['id'])
            st.caption(f"📊 {path_count}/3 paths used")

            if st.button("🚪 Logout", use_container_width=True, key="logout_topics"):
                logout()

    # Simple calculation: each module adds progress toward 100%
    # Modules give you the remaining gap: (100 - initial) / 8 per module
    points_per_module = (100 - initial_mastery) / 8.0
    mastery_from_modules = len(completed_modules) * points_per_module
    updated_mastery = min(int(initial_mastery + mastery_from_modules), 100)

    # Calculate gain for display
    mastery_gain = updated_mastery - initial_mastery

    # Display topic header with updated mastery (formatted name)
    st.header(f":material/menu_book: {format_topic_name(selected_topic_id)}")

    # Compact header with key info only
    col1, col2, col3 = st.columns(3)
    with col1:
        if mastery_gain > 0:
            st.metric("Mastery", f"{updated_mastery}%", f"+{mastery_gain}%")
        else:
            st.metric("Mastery", f"{updated_mastery}%")
    with col2:
        st.metric("Progress", f"{len(completed_modules)}/8 modules")
    with col3:
        st.metric("Est. Hours", f"{selected_topic['estimated_hours']}h")

    # Progress bar - using text representation for neutral theme
    filled = int(updated_mastery / 10)
    empty = 10 - filled
    progress_bar = '█' * filled + '░' * empty
    st.text(f"{progress_bar}")

    st.markdown("---")

    # Initialize session state for module
    if 'current_module' not in st.session_state:
        st.session_state.current_module = None
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'advance_to_next' not in st.session_state:
        st.session_state.advance_to_next = False
    if 'show_completion' not in st.session_state:
        st.session_state.show_completion = False

    # Check if we need to advance to next module
    if st.session_state.advance_to_next:
        current = st.session_state.current_module

        # Clear all answer-related keys from session state
        keys_to_delete = [key for key in st.session_state.keys() if key.startswith('answer_')]
        for key in keys_to_delete:
            del st.session_state[key]

        if current and current < 8:
            st.session_state.current_module = current + 1
            st.session_state.user_answers = {}
            st.session_state.show_completion = False  # Reset completion flag
        elif current and current >= 8:
            # Last module completed - go back to learning path
            st.session_state.current_module = None
            st.session_state.dashboard_tab = 'Learn'
            st.query_params["screen"] = "graph_new"
        st.session_state.advance_to_next = False
        st.rerun()
        return  # Stop execution after rerun

    # Show instruction if no module selected
    if not st.session_state.current_module:
        st.markdown(":material/arrow_back: **Select a module from the sidebar to begin learning**")
        return

    # FIX #2: Removed auto_open_module logic - module now set explicitly in Learn tab

    # Display module content and questions
    if st.session_state.current_module:
        module_id = st.session_state.current_module

        # Check cache first
        #cache_key = (selected_topic_id, module_id)
        cache_key = (path_id, selected_topic_id, module_id)
        if cache_key in st.session_state.module_cache:
            content_data = st.session_state.module_cache[cache_key]
        else:
            # Generate content and cache it
            # Get the module name from the names cache
            module_name = module_names.get(module_id, f"Module {module_id}")

            # Calculate depth score for personalized content
            depth_score = calculate_depth_score(
                target_seniority=target_seniority,
                initial_mastery=initial_mastery,
                module_id=module_id
            )

            # Build user context for personalized content
            user_context = None
            if path_record:
                user_context = {
                    "current_seniority": path_record.get('current_seniority', 'Intermediate'),
                    "current_job_title": path_record.get('current_job_title', 'Professional'),
                    "current_description": path_record.get('current_description', 'General background'),
                    "target_seniority": path_record.get('target_seniority', 'Advanced'),
                    "target_job_title": path_record.get('target_job_title', 'Senior Professional'),
                    "target_description": path_record.get('target_description', 'Advanced skills required'),
                    "target_company": path_record.get('target_company', 'Industry'),
                    "mastery": initial_mastery
                }

            with st.spinner(f"🤖 Generating module content..."):
                try:
                    from src.agents.content_generator import generate_content
                    content_data = generate_content(
                        topic_id=selected_topic_id,
                        module_id=module_id,
                        module_name=module_name,
                        depth_score=depth_score,
                        user_context=user_context,
                        all_module_names=module_names  # Pass all 8 module names to prevent overlap
                    )
                    st.session_state.module_cache[cache_key] = content_data
                except Exception as e:
                    st.error(f"❌ Error generating content: {e}")
                    return

        st.markdown("---")
        st.subheader(f":material/book: {content_data.get('module_name', f'Module {module_id}')}")

        # Content section
        with st.expander(":material/article: Module Content", expanded=True):
            st.markdown(content_data['content'])

        # References section
        with st.expander(":material/collections_bookmark: Learning Resources"):
            for ref in content_data['references']:
                if isinstance(ref, dict):
                    # New format with clickable URLs
                    st.markdown(f"- [{ref['text']}]({ref['url']})")
                else:
                    # Legacy string format (backward compatibility)
                    st.markdown(f"- {ref}")

        st.markdown("---")

        # FIX #3: Check if module is already completed
        module_already_completed = module_id in completed_modules

        if module_already_completed and not st.session_state.show_completion:
            # Module was completed in a previous session
            st.info(f":material/check_circle: Module {module_id} already completed!")

            if module_id < 8:
                if st.button(":material/arrow_forward: Continue to Next Module", type="primary", use_container_width=True):
                    st.session_state.current_module = module_id + 1
                    st.session_state.user_answers = {}
                    st.rerun()
            else:
                st.success(":material/emoji_events: All 8 modules completed! Great work!")
                if st.button(":material/arrow_back: Back to Learning Path", type="primary", use_container_width=True):
                    st.session_state.current_module = None
                    st.session_state.dashboard_tab = 'Learn'
                    st.query_params["screen"] = "graph_new"
                    st.rerun()
            return  # Don't show questions for already-completed modules

        # Questions section
        st.subheader(":material/quiz: Comprehension Check")
        st.caption("Answer all 3 questions correctly to earn +15% mastery")

        questions = content_data['questions']

        # Show completion message if module was just completed
        if st.session_state.show_completion and st.session_state.get('completed_module_id') == module_id:
            # Recalculate mastery for display
            completed_modules_fresh = database.get_completed_modules(user_id, path_id, selected_topic_id)
            new_completion_count = len(completed_modules_fresh)
            points_per_module = (100 - initial_mastery) / 8.0
            new_mastery_gain = new_completion_count * points_per_module
            new_mastery = min(int(initial_mastery + new_mastery_gain), 100)

            st.success(f":material/celebration: Perfect! 3/3 correct! Module {module_id} completed!")
            st.markdown(f":material/trending_up: **Mastery:** {updated_mastery}% → **{new_mastery}%** ({new_completion_count}/8 modules)")
            st.balloons()

            # Add a button to continue (gives time for balloons to show)
            if st.button(":material/arrow_forward: Continue Learning", type="primary", use_container_width=True):
                # Set flag to advance to next module on rerun
                st.session_state.advance_to_next = True
                st.rerun()

            # Stop here - don't show questions again
            return

        # # Display questions
        # for i, question in enumerate(questions, 1):
        #     st.markdown(f"**Q{i}: {question['text']}**")
        #     answer = st.text_input(
        #         "Your answer:",
        #         key=f"answer_{module_id}_{question['id']}",
        #         placeholder="Type your answer here..."
        #     )
        #     st.session_state.user_answers[question['id']] = answer
        # Display questions (supports both multiple choice and free text)
        for i, question in enumerate(questions, 1):
            st.markdown(f"**Q{i}: {question['text']}**")

            # Check if question has options (multiple choice format)
            options = question.get('options', {})

            if options and isinstance(options, dict) and len(options) == 4:
                # Multiple choice format - use radio buttons
                choice = st.radio(
                    "Select your answer:",
                    options=["A", "B", "C", "D"],
                    format_func=lambda x, opts=options: f"{x}) {opts.get(x, '')}",
                    key=f"answer_{module_id}_{question['id']}",
                    index=None,  # No default selection
                    label_visibility="collapsed"
                )
                st.session_state.user_answers[question['id']] = choice if choice else ""
            else:
                # Free text format (legacy) - use text input
                answer = st.text_input(
                    "Your answer:",
                    key=f"answer_{module_id}_{question['id']}",
                    placeholder="Type your answer here..."
                )
                st.session_state.user_answers[question['id']] = answer

            st.markdown("")  # Spacing between questions
        # Submit button
        if st.button(":material/check_circle: Submit Answers", type="primary", use_container_width=True):
            # Check if all questions are answered
            all_answered = all(
                st.session_state.user_answers.get(q['id'], "").strip()
                for q in questions
            )

            if not all_answered:
                st.warning(":material/warning: Please answer all questions before submitting.")
            else:
                # Evaluate answers using LLM
                with st.spinner(":material/psychology: Evaluating your answers..."):
                    correct_count = 0
                    results = []

                    for question in questions:
                        user_answer = st.session_state.user_answers.get(question['id'], "").strip()
                        correct_answer = question['correct_answer'].strip()

                        # Use semantic evaluation
                        is_correct = evaluate_answer(
                            user_answer=user_answer,
                            correct_answer=correct_answer,
                            question_text=question['text']
                        )

                        if is_correct:
                            correct_count += 1

                        results.append({
                            'question': question,
                            'user_answer': user_answer,
                            'is_correct': is_correct
                        })

                        # Record answer in database
                        database.record_answer(
                            user_id, path_id, selected_topic_id, module_id,
                            question['id'], user_answer, is_correct
                        )

                # Display results
                st.markdown("---")

                if correct_count == 3:
                    # All correct - mark module as complete
                    if module_id not in completed_modules:
                        # Record completion
                        database.complete_module(user_id, path_id, selected_topic_id, module_id, mastery_bonus=0)

                        # Set flag to show completion message
                        st.session_state.show_completion = True
                        st.session_state.completed_module_id = module_id
                        st.rerun()
                    else:
                        st.markdown(":material/check: **You've already completed this module!**")

                else:
                    # Some incorrect - show detailed feedback
                    st.warning(f":material/edit_note: Score: {correct_count}/3 - Review the feedback below and try again")
                    st.markdown("---")

                    for i, result in enumerate(results, 1):
                        if result['is_correct']:
                            st.success(f":material/check_circle: **Question {i}:** {result['question']['text']}")
                            st.markdown(f"**Your answer:** ✓ {result['user_answer']}")
                        else:
                            st.error(f":material/cancel: **Question {i}:** {result['question']['text']}")
                            st.markdown(f"**Your answer:** ✗ {result['user_answer']}")
                            st.markdown(f"**Correct answer:** {result['question']['correct_answer']}")
                            st.markdown(f":material/lightbulb: **Why:** {result['question']['explanation']}")
                        st.markdown("")  # Spacing

                    # Retry button
                    if st.button(":material/refresh: Try Again", type="primary", use_container_width=True):
                        st.session_state.user_answers = {}
                        st.rerun()

    else:
        st.markdown(":material/touch_app: **Select a module above to begin learning**")


# ============================================================
# ROUTING & AUTHENTICATION CHECK
# ============================================================

# Route to appropriate screen
if screen == "login":
    # Login screen (no authentication required)
    screen_0_login()
elif screen in ["my_paths", "form", "graph", "graph_new", "topics"]:
    # Protected screens - require authentication
    if not st.session_state.get('authenticated'):
        # Not authenticated - redirect to login
        st.query_params["screen"] = "login"
        st.rerun()
    else:
        # Authenticated - show requested screen
        if screen == "my_paths":
            screen_0_my_paths()
        elif screen == "form":
            # Check path limit before allowing form access
            user_id = get_current_user_id()
            path_count = database.get_path_count(user_id)
            if path_count >= 3:
                st.error("⚠️ Maximum 3 paths reached. Please resume an existing path.")
                if st.button("← Back to My Paths"):
                    st.query_params["screen"] = "my_paths"
                    st.rerun()
            else:
                screen_1_form()
        elif screen == "graph":
            screen_2_graph()
        elif screen == "graph_new":
            screen_2_new()
        elif screen == "topics":
            screen_3_topics()
else:
    # Unknown screen - redirect to login by default
    st.query_params["screen"] = "login"
    st.rerun()
