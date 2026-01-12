#!/usr/bin/env python3
"""
Test that ADVANCED modules (high depth, no 'Foundations') get advanced content
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import generate_content

def test_advanced_content():
    print("🧪 ADVANCED MODULE TEST\n")
    print("="*80)
    print("Testing 'Stochastic Calculus' for Senior → Jane Street")
    print("Expected: Advanced stochastic calculus (Itô's Lemma, SDEs)")
    print("NOT: Basic calculus (simple derivatives, integrals)")
    print("="*80)

    try:
        # Generate content for Advanced Stochastic Calculus
        content_data = generate_content(
            topic_id="calculus",
            module_id=10,
            module_name="Stochastic Calculus",  # No "Foundations"
            depth_score=0.9,  # High depth = advanced
            user_context={
                'current_seniority': 'Senior',
                'current_job_title': 'Quant Researcher',
                'current_description': 'Advanced mathematical modeling',
                'target_seniority': 'Lead',
                'target_job_title': 'Lead Quant',
                'target_description': 'Leading quantitative research',
                'target_company': 'Jane Street',
                'mastery': 80  # High mastery
            }
        )

        content = content_data['content']
        print(f"\n📄 GENERATED CONTENT:\n")
        print(content[:800] + "..." if len(content) > 800 else content)
        print("\n" + "="*80)

        # Check for GOOD content (advanced stochastic calculus)
        good_terms = [
            'stochastic', 'martingale', 'brownian motion',
            "itô", 'ito', 'girsanov',
            'diffusion', 'drift', 'volatility'
        ]

        # Check for BAD content (basic calculus only)
        bad_patterns = [
            'basic derivative', 'simple integral', 'power rule',
            'what is a derivative', 'introduction to'
        ]

        content_lower = content.lower()

        good_count = sum(1 for term in good_terms if term in content_lower)
        bad_count = sum(1 for term in bad_patterns if term in content_lower)

        print(f"\n🔍 VALIDATION:")
        print(f"  Advanced stochastic terms found: {good_count}/{len(good_terms)}")
        print(f"  Basic-only patterns found: {bad_count}/{len(bad_patterns)}")

        if good_count >= 2:
            print(f"  ✅ Contains advanced stochastic concepts")
        else:
            print(f"  ❌ Missing advanced stochastic concepts")

        if bad_count == 0:
            print(f"  ✅ No overly basic content")
        else:
            print(f"  ⚠️  Contains basic-level explanations")

        # Extract section titles
        import re
        print(f"\n📋 SECTION TITLES:")
        for match in re.finditer(r'## (\d+)\. (.+)', content):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            print(f"  {section_num}. {section_title}")

        if good_count >= 2:
            print(f"\n✅ SUCCESS: Content is appropriately advanced!")
            return True
        else:
            print(f"\n❌ FAILED: Content is too basic for advanced module")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_advanced_content()
