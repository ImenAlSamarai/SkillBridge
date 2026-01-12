#!/usr/bin/env python3
"""
Quick test to verify content structure has NO Overview/Summary sections
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import generate_content

def test_content_structure():
    print("🧪 CONTENT STRUCTURE TEST\n")
    print("="*80)
    print("Testing that content has NO Overview/Summary sections...")
    print("="*80)

    try:
        # Generate content for one module
        content_data = generate_content(
            topic_id="derivatives_pricing",
            module_id=1,
            module_name="Options Pricing Models",
            depth_score=0.5,
            user_context={
                'current_seniority': 'Junior',
                'current_job_title': 'Analyst',
                'current_description': 'Basic skills',
                'target_seniority': 'Senior',
                'target_job_title': 'Senior Analyst',
                'target_description': 'Advanced skills',
                'target_company': 'Tech Company',
                'mastery': 30
            }
        )

        content = content_data['content']
        print(f"\n📄 GENERATED CONTENT:\n")
        print(content)
        print("\n" + "="*80)

        # Check for Overview/Summary sections
        has_overview = "## 1. Overview" in content or "##1. Overview" in content
        has_summary = "## 5. Summary" in content or "##5. Summary" in content

        print(f"\n🔍 VALIDATION:")
        print(f"  {'❌' if has_overview else '✅'} No 'Overview' section: {not has_overview}")
        print(f"  {'❌' if has_summary else '✅'} No 'Summary' section: {not has_summary}")

        # Count sections
        import re
        sections = re.findall(r'## \d+\.', content)
        num_sections = len(sections)
        print(f"  {'✅' if 3 <= num_sections <= 4 else '❌'} Has 3-4 sections: {num_sections} sections found")

        # Extract section titles
        print(f"\n📋 SECTION TITLES:")
        for match in re.finditer(r'## (\d+)\. (.+)', content):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            print(f"  {section_num}. {section_title}")

        if has_overview or has_summary or num_sections > 4:
            print(f"\n❌ FAILED: Content structure not correct")
            return False
        else:
            print(f"\n✅ SUCCESS: Content structure is correct!")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_content_structure()
