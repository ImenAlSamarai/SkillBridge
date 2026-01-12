#!/usr/bin/env python3
"""
Test script to verify Dashboard updates after module completion
Simulates: Complete module → Return to Dashboard → Check if mastery updated
"""

import sys
sys.path.insert(0, 'src')

from src.core import database

print("=" * 80)
print("DASHBOARD UPDATE TEST")
print("=" * 80)
print()

# Use user 2 for testing
user_id = 2
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
print()

# Find a topic with few completed modules
test_topic = None
for topic in topics:
    topic_id = topic['topic_id']
    completed_modules = database.get_completed_modules(user_id, path_id, topic_id)
    if len(completed_modules) < 5:
        test_topic = topic
        test_topic_id = topic_id
        test_completed = completed_modules
        break

if not test_topic:
    print("❌ No suitable topic found for testing")
    sys.exit(1)

print(f"Test Topic: {test_topic_id}")
print(f"Initial mastery: {test_topic['mastery']}%")
print(f"Completed modules before: {len(test_completed)}/8")
print()

# STEP 1: Calculate Dashboard mastery BEFORE completing a module
print("=" * 80)
print("STEP 1: Dashboard View (Before Module Completion)")
print("=" * 80)

topic_masteries_before = []
for topic in topics:
    topic_id = topic['topic_id']
    initial_mastery = topic.get('mastery', 0)
    completed_modules = database.get_completed_modules(user_id, path_id, topic_id)
    points_per_module = (100 - initial_mastery) / 8.0
    mastery_from_modules = len(completed_modules) * points_per_module
    updated_mastery = min(int(initial_mastery + mastery_from_modules), 100)
    topic_masteries_before.append(updated_mastery)

avg_mastery_before = sum(topic_masteries_before) / len(topic_masteries_before)
print(f"Dashboard Average Mastery: {avg_mastery_before:.1f}%")
print()

# STEP 2: User completes a new module
print("=" * 80)
print("STEP 2: User Completes a Module")
print("=" * 80)

# Find next uncompleted module
next_module = len(test_completed) + 1
if next_module > 8:
    print("⚠️  All modules already completed for this topic")
    sys.exit(0)

print(f"Completing Module {next_module} for topic '{test_topic_id}'...")
try:
    database.complete_module(user_id, path_id, test_topic_id, next_module, mastery_bonus=0)
    print(f"✅ Module {next_module} marked as complete in database")
except Exception as e:
    print(f"⚠️  Module may already be completed: {e}")
print()

# STEP 3: Verify database was updated
print("=" * 80)
print("STEP 3: Verify Database Updated")
print("=" * 80)

completed_modules_after = database.get_completed_modules(user_id, path_id, test_topic_id)
print(f"Completed modules after: {len(completed_modules_after)}/8")
print(f"Modules: {completed_modules_after}")

if len(completed_modules_after) > len(test_completed):
    print("✅ Database updated successfully")
else:
    print("⚠️  Database not updated (module may have already been completed)")
print()

# STEP 4: Calculate Dashboard mastery AFTER completing the module
# This simulates what happens when user clicks "Back to Dashboard"
print("=" * 80)
print("STEP 4: Dashboard View (After Module Completion)")
print("=" * 80)

# Reload path from database (simulating what happens on dashboard reload)
paths_fresh = database.get_paths_by_user(user_id)
path_fresh = paths_fresh[0]
topics_fresh = path_fresh['topics']

topic_masteries_after = []
for topic in topics_fresh:
    topic_id = topic['topic_id']
    initial_mastery = topic.get('mastery', 0)
    completed_modules = database.get_completed_modules(user_id, path_id, topic_id)
    points_per_module = (100 - initial_mastery) / 8.0
    mastery_from_modules = len(completed_modules) * points_per_module
    updated_mastery = min(int(initial_mastery + mastery_from_modules), 100)
    topic_masteries_after.append(updated_mastery)

    # Print detail for test topic
    if topic_id == test_topic_id:
        print(f"Test Topic '{test_topic_id}':")
        print(f"  Initial mastery: {initial_mastery}%")
        print(f"  Completed modules: {len(completed_modules)}/8")
        print(f"  Points per module: {points_per_module:.1f}")
        print(f"  Updated mastery: {updated_mastery}%")
        print()

avg_mastery_after = sum(topic_masteries_after) / len(topic_masteries_after)
print(f"Dashboard Average Mastery: {avg_mastery_after:.1f}%")
print(f"Change: {avg_mastery_after - avg_mastery_before:+.1f}%")
print()

# STEP 5: Verify Dashboard shows updated mastery
print("=" * 80)
print("RESULT")
print("=" * 80)

if abs(avg_mastery_after - avg_mastery_before) < 0.1:
    print("❌ FAIL: Dashboard mastery did not update (no change)")
    print(f"   Before: {avg_mastery_before:.1f}%")
    print(f"   After: {avg_mastery_after:.1f}%")
    print()
    print("Possible causes:")
    print("  1. Module was already completed")
    print("  2. Dashboard not querying database correctly")
else:
    print("✅ PASS: Dashboard mastery updated correctly!")
    print(f"   Before: {avg_mastery_before:.1f}%")
    print(f"   After: {avg_mastery_after:.1f}%")
    print(f"   Change: {avg_mastery_after - avg_mastery_before:+.1f}%")
print()
