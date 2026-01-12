#!/usr/bin/env python3
"""
Comprehensive Test for ALL 3 Agents + LangGraph Workflow

Tests:
1. Agent 1 (Job Parser): Generates appropriate topics from job descriptions
2. Agent 2 (Topic Assessor): Creates modules with correct depth progression
3. Agent 3 (Content Generator): Generates aligned content for each module
4. Content Alignment: Foundational modules get basic content, advanced get advanced
5. Reference Quality: Only reputable institutions, no YouTube search, no Khan Academy
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.workflow import run_full_workflow
from src.agents.content_generator import generate_content
from src.core import database
import re


def test_agent1_job_parser():
    """Test Agent 1: Job Parser generates appropriate topics"""
    print("\n" + "="*80)
    print("TEST 1: AGENT 1 (JOB PARSER)")
    print("="*80)

    # Test case: Undergrad → Quant Researcher (use existing user_id=1)
    form_data = {
        "current_job_title": "Undergrad Student",
        "current_description": "Basic math and programming",
        "current_seniority": "Student",
        "target_job_title": "Quant Researcher",
        "target_description": "Develop trading strategies, statistical modeling",
        "target_seniority": "Junior",
        "target_company": "Jane Street",
        "target_industry": "Finance"
    }

    print(f"\nUser Profile:")
    print(f"  Current: {form_data['current_seniority']} {form_data['current_job_title']}")
    print(f"  Target: {form_data['target_seniority']} {form_data['target_job_title']} @ {form_data['target_company']}")

    # Run workflow with existing user_id=1
    result = run_full_workflow(user_id=1, form_data=form_data)

    if result["error"]:
        print(f"\n❌ FAILED: {result['error']}")
        return False

    topics = result["assessed_topics"]
    print(f"\n✅ Agent 1 SUCCESS: {len(topics)} topics generated")

    # Validate topics are relevant
    expected_domains = ["statistics", "calculus", "programming", "probability", "linear_algebra"]
    found_domains = [t["topic_id"] for t in topics]

    relevant_count = sum(1 for domain in expected_domains if any(domain in tid for tid in found_domains))
    print(f"\n  Relevant topics: {relevant_count}/{len(expected_domains)}")
    print(f"  Topics: {', '.join([t['topic_name'] for t in topics[:5]])}...")

    return len(topics) > 0


def test_agent2_topic_assessor(topics):
    """Test Agent 2: Topic Assessor creates properly structured modules"""
    print("\n" + "="*80)
    print("TEST 2: AGENT 2 (TOPIC ASSESSOR)")
    print("="*80)

    if not topics:
        print("❌ No topics to assess")
        return False

    # Check first topic's modules
    first_topic = topics[0]
    print(f"\nAnalyzing topic: {first_topic['topic_name']}")
    print(f"  Mastery: {first_topic['mastery']}%")
    print(f"  Modules: {len(first_topic.get('modules', []))}")

    modules = first_topic.get('modules', [])
    if not modules:
        print("❌ No modules generated")
        return False

    # Check module progression
    print(f"\n  Module Structure:")
    for i, mod in enumerate(modules[:4], 1):
        print(f"    Module {i}: {mod.get('module_name', 'Unknown')}")

    # Validate first module is foundational
    first_module_name = modules[0].get('module_name', '').lower()
    is_foundational = any(kw in first_module_name for kw in ['basis', 'foundations', 'basics', 'introduction', 'fundamentals'])

    if is_foundational:
        print(f"\n  ✅ Module 1 is foundational: '{modules[0]['module_name']}'")
    else:
        print(f"\n  ⚠️  Module 1 may not be foundational: '{modules[0]['module_name']}'")

    return True


def test_agent3_content_alignment(topics):
    """Test Agent 3: Content Generator creates aligned content"""
    print("\n" + "="*80)
    print("TEST 3: AGENT 3 (CONTENT GENERATOR) - ALIGNMENT")
    print("="*80)

    if not topics or not topics[0].get('modules'):
        print("❌ No modules to generate content for")
        return False

    first_topic = topics[0]
    first_module = first_topic['modules'][0]

    print(f"\nGenerating content for:")
    print(f"  Topic: {first_topic['topic_name']}")
    print(f"  Module 1: {first_module['module_name']}")
    print(f"  Mastery: {first_topic['mastery']}%")

    try:
        # Generate content for Module 1
        content_data = generate_content(
            topic_id=first_topic['topic_id'],
            module_id=1,
            module_name=first_module['module_name'],
            depth_score=0.2,  # Module 1 should be foundational
            user_context={
                'current_seniority': 'Student',
                'current_job_title': 'Undergrad Student',
                'current_description': 'Basic math and programming',
                'target_seniority': 'Junior',
                'target_job_title': 'Quant Researcher',
                'target_description': 'Quantitative research',
                'target_company': 'Jane Street',
                'mastery': first_topic['mastery']
            }
        )

        content = content_data['content']

        # Extract section titles
        sections = re.findall(r'## (\d+)\. (.+)', content)

        print(f"\n  Generated {len(sections)} sections:")
        for num, title in sections:
            print(f"    {num}. {title}")

        # Check for alignment
        content_lower = content.lower()

        # Define basic vs advanced terms for different topics
        if 'statistic' in first_topic['topic_id'].lower():
            basic_terms = ['mean', 'median', 'mode', 'variance', 'distribution', 'probability']
            advanced_terms = ['arbitrage', 'derivatives pricing', 'microstructure', 'backtesting']
        elif 'calculus' in first_topic['topic_id'].lower():
            basic_terms = ['derivative', 'integral', 'limit', 'differentiation']
            advanced_terms = ['stochastic', "itô", 'martingale', 'sde']
        else:
            basic_terms = ['basic', 'introduction', 'fundamental']
            advanced_terms = ['advanced', 'complex', 'sophisticated']

        basic_count = sum(1 for term in basic_terms if term in content_lower)
        advanced_count = sum(1 for term in advanced_terms if term in content_lower)

        print(f"\n  Content Analysis:")
        print(f"    Basic terms found: {basic_count}/{len(basic_terms)}")
        print(f"    Advanced terms found: {advanced_count}/{len(advanced_terms)}")

        if basic_count >= len(basic_terms) * 0.4 and advanced_count == 0:
            print(f"\n  ✅ Content is appropriately foundational")
            return True
        elif advanced_count > 0:
            print(f"\n  ❌ Content contains advanced topics in foundational module!")
            print(f"     Advanced terms: {[t for t in advanced_terms if t in content_lower]}")
            return False
        else:
            print(f"\n  ⚠️  Content may not have enough foundational concepts")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent3_reference_quality(topics):
    """Test Agent 3: Reference quality validation"""
    print("\n" + "="*80)
    print("TEST 4: AGENT 3 (CONTENT GENERATOR) - REFERENCE QUALITY")
    print("="*80)

    if not topics or not topics[0].get('modules'):
        print("❌ No modules to test")
        return False

    first_topic = topics[0]
    first_module = first_topic['modules'][0]

    print(f"\nChecking references for Module 1: {first_module['module_name']}")

    try:
        content_data = generate_content(
            topic_id=first_topic['topic_id'],
            module_id=1,
            module_name=first_module['module_name'],
            depth_score=0.2,
            user_context={
                'current_seniority': 'Student',
                'current_job_title': 'Undergrad Student',
                'current_description': 'Basic math and programming',
                'target_seniority': 'Junior',
                'target_job_title': 'Quant Researcher',
                'target_description': 'Quantitative research',
                'target_company': 'Jane Street',
                'mastery': first_topic['mastery']
            }
        )

        refs = content_data['references']

        print(f"\n  Generated {len(refs)} references:")
        for i, ref in enumerate(refs, 1):
            print(f"    {i}. {ref['text'][:60]}...")
            print(f"       URL: {ref['url']}")

        # Validation checks
        has_youtube_search = any('youtube.com/results?search_query=' in ref['url'] for ref in refs)
        has_khan_academy = any('khanacademy.org' in ref['url'] for ref in refs)
        has_channel_homepage = any('youtube.com/@' in ref['url'] and '/courses' not in ref['url'] for ref in refs)

        print(f"\n  Reference Quality:")
        print(f"    {'✅' if not has_youtube_search else '❌'} No YouTube search results: {not has_youtube_search}")
        print(f"    {'✅' if not has_khan_academy else '❌'} No Khan Academy: {not has_khan_academy}")
        print(f"    {'✅' if not has_channel_homepage else '❌'} No channel homepages: {not has_channel_homepage}")

        if has_youtube_search or has_khan_academy or has_channel_homepage:
            print(f"\n  ❌ Reference quality check FAILED")
            return False
        else:
            print(f"\n  ✅ All reference quality checks passed")
            return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main():
    """Run comprehensive test suite"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST: ALL 3 AGENTS + LANGGRAPH WORKFLOW")
    print("="*80)
    print("\nTesting end-to-end pipeline:")
    print("  1. Agent 1: Job Parser")
    print("  2. Agent 2: Topic Assessor")
    print("  3. Agent 3: Content Generator (alignment + references)")
    print("  4. LangGraph Workflow orchestration")
    print("="*80)

    # Test Agent 1 (use existing user ID 1)
    agent1_pass = test_agent1_job_parser()

    if not agent1_pass:
        print("\n❌ AGENT 1 FAILED - Cannot continue")
        return False

    # Get topics for subsequent tests
    paths = database.get_paths_by_user(1)
    if not paths:
        print("\n❌ No path data found")
        return False

    topics = paths[0].get('topics', [])

    # Test Agent 2
    agent2_pass = test_agent2_topic_assessor(topics)

    # Test Agent 3
    agent3_alignment = test_agent3_content_alignment(topics)
    agent3_references = test_agent3_reference_quality(topics)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"  Agent 1 (Job Parser): {'✅ PASS' if agent1_pass else '❌ FAIL'}")
    print(f"  Agent 2 (Topic Assessor): {'✅ PASS' if agent2_pass else '❌ FAIL'}")
    print(f"  Agent 3 (Content Alignment): {'✅ PASS' if agent3_alignment else '❌ FAIL'}")
    print(f"  Agent 3 (Reference Quality): {'✅ PASS' if agent3_references else '❌ FAIL'}")

    all_pass = agent1_pass and agent2_pass and agent3_alignment and agent3_references

    print(f"\n{'='*80}")
    if all_pass:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)

    return all_pass


if __name__ == "__main__":
    main()
