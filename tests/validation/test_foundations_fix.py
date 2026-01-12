#!/usr/bin/env python3
"""
Test that "Foundations" modules teach BASICS, not advanced topics
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.content_generator import generate_content

def test_foundations_content():
    print("🧪 FOUNDATIONS MODULE TEST\n")
    print("="*80)
    print("Testing 'Calculus Foundations' for undergrad → Jane Street")
    print("Expected: Basic calculus (derivatives, integrals, limits)")
    print("NOT: Stochastic calculus (Itô's Lemma, SDEs)")
    print("="*80)

    try:
        # Generate content for Calculus Foundations
        content_data = generate_content(
            topic_id="calculus",
            module_id=1,
            module_name="Calculus Foundations",
            depth_score=0.2,  # Low depth = foundational
            user_context={
                'current_seniority': 'Undergrad',
                'current_job_title': 'Student',
                'current_description': 'Learning fundamentals',
                'target_seniority': 'Junior',
                'target_job_title': 'Quant Researcher',
                'target_description': 'Quantitative research',
                'target_company': 'Jane Street',
                'mastery': 10  # Low mastery
            }
        )

        content = content_data['content']
        print(f"\n📄 GENERATED CONTENT:\n")
        print(content)
        print("\n" + "="*80)

        # Check for GOOD content (basic calculus)
        good_terms = [
            'derivative', 'derivatives', 'differentiation',
            'integral', 'integration',
            'limit', 'limits',
            'chain rule', 'product rule', 'quotient rule',
            'fundamental theorem'
        ]

        # Check for BAD content (advanced stochastic calculus)
        bad_terms = [
            'stochastic process', 'stochastic calculus',
            "itô's lemma", 'ito lemma',
            'wiener process', 'brownian motion',
            'stochastic differential equation', 'sde'
        ]

        content_lower = content.lower()

        good_count = sum(1 for term in good_terms if term in content_lower)
        bad_count = sum(1 for term in bad_terms if term in content_lower)

        print(f"\n🔍 VALIDATION:")
        print(f"  Basic calculus terms found: {good_count}/{len(good_terms)}")
        print(f"  Advanced stochastic terms found: {bad_count}/{len(bad_terms)}")

        if good_count >= 3:
            print(f"  ✅ Contains basic calculus concepts")
        else:
            print(f"  ❌ Missing basic calculus concepts")
            print(f"     Found terms: {[t for t in good_terms if t in content_lower]}")

        if bad_count == 0:
            print(f"  ✅ No advanced stochastic calculus")
        else:
            print(f"  ❌ Contains advanced stochastic calculus!")
            print(f"     Found terms: {[t for t in bad_terms if t in content_lower]}")

        # Extract section titles
        import re
        print(f"\n📋 SECTION TITLES:")
        for match in re.finditer(r'## (\d+)\. (.+)', content):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            print(f"  {section_num}. {section_title}")

        if good_count >= 3 and bad_count == 0:
            print(f"\n✅ SUCCESS: Content is appropriate for Calculus Foundations!")
            return True
        else:
            print(f"\n❌ FAILED: Content is not appropriate for foundational module")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_foundations_content()
