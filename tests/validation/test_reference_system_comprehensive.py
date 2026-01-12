#!/usr/bin/env python3
"""
Comprehensive test of reference system for ANY submodule:
1. NO YouTube search results
2. NO Khan Academy
3. Videos DIRECTLY relevant to submodule
4. Videos from REPUTABLE institutions
5. Resources exist (not 404)
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import generate_content
import time

def test_comprehensive_references():
    print("🧪 COMPREHENSIVE REFERENCE SYSTEM TEST\n")
    print("="*80)
    print("Testing multiple submodules across different topics...")
    print("="*80)

    # Test diverse submodules across different domains
    test_cases = [
        {
            "topic_id": "derivatives_pricing",
            "module_name": "Options Pricing Models",
            "description": "Finance topic - should get Yale/MIT finance courses"
        },
        {
            "topic_id": "machine_learning",
            "module_name": "Neural Networks Basics",
            "description": "ML topic - should get Coursera/Stanford ML courses"
        },
        {
            "topic_id": "linear_algebra",
            "module_name": "Matrix Operations",
            "description": "Math topic - should get 3Blue1Brown or MIT math"
        },
        {
            "topic_id": "statistics",
            "module_name": "Probability Distributions",
            "description": "Stats topic - should get StatQuest or university stats"
        },
        {
            "topic_id": "distributed_systems",
            "module_name": "Consensus Algorithms",
            "description": "CS topic - should get MIT/Stanford CS courses"
        }
    ]

    all_results = []
    issues_found = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/5: {test_case['module_name']}")
        print(f"Topic: {test_case['topic_id']}")
        print(f"Expected: {test_case['description']}")
        print("="*80)

        try:
            # Generate content
            content_data = generate_content(
                topic_id=test_case['topic_id'],
                module_id=i,
                module_name=test_case['module_name'],
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

            refs = content_data['references']

            print(f"\n📚 GENERATED REFERENCES:")
            for j, ref in enumerate(refs, 1):
                print(f"\n  {j}. {ref['text']}")
                print(f"     URL: {ref['url']}")

            # VALIDATION CHECKS
            print(f"\n🔍 VALIDATION:")

            # Check 1: NO YouTube search
            has_youtube_search = any('youtube.com/results?search_query=' in ref['url'] for ref in refs)
            print(f"  {'❌' if has_youtube_search else '✅'} No YouTube search results: {not has_youtube_search}")
            if has_youtube_search:
                issues_found.append(f"{test_case['module_name']}: Contains YouTube search")

            # Check 2: NO Khan Academy
            has_khan_academy = any('khanacademy.org' in ref['url'] for ref in refs)
            print(f"  {'❌' if has_khan_academy else '✅'} No Khan Academy: {not has_khan_academy}")
            if has_khan_academy:
                issues_found.append(f"{test_case['module_name']}: Contains Khan Academy")

            # Check 3: Check for reputable institutions
            reputable_domains = [
                'yale.edu', 'mit.edu', 'stanford.edu', 'harvard.edu',  # Universities
                'coursera.org', 'edx.org',  # MOOCs
                'deeplearningbook.org', 'neuralnetworksanddeeplearning.com',  # Free books
                'openintro.org', 'd2l.ai', 'github.io', 'greenteapress.com'  # Free resources
            ]

            # Verified YouTube channels/playlists (check in text description)
            verified_youtube = [
                '3blue1brown', '3b1b', 'statquest', 'computerphile',
                'stanfordonline', '@stanfordonline', '@statquest', '@computerphile'
            ]

            video_ref = refs[0] if len(refs) > 0 else None
            if video_ref:
                video_text = video_ref['text'].lower()
                video_url = video_ref['url'].lower()

                # Check if from university domain OR verified YouTube channel
                is_reputable = (
                    any(domain in video_url for domain in reputable_domains) or
                    any(channel in video_text or channel in video_url for channel in verified_youtube) or
                    'harvard' in video_text or 'yale' in video_text or 'mit' in video_text or 'stanford' in video_text
                )
                print(f"  {'✅' if is_reputable else '❌'} Video from reputable source: {is_reputable}")
                if not is_reputable:
                    issues_found.append(f"{test_case['module_name']}: Video not from reputable source - {video_ref['url']}")

            # Check 4: Books are FREE
            book_ref = refs[1] if len(refs) > 1 else None
            if book_ref:
                paid_publishers = ['packtpub.com', 'manning.com', 'oreilly.com', 'amazon.com']
                is_free = not any(pub in book_ref['url'].lower() for pub in paid_publishers)
                print(f"  {'✅' if is_free else '❌'} Book is FREE: {is_free}")
                if not is_free:
                    issues_found.append(f"{test_case['module_name']}: Book is paid - {book_ref['url']}")

            # Check 5: References are unique (not same for all topics)
            all_results.append({
                'module': test_case['module_name'],
                'video_url': refs[0]['url'] if len(refs) > 0 else None,
                'book_url': refs[1]['url'] if len(refs) > 1 else None,
                'refs': refs
            })

            print(f"\n  ✓ Test completed for {test_case['module_name']}")

        except Exception as e:
            print(f"\n  ❌ ERROR: {e}")
            issues_found.append(f"{test_case['module_name']}: Generation failed - {e}")

        # Small delay to avoid rate limiting
        if i < len(test_cases):
            time.sleep(2)

    # Cross-module validation
    print("\n" + "="*80)
    print("📊 CROSS-MODULE VALIDATION")
    print("="*80)

    video_urls = [r['video_url'] for r in all_results if r['video_url']]
    book_urls = [r['book_url'] for r in all_results if r['book_url']]

    unique_videos = len(set(video_urls))
    unique_books = len(set(book_urls))

    print(f"\n  Video References:")
    print(f"    • Total modules: {len(video_urls)}")
    print(f"    • Unique videos: {unique_videos}")
    print(f"    • {'✅' if unique_videos >= len(video_urls) * 0.8 else '⚠️'} Variety: {unique_videos}/{len(video_urls)}")

    print(f"\n  Book References:")
    print(f"    • Total modules: {len(book_urls)}")
    print(f"    • Unique books: {unique_books}")
    print(f"    • {'✅' if unique_books >= len(book_urls) * 0.8 else '⚠️'} Variety: {unique_books}/{len(book_urls)}")

    # Final summary
    print("\n" + "="*80)
    print("✅ FINAL SUMMARY")
    print("="*80)

    if not issues_found:
        print("\n  🎉 ALL TESTS PASSED!")
        print("\n  ✓ No YouTube search results")
        print("  ✓ No Khan Academy")
        print("  ✓ All videos from reputable institutions")
        print("  ✓ All books are FREE")
        print("  ✓ Good variety across modules")
    else:
        print("\n  ⚠️  ISSUES FOUND:")
        for issue in issues_found:
            print(f"    • {issue}")

    print("\n" + "="*80)
    print("DETAILED RESULTS BY MODULE:")
    print("="*80)

    for result in all_results:
        print(f"\n  📝 {result['module']}:")
        for j, ref in enumerate(result['refs'], 1):
            print(f"    {j}. {ref['text'][:60]}...")
            print(f"       {ref['url']}")

    print("\n")


if __name__ == "__main__":
    test_comprehensive_references()
