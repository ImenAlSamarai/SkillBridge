#!/usr/bin/env python3
"""
Phase 2D End-to-End Test
Tests full workflow: Screen 1 Form → Agent 1 → Agent 2 → Database
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.workflow import run_full_workflow
from src.core import database


def get_user_path_data(user_id: int) -> dict:
    """Get user's path data from Phase 1 database"""
    paths = database.get_paths_by_user(user_id)
    if not paths:
        raise ValueError(f"No path found for user {user_id}")

    path = paths[0]

    return {
        "current_job_title": path["current_job_title"],
        "current_description": path["current_description"],
        "current_seniority": path["current_seniority"],
        "target_job_title": path["target_job_title"],
        "target_description": path["target_description"],
        "target_seniority": path["target_seniority"],
        "target_company": path["target_company"],
        "target_industry": path["target_industry"]
    }


def verify_database(user_id: int, expected_topics_count: int) -> bool:
    """Verify database was updated correctly"""
    # Check paths table
    paths = database.get_paths_by_user(user_id)
    if not paths:
        print(f"  ❌ No path found in database for user {user_id}")
        return False

    path = paths[0]
    if path["global_readiness"] == 0.0:
        print(f"  ❌ Global readiness not updated (still 0.0)")
        return False

    # Check user_skills table
    skills = database.get_user_skills(user_id)
    if len(skills) != expected_topics_count:
        print(f"  ❌ Expected {expected_topics_count} rows in user_skills, got {len(skills)}")
        return False

    print(f"  ✓ Database: {len(skills)} topics saved, {path['global_readiness']}% readiness")
    return True


def test_phase2d():
    """Test full workflow with 3 users"""
    print("Testing Phase 2D: Full Workflow (Form → Agent1 → Agent2 → DB)")
    print("=" * 70)
    print()

    # Clear existing user_skills for test users to ensure clean state
    print("Clearing existing user_skills data...")
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_skills WHERE user_id IN (1, 2, 3)")
        print(f"  Deleted {cursor.rowcount} existing rows\n")

    test_users = [1, 2, 3]
    all_passed = True

    for user_id in test_users:
        try:
            # Get user and form data
            user = database.get_user(user_id)
            if not user:
                print(f"❌ User {user_id} not found")
                all_passed = False
                continue

            form_data = get_user_path_data(user_id)

            # Run full workflow
            result = run_full_workflow(user_id, form_data)

            # Check for errors
            if result["error"]:
                print(f"❌ Workflow failed: {result['error']}")
                all_passed = False
                continue

            # Validate results
            assert result["topics_count"] >= 3, f"Expected at least 3 topics, got {result['topics_count']}"
            assert 0 <= result["global_readiness"] <= 100, f"Invalid readiness: {result['global_readiness']}"

            # Verify database was updated
            if not verify_database(user_id, result["topics_count"]):
                all_passed = False
                continue

            # User-specific validations
            if user_id == 1:
                # Student → Quant Intern: Low readiness
                assert result["global_readiness"] <= 25, f"Student should have low readiness, got {result['global_readiness']}%"

            elif user_id == 2:
                # Analyst → Researcher: Partial readiness
                assert 20 <= result["global_readiness"] <= 60, f"Analyst should have partial readiness, got {result['global_readiness']}%"

            elif user_id == 3:
                # ML → Quant: Has high-mastery topics
                high_mastery_topics = [t for t in result["assessed_topics"] if t["mastery"] >= 60]
                assert len(high_mastery_topics) >= 1, f"ML Engineer should have at least one high-mastery topic"

            print(f"  ✓ All validations passed for User {user_id}")
            print()

        except AssertionError as e:
            print(f"  ❌ Validation failed: {e}")
            import traceback
            traceback.print_exc()
            print()
            all_passed = False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print()
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("✅ PHASE 2D COMPLETE")
        print("\nFull Pipeline Test Results:")
        print("  User 1 ✓ (Form → Topics → Mastery → DB)")
        print("  User 2 ✓ (Form → Topics → Mastery → DB)")
        print("  User 3 ✓ (Form → Topics → Mastery → DB)")
        print("\nSINGLE COMMAND = Complete learning path from form input")
        print("Database: paths + user_skills tables populated")
        print("Ready for Screen 2 Graph visualization")
        return True
    else:
        print("❌ PHASE 2D FAILED - Some tests did not pass")
        return False


if __name__ == "__main__":
    success = test_phase2d()
    sys.exit(0 if success else 1)
