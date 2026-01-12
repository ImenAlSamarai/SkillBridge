#!/usr/bin/env python3
"""
Test improved reference system:
1. Submodule-specific (not same for all)
2. Free resources prioritized
3. Academic institutions prioritized
4. Specific video URLs (not just channel homepage)
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import generate_content

def test_improved_references():
    print("🧪 TESTING IMPROVED REFERENCE SYSTEM\n")
    print("="*80)

    test_cases = [
        {
            "name": "Neural Networks (ML topic)",
            "topic": "machine_learning",
            "module": "Neural Networks Basics",
            "expected_video": "3Blue1Brown playlist or academic course",
            "expected_book": "Free online book (Nielsen or Goodfellow)"
        },
        {
            "name": "Options Pricing (Finance topic)",
            "topic": "derivatives_pricing",
            "module": "Options Pricing Models",
            "expected_video": "MIT OCW or academic course",
            "expected_book": "Khan Academy or free course"
        },
        {
            "name": "Linear Algebra (Math topic)",
            "topic": "linear_algebra",
            "module": "Matrix Operations",
            "expected_video": "MIT Gilbert Strang or 3Blue1Brown",
            "expected_book": "Khan Academy or MIT OCW"
        }
    ]

    results = []

    for test in test_cases:
        print(f"\n📝 TEST: {test['name']}")
        print(f"   Module: {test['module']}")
        print(f"   Generating references...")

        content_data = generate_content(
            topic_id=test['topic'],
            module_id=1,
            module_name=test['module'],
            depth_score=0.5,
            user_context={
                'current_seniority': 'Junior',
                'current_job_title': 'Analyst',
                'current_description': 'Basic skills',
                'target_seniority': 'Intermediate',
                'target_job_title': 'Senior Analyst',
                'target_description': 'Advanced skills',
                'target_company': 'Tech Company',
                'mastery': 30
            }
        )

        refs = content_data['references']

        print(f"\n   📚 Generated References:")
        for i, ref in enumerate(refs, 1):
            print(f"      {i}. {ref['text']}")
            print(f"         🔗 {ref['url']}")

        # Validation
        print(f"\n   ✅ Validation:")

        # Check video
        video_ref = refs[0]
        video_url = video_ref['url'].lower()
        video_text = video_ref['text'].lower()

        is_specific = 'playlist' in video_url or 'search_query' in video_url or 'video-lectures' in video_url or 'courses' in video_url
        is_academic = any(domain in video_url for domain in ['mit.edu', 'stanford', 'harvard', 'yale', 'khanacademy', 'oyc.yale.edu'])

        # Check for trusted channels in BOTH URL and text (YouTube playlists have channel name in text, not URL)
        trusted_channels = ['3blue1brown', 'statquest', 'computerphile', 'cs50']
        is_trusted = any(channel in video_url or channel in video_text for channel in trusted_channels)

        is_not_homepage = '@' not in video_url or 'playlist' in video_url or 'search' in video_url
        is_academic_or_trusted = is_academic or is_trusted

        print(f"      Video:")
        print(f"         ✓ Specific URL (not homepage): {is_not_homepage}")
        print(f"         ✓ Academic institution: {is_academic}")
        print(f"         ✓ Trusted channel: {is_trusted}")
        print(f"         ✓ Specific content (playlist/search): {is_specific}")

        # Check book
        book_ref = refs[1]
        book_url = book_ref['url'].lower()
        book_text = book_ref['text'].lower()

        is_free = 'free' in book_text or any(domain in book_url for domain in [
            'ocw.mit.edu', 'khanacademy.org', 'deeplearningbook.org',
            'neuralnetworksanddeeplearning.com', 'd2l.ai', 'greenteapress.com',
            'mml-book.github.io', 'course.fast.ai'
        ])
        is_not_amazon = 'amazon.com' not in book_url

        print(f"      Book:")
        print(f"         ✓ FREE resource: {is_free}")
        print(f"         ✓ Not paid Amazon link: {is_not_amazon}")

        results.append({
            "name": test['name'],
            "video_specific": is_not_homepage and is_specific,
            "video_academic": is_academic or is_trusted,
            "book_free": is_free,
            "refs": refs
        })

        print("   " + "-"*76)

    # Cross-check: Different submodules should have different references
    print(f"\n\n📊 CROSS-MODULE VALIDATION:")
    print("="*80)

    all_video_urls = [r['refs'][0]['url'] for r in results]
    all_book_urls = [r['refs'][1]['url'] for r in results]

    unique_videos = len(set(all_video_urls))
    unique_books = len(set(all_book_urls))

    print(f"\n   Video References:")
    print(f"      • Total modules tested: {len(results)}")
    print(f"      • Unique video URLs: {unique_videos}")
    print(f"      • ✓ Different per module: {unique_videos == len(results)}")

    print(f"\n   Book References:")
    print(f"      • Total modules tested: {len(results)}")
    print(f"      • Unique book URLs: {unique_books}")
    print(f"      • ✓ Different per module: {unique_books == len(results)}")

    # Summary
    print(f"\n\n✅ SUMMARY:")
    print("="*80)

    all_specific = all(r['video_specific'] for r in results)
    all_academic = all(r['video_academic'] for r in results)
    all_free = all(r['book_free'] for r in results)
    all_unique = unique_videos == len(results) and unique_books == len(results)

    print(f"   ✓ All videos are specific (not homepage): {all_specific}")
    print(f"   ✓ All videos from academic/trusted sources: {all_academic}")
    print(f"   ✓ All books are FREE: {all_free}")
    print(f"   ✓ All references are unique per module: {all_unique}")

    if all_specific and all_academic and all_free and all_unique:
        print(f"\n   🎉 SUCCESS: All requirements met!")
    else:
        print(f"\n   ⚠️  ISSUES: Some requirements not met, see details above")

    print("\n")

if __name__ == "__main__":
    test_improved_references()
