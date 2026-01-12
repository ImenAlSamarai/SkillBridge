#!/usr/bin/env python3
"""
Test Topic Assessor Agent - Mastery Adaptation for Different Users
Tests how mastery estimation adapts to different skill levels and backgrounds
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


import json
from src.core import database
from src.agents.topic_assessor import assess_topics

def print_separator():
    print("\n" + "="*80 + "\n")

def test_topic_assessor_adaptation():
    """Test mastery adaptation across 5 different user profiles"""

    print("🧪 TESTING TOPIC ASSESSOR - Mastery Adaptation\n")
    print("Testing how mastery estimation adapts to different backgrounds:")
    print_separator()

    # Test topics - mix of technical skills
    test_topics = [
        {"id": "linear_algebra", "prereq": None, "difficulty": "foundational"},
        {"id": "python_programming", "prereq": None, "difficulty": "foundational"},
        {"id": "machine_learning", "prereq": "python_programming", "difficulty": "intermediate"},
        {"id": "derivatives_pricing", "prereq": "linear_algebra", "difficulty": "intermediate"},
        {"id": "stochastic_calculus", "prereq": "derivatives_pricing", "difficulty": "advanced"}
    ]

    print(f"📋 Test Topics ({len(test_topics)} topics):")
    for t in test_topics:
        print(f"   • {t['id']} ({t['difficulty']})")
    print_separator()

    # Get all 5 test users from database
    users = []
    for user_id in range(1, 6):
        user_data = database.get_user(user_id)
        if user_data:
            # Get their path
            paths = database.get_paths_by_user(user_id)
            if paths:
                path = paths[0]  # Most recent
                users.append({
                    "user_id": user_id,
                    "name": user_data['name'],
                    "current_title": path['current_job_title'],
                    "current_desc": path['current_description'],
                    "current_seniority": path['current_seniority'],
                    "target_title": path['target_job_title'],
                    "target_seniority": path['target_seniority']
                })

    if not users:
        print("❌ No test users found in database!")
        print("Run: python scripts/populate_test_data.py --all")
        return

    print(f"✅ Found {len(users)} test users\n")

    # Test each user
    results = []

    for user in users:
        print(f"👤 USER {user['user_id']}: {user['name']}")
        print(f"   Current: {user['current_seniority']} {user['current_title']}")
        print(f"   Target:  {user['target_seniority']} {user['target_title']}")
        print(f"   Skills:  {user['current_desc'][:80]}...")

        # Build context
        current_context = f"{user['current_seniority']} {user['current_title']}: {user['current_desc']}"

        # Call topic assessor
        try:
            assessed = assess_topics(
                user_id=user['user_id'],
                topics=test_topics.copy(),
                current_job_context=current_context
            )

            results.append({
                "user": user,
                "assessed_topics": assessed
            })

            print(f"\n   📊 Mastery Estimates:")
            for topic in assessed:
                topic_id = topic['topic_id']
                mastery = topic['mastery']
                hours = topic['estimated_hours']
                subtopics_count = len(topic.get('subtopics', []))

                # Color code mastery
                if mastery >= 70:
                    status = "🟢"
                elif mastery >= 40:
                    status = "🟡"
                elif mastery >= 20:
                    status = "🟠"
                else:
                    status = "🔴"

                print(f"      {status} {topic_id:<25} {mastery:>3}%  |  {hours:>2}h  |  {subtopics_count} subtopics")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print_separator()

    # Comparison analysis
    print("\n📈 COMPARATIVE ANALYSIS\n")

    # For each topic, show mastery across all users
    for topic in test_topics:
        topic_id = topic['id']
        print(f"\n🎯 {topic_id.upper()}")
        print(f"   {'User':<20} {'Background':<30} {'Mastery':<10} {'Hours'}")
        print(f"   {'-'*20} {'-'*30} {'-'*10} {'-'*5}")

        for result in results:
            user = result['user']
            assessed = next((t for t in result['assessed_topics'] if t['topic_id'] == topic_id), None)

            if assessed:
                background = f"{user['current_seniority']} {user['current_title'][:15]}"
                mastery = assessed['mastery']
                hours = assessed['estimated_hours']

                # Visual bar
                bar_length = int(mastery / 5)
                bar = "█" * bar_length + "░" * (20 - bar_length)

                print(f"   {user['name']:<20} {background:<30} {mastery:>3}% {bar} {hours:>3}h")

    print("\n" + "="*80)
    print("\n✅ Test Complete!")
    print("\n💡 Key Questions:")
    print("   1. Does mastery adapt to user background?")
    print("   2. Do students get lower mastery than professionals?")
    print("   3. Do ML engineers get higher mastery for ML/Python topics?")
    print("   4. Are hours inversely correlated with mastery?")
    print("   5. Are subtopics relevant to the user's level?")
    print("\n")

if __name__ == "__main__":
    test_topic_assessor_adaptation()
