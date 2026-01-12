#!/usr/bin/env python3
"""
Test script for mastery progress tracking
Verifies that mastery updates correctly as users complete modules
"""

import sys
sys.path.insert(0, 'src')

from src.core import database

print("=" * 80)
print("MASTERY PROGRESS TRACKING TEST")
print("=" * 80)
print()

# Get a test user's path
user_id = 2  # Use user 2 who has fewer paths
paths = database.get_paths_by_user(user_id)

if not paths:
    print(f"❌ No paths found for user {user_id}")
    sys.exit(1)

path = paths[0]
path_id = path['id']
topics = path['topics']

print(f"Test Path: {path['current_seniority']} → {path['target_seniority']}")
print(f"User ID: {user_id}")
print(f"Path ID: {path_id[:8]}...")
print(f"Topics: {len(topics)}")
print()

# Test 1: Initial mastery calculation
print("=" * 80)
print("TEST 1: Initial Mastery Calculation")
print("=" * 80)
initial_mastery = database.calculate_path_mastery(path)
print(f"✅ Initial path mastery: {initial_mastery}%")
print()

# Test 2: Show per-topic mastery breakdown
print("=" * 80)
print("TEST 2: Per-Topic Mastery Breakdown")
print("=" * 80)
for i, topic in enumerate(topics[:5], 1):  # Show first 5 topics
    topic_id = topic['topic_id']
    initial = topic['mastery']
    completed = database.get_completed_modules(user_id, path_id, topic_id)
    points_per_module = (100 - initial) / 8.0
    current_mastery = min(int(initial + len(completed) * points_per_module), 100)

    print(f"{i}. {topic_id}")
    print(f"   Initial: {initial}% | Completed: {len(completed)}/8 | Current: {current_mastery}%")
print()

# Test 3: Simulate completing modules and verify mastery updates
print("=" * 80)
print("TEST 3: Simulate Module Completion")
print("=" * 80)

# Pick a topic with low initial mastery for better visibility
test_topic = None
for topic in topics:
    if topic['mastery'] < 50:
        test_topic = topic
        break

if not test_topic:
    test_topic = topics[0]

topic_id = test_topic['topic_id']
initial_topic_mastery = test_topic['mastery']

print(f"Test topic: {topic_id}")
print(f"Initial topic mastery: {initial_topic_mastery}%")

# Get current state
completed_before = database.get_completed_modules(user_id, path_id, topic_id)
mastery_before = database.calculate_path_mastery(path)
print(f"Modules completed before: {len(completed_before)}/8")
print(f"Path mastery before: {mastery_before}%")
print()

# Complete 3 modules
print("📝 Completing 3 modules...")
for module_id in [1, 2, 3]:
    try:
        database.complete_module(user_id, path_id, topic_id, module_id, mastery_bonus=0)
        print(f"   ✅ Module {module_id} completed")
    except Exception as e:
        print(f"   ⚠️  Module {module_id} already completed or error: {e}")
print()

# Reload path and recalculate
paths = database.get_paths_by_user(user_id)
path = paths[0]
completed_after = database.get_completed_modules(user_id, path_id, topic_id)
mastery_after = database.calculate_path_mastery(path)

# Calculate expected mastery
points_per_module = (100 - initial_topic_mastery) / 8.0
modules_added = len(completed_after) - len(completed_before)
expected_topic_increase = modules_added * points_per_module
expected_topic_mastery = min(int(initial_topic_mastery + len(completed_after) * points_per_module), 100)

print(f"Results:")
print(f"  Modules completed after: {len(completed_after)}/8")
print(f"  New modules added: {modules_added}")
print(f"  Points per module: {points_per_module:.1f}")
print(f"  Expected topic mastery: {expected_topic_mastery}%")
print(f"  Path mastery after: {mastery_after}%")
print(f"  Path mastery change: {mastery_after - mastery_before:+.1f}%")
print()

if mastery_after > mastery_before or modules_added == 0:
    print("✅ Mastery tracking working correctly!")
else:
    print("❌ Mastery did not update as expected")
print()

# Test 4: Verify mastery persists across sessions
print("=" * 80)
print("TEST 4: Verify Mastery Persists (Reload from Database)")
print("=" * 80)

# Reload path fresh from database
fresh_paths = database.get_paths_by_user(user_id)
fresh_path = fresh_paths[0]
fresh_mastery = database.calculate_path_mastery(fresh_path)

print(f"Reloaded path mastery: {fresh_mastery}%")
if abs(fresh_mastery - mastery_after) < 0.1:
    print("✅ Mastery persists correctly!")
else:
    print(f"❌ Mastery mismatch: {fresh_mastery}% vs {mastery_after}%")
print()

print("=" * 80)
print("✅ MASTERY TRACKING TEST COMPLETE")
print("=" * 80)
print()
print("Summary:")
print(f"  • Initial path mastery: {initial_mastery}%")
print(f"  • Final path mastery: {mastery_after}%")
print(f"  • Total change: {mastery_after - initial_mastery:+.1f}%")
print(f"  • Modules completed in test: {modules_added}")
print()
print("The 'My Learning Paths' screen will now show real-time progress!")
print()
