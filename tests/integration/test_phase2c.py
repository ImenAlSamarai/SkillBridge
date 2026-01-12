#!/usr/bin/env python3
"""
Phase 2C Validation Test
Tests Topic Assessor Agent with 3 test cases
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.job_parser import parse_jobs
from src.agents.topic_assessor import assess_topics, calculate_global_readiness
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


def test_phase2c():
    """Test Topic Assessor Agent with 3 test cases"""
    print("Testing Phase 2C: Topic Breakdown + Skill Assessment")
    print("=" * 70)
    print()

    test_users = [1, 2, 3]  # Student, Analyst, ML Engineer
    all_passed = True

    for user_id in test_users:
        try:
            # Get user data
            user = database.get_user(user_id)
            if not user:
                print(f"❌ User {user_id} not found")
                all_passed = False
                continue

            form_data = get_user_path_data(user_id)

            # Phase 2B: Parse jobs to get topics
            print(f"User {user_id} ({user['name']}):")
            print(f"  Path: {form_data['current_seniority']} {form_data['current_job_title']} → "
                  f"{form_data['target_seniority']} {form_data['target_job_title']}")

            topics = parse_jobs(user_id, form_data)
            print(f"  Phase 2B: {len(topics)} topics generated")

            # Phase 2C: Assess topics (breakdown into subtopics)
            # Pass current job context for better mastery estimation
            current_context = f"{form_data['current_seniority']} {form_data['current_job_title']}: {form_data['current_description']}"
            assessed_topics = assess_topics(user_id, topics, current_context)
            print(f"  Phase 2C: {len(assessed_topics)} topics assessed")

            # Calculate global readiness
            global_readiness = calculate_global_readiness(assessed_topics)
            print(f"  Global readiness: {global_readiness}%")

            # Display sample topic
            if assessed_topics:
                sample = assessed_topics[0]
                print(f"  Sample topic: {sample['topic_id']}")
                print(f"    - Mastery: {sample['mastery']}%")
                print(f"    - Est. hours: {sample['estimated_hours']}h")
                print(f"    - Subtopics: {len(sample['subtopics'])}")

            # Validation checks
            assert len(assessed_topics) >= 3, f"Need at least 3 topics, got {len(assessed_topics)}"

            for topic in assessed_topics:
                assert "topic_id" in topic, "Missing topic_id"
                assert "mastery" in topic, "Missing mastery"
                assert "modules_complete" in topic, "Missing modules_complete"
                assert "estimated_hours" in topic, "Missing estimated_hours"
                assert "subtopics" in topic, "Missing subtopics"

                # Validate ranges
                assert 0 <= topic["mastery"] <= 100, f"Invalid mastery: {topic['mastery']}"
                assert topic["estimated_hours"] > 0, f"Invalid hours: {topic['estimated_hours']}"
                assert 3 <= len(topic["subtopics"]) <= 8, f"Expected 3-8 subtopics, got {len(topic['subtopics'])}"

            # User-specific validations
            if user_id == 1:
                # Student → Quant Intern: Low mastery (0-20%)
                assert global_readiness <= 25, f"Student should have low readiness, got {global_readiness}%"

            elif user_id == 2:
                # Analyst → Researcher: Partial mastery (20-50%)
                assert 20 <= global_readiness <= 60, f"Analyst should have partial readiness, got {global_readiness}%"

            elif user_id == 3:
                # ML → Quant: Has some high-mastery topics (e.g., Python 70%) even if global readiness is low
                # due to many advanced finance topics being new
                assert any(t["mastery"] >= 60 for t in assessed_topics), f"ML Engineer should have at least one high-mastery topic (≥60%), got: {[t['mastery'] for t in assessed_topics[:5]]}"

            print(f"  ✓ All validations passed")
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
        print("✅ PHASE 2C COMPLETE")
        print("\nResults Summary:")
        print("  User 1 ✓ (Student → Quant)")
        print("  User 2 ✓ (Analyst → Researcher)")
        print("  User 3 ✓ (ML → Quant Trader)")
        print("\nDatabase ready for Screen 2 Graph visualization")
        return True
    else:
        print("❌ PHASE 2C FAILED - Some tests did not pass")
        return False


if __name__ == "__main__":
    success = test_phase2c()
    sys.exit(0 if success else 1)
