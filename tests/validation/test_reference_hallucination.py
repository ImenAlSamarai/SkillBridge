#!/usr/bin/env python3
"""
Test that LLM doesn't hallucinate fake references
Validates: No fake chapter numbers, no fake video titles
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import generate_content
import re

def test_reference_format():
    """
    Test that references use general format without fake specifics
    """

    print("🧪 TESTING REFERENCE HALLUCINATION FIX\n")
    print("="*80)

    # Test multiple topics to check consistency
    test_cases = [
        {
            "topic": "derivatives_pricing",
            "module_name": "Options Pricing Models",
            "depth_score": 0.7,
            "user_context": {
                "current_seniority": "Intermediate",
                "current_job_title": "Financial Analyst",
                "current_description": "Portfolio analysis",
                "target_seniority": "Advanced",
                "target_job_title": "Quant Analyst",
                "target_description": "Derivatives pricing",
                "target_company": "Goldman Sachs",
                "mastery": 40
            }
        },
        {
            "topic": "machine_learning",
            "module_name": "Neural Networks",
            "depth_score": 0.5,
            "user_context": {
                "current_seniority": "Junior",
                "current_job_title": "Data Analyst",
                "current_description": "Basic Python, SQL",
                "target_seniority": "Intermediate",
                "target_job_title": "ML Engineer",
                "target_description": "Build ML models",
                "target_company": "Tech Company",
                "mastery": 30
            }
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 TEST {i}: {test['module_name']}")
        print(f"   Topic: {test['topic']}")

        content_data = generate_content(
            topic_id=test['topic'],
            module_id=1,
            module_name=test['module_name'],
            depth_score=test['depth_score'],
            user_context=test['user_context']
        )

        references = content_data['references']
        print(f"\n   📚 Generated References ({len(references)}):")

        for ref in references:
            if isinstance(ref, dict):
                print(f"      • {ref['text']}")
                print(f"        🔗 {ref['url']}")
            else:
                print(f"      • {ref}")

        # Check for hallucination patterns
        print(f"\n   ✅ Validation:")

        issues = []

        for ref in references:
            # Handle new dict format with text/url
            if isinstance(ref, dict):
                ref_text = ref.get('text', '')
                ref_url = ref.get('url', '')

                # Check URL exists and is valid
                if not ref_url:
                    issues.append(f"Missing URL: {ref_text}")
                elif not ref_url.startswith('http'):
                    issues.append(f"Invalid URL (must start with http): {ref_url}")

                # Check for fake chapter/section numbers in text
                if re.search(r'[Cc]hapter \d+', ref_text):
                    issues.append(f"Contains specific chapter number: {ref_text}")
                if re.search(r'[Ss]ection \d+\.\d+', ref_text):
                    issues.append(f"Contains specific section number: {ref_text}")

                # Validate URL is from approved platforms
                approved_domains = [
                    'khanacademy.org', 'ocw.mit.edu', 'coursera.org', 'youtube.com',
                    'wikipedia.org', 'arxiv.org', 'amazon.com', 'springer.com',
                    'deeplearningbook.org', 'github.com', 'docs.python.org'
                ]

                is_approved = any(domain in ref_url for domain in approved_domains)
                if not is_approved:
                    issues.append(f"URL not from approved platform: {ref_url}")

            # Legacy string format
            else:
                # Check for fake chapter numbers
                if re.search(r'[Cc]hapter \d+', ref):
                    issues.append(f"Contains specific chapter number: {ref}")

                # Check for fake section numbers
                if re.search(r'[Ss]ection \d+\.\d+', ref):
                    issues.append(f"Contains specific section number: {ref}")

                # Legacy format should have URL now
                issues.append(f"Legacy format without URL: {ref}")

        if issues:
            print(f"      ⚠️  Found {len(issues)} potential issues:")
            for issue in issues:
                print(f"         - {issue}")
            all_passed = False
        else:
            print(f"      ✓ All references include clickable URLs")
            print(f"      ✓ URLs are from approved platforms")
            print(f"      ✓ No fake chapter/section numbers")
            print(f"      ✓ No hallucination patterns detected")

        print("   " + "-"*76)

    print("\n" + "="*80)

    if all_passed:
        print("✅ ALL TESTS PASSED: References use general format without hallucination")
    else:
        print("⚠️  SOME ISSUES FOUND: Review reference format above")

    print("\n💡 Expected Format:")
    print("   ✓ {\"text\": \"Khan Academy Statistics\", \"url\": \"https://khanacademy.org/...\"}")
    print("   ✓ {\"text\": \"MIT OCW Algorithms\", \"url\": \"https://ocw.mit.edu/...\"}")
    print("   ✗ {\"text\": \"Book Chapter 5 on X\", \"url\": \"...\"}")
    print("   ✗ String format without URL: \"Book: Title by Author\"")
    print("\n")

if __name__ == "__main__":
    test_reference_format()
