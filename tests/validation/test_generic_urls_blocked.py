#!/usr/bin/env python3
"""
Test that generic/unverified URLs are blocked:
1. Khan Academy landing pages (not specific courses)
2. YouTube search results
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import validate_and_fix_references

def test_generic_urls_blocked():
    print("🧪 TESTING GENERIC URL BLOCKING\n")
    print("="*80)

    # Test case: The two issues user reported
    bad_references = [
        {
            "text": "Video: Khan Academy - Introduction to Stock Market",
            "url": "https://www.khanacademy.org/economics-finance-domain"
        },
        {
            "text": "YouTube Search: Stock Market Fundamentals",
            "url": "https://www.youtube.com/results?search_query=Stock+Market+Fundamentals"
        }
    ]

    print("\n📝 TEST INPUT (BAD references user reported):")
    print("\n1. Khan Academy Landing Page (NOT specific course)")
    print(f"   Text: {bad_references[0]['text']}")
    print(f"   URL: {bad_references[0]['url']}")
    print(f"   ❌ Problem: Generic landing page, not a specific course")

    print("\n2. YouTube Search Results (NOT curated content)")
    print(f"   Text: {bad_references[1]['text']}")
    print(f"   URL: {bad_references[1]['url']}")
    print(f"   ❌ Problem: Search results with random YouTube videos")

    print("\n" + "="*80)
    print("🔍 Running validation...\n")

    # Validate and fix
    validated_refs = validate_and_fix_references(
        references=bad_references,
        topic_id="derivatives_pricing",
        module_name="Stock Market Fundamentals"
    )

    print("\n" + "="*80)
    print("📚 VALIDATED REFERENCES (after fixing):")
    print("="*80)

    for i, ref in enumerate(validated_refs, 1):
        print(f"\n{i}. {ref['text']}")
        print(f"   🔗 {ref['url']}")

        # Check if bad patterns still exist
        if 'khanacademy.org/economics-finance-domain' in ref['url'] and ref['url'].count('/') == 3:
            print(f"   ❌ FAILED: Still has generic Khan Academy landing page!")
        elif 'youtube.com/results?search_query=' in ref['url']:
            print(f"   ❌ FAILED: Still has YouTube search results!")
        else:
            print(f"   ✅ SUCCESS: Replaced with curated resource")

    print("\n" + "="*80)
    print("✅ VALIDATION SUMMARY:")
    print("="*80)

    # Check that no bad patterns remain
    has_ka_landing = any(
        'khanacademy.org/economics-finance-domain' in ref['url'] and ref['url'].count('/') == 3
        for ref in validated_refs
    )
    has_youtube_search = any(
        'youtube.com/results?search_query=' in ref['url']
        for ref in validated_refs
    )

    all_clean = not (has_ka_landing or has_youtube_search)

    print(f"   • Blocked Khan Academy landing pages: {not has_ka_landing}")
    print(f"   • Blocked YouTube search results: {not has_youtube_search}")
    print(f"   • All references curated: {all_clean}")

    if all_clean:
        print(f"\n   🎉 SUCCESS: Generic/unverified URLs blocked and replaced!")
        print(f"   → Users will only see specific courses from reputable sources")
    else:
        print(f"\n   ❌ FAILURE: Some generic URLs still present")

    print("\n" + "="*80)
    print("📖 WHAT USERS WILL SEE:")
    print("="*80)

    for i, ref in enumerate(validated_refs, 1):
        print(f"\n{i}. {ref['text']}")
        print(f"   → Specific course: {'/' in ref['url'][30:] if len(ref['url']) > 30 else 'Yes'}")
        print(f"   → Curated content: {not any(bad in ref['url'] for bad in ['search_query', '/math$', '/economics-finance-domain$'])}")

    print("\n")


if __name__ == "__main__":
    test_generic_urls_blocked()
