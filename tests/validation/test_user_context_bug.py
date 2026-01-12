#!/usr/bin/env python3
"""
Test to reproduce the user context bug
Expected: "Student → Junior Quant Researcher @ Jane Street"
Actual: "Intermediate Professional → Advanced Senior Professional @ Industry"
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import generate_content
from src.core import database

def test_user_context_propagation():
    """
    Reproduce the exact scenario: Student → Junior Quant Researcher @ Jane Street
    """

    print("🐛 TESTING USER CONTEXT BUG REPRODUCTION\n")
    print("="*80)

    # Get Alex Student from database (User 1)
    user = database.get_user(1)
    paths = database.get_paths_by_user(1)

    if not paths:
        print("❌ No path found for user 1")
        return

    path = paths[0]

    print("👤 USER FROM DATABASE:")
    print(f"   Name: {user['name']}")
    print(f"   Current: {path['current_seniority']} {path['current_job_title']}")
    print(f"   Target: {path['target_seniority']} {path['target_job_title']} @ {path['target_company']}")
    print(f"   Description: {path['current_description'][:80]}...")

    # Build user context exactly as app.py should
    user_context = {
        "current_seniority": path['current_seniority'],
        "current_job_title": path['current_job_title'],
        "current_description": path['current_description'],
        "target_seniority": path['target_seniority'],
        "target_job_title": path['target_job_title'],
        "target_description": path['target_description'],
        "target_company": path['target_company'],
        "mastery": 15  # From topic assessor
    }

    print("\n📝 USER CONTEXT DICT:")
    for key, value in user_context.items():
        if key == 'current_description' or key == 'target_description':
            print(f"   {key}: {value[:60]}...")
        else:
            print(f"   {key}: {value}")

    print("\n🤖 Generating content with this context...\n")

    content_data = generate_content(
        topic_id="derivatives_pricing",
        module_id=1,
        module_name="Derivatives Basics",
        depth_score=0.22,
        user_context=user_context
    )

    print("="*80)
    print("📖 GENERATED CONTENT - OVERVIEW SECTION")
    print("="*80)

    # Extract just the overview section
    content = content_data['content']
    overview_end = content.find('## 2.')
    if overview_end == -1:
        overview = content[:500]
    else:
        overview = content[:overview_end]

    print(overview)
    print("\n" + "="*80)

    # Validate
    print("\n✅ VALIDATION:")

    content_lower = content.lower()

    has_student = "student" in content_lower
    has_quant_researcher = "quant researcher" in content_lower
    has_jane_street = "jane street" in content_lower
    has_generic_professional = "intermediate professional" in content_lower or "advanced senior professional" in content_lower
    has_generic_industry = content_lower.count("industry") > 0 and "@ industry" in content_lower

    print(f"   ✓ Mentions 'Student': {has_student}")
    print(f"   ✓ Mentions 'Quant Researcher': {has_quant_researcher}")
    print(f"   ✓ Mentions 'Jane Street': {has_jane_street}")
    print(f"   ✗ Uses 'Intermediate Professional' (generic): {has_generic_professional}")
    print(f"   ✗ Uses '@ Industry' (generic): {has_generic_industry}")

    print("\n" + "="*80)

    if has_student and has_quant_researcher and has_jane_street and not has_generic_professional and not has_generic_industry:
        print("✅ SUCCESS: User context correctly propagated!")
        print("   → Content mentions actual roles and company")
    else:
        print("❌ FAILURE: User context NOT propagated correctly!")
        if has_generic_professional or has_generic_industry:
            print("   → Still using generic fallback values")
            print("   → BUG: user_context not being used in prompt")
        if not has_student or not has_quant_researcher or not has_jane_street:
            print("   → Missing actual user details")
            print(f"   → Student: {has_student}, Quant Researcher: {has_quant_researcher}, Jane Street: {has_jane_street}")

    print("\n")

if __name__ == "__main__":
    test_user_context_propagation()
