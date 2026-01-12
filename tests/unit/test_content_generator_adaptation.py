#!/usr/bin/env python3
"""
Test Content Generator Agent - Depth Adaptation
Tests how content adapts to different user levels and seniority gaps
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


import json
from src.core import database
from src.agents.content_generator import generate_content, generate_module_names
from app import calculate_depth_score

def print_separator():
    print("\n" + "="*80 + "\n")

def test_content_generator_adaptation():
    """Test content adaptation across different depth levels"""

    print("🧪 TESTING CONTENT GENERATOR - Depth Adaptation\n")
    print_separator()

    # Test topic
    topic_id = "derivatives_pricing"
    module_id = 1

    # Generate module name first
    print(f"📝 Generating module names for topic: {topic_id}")
    module_names = generate_module_names(topic_id)
    module_name = module_names.get(module_id, f"Module {module_id}")
    print(f"   Module {module_id}: {module_name}")
    print_separator()

    # Get test users with different backgrounds
    test_cases = []

    # User 1: Alex Student (Student → Junior)
    user1 = database.get_user(1)
    paths1 = database.get_paths_by_user(1)
    if paths1:
        path1 = paths1[0]
        depth1 = calculate_depth_score(
            target_seniority=path1['target_seniority'],
            initial_mastery=15,  # Low mastery (from topic assessor)
            module_id=module_id
        )
        test_cases.append({
            "name": user1['name'],
            "current": f"{path1['current_seniority']} {path1['current_job_title']}",
            "target": f"{path1['target_seniority']} {path1['target_job_title']} @ {path1['target_company']}",
            "mastery": 15,
            "depth_score": depth1,
            "description": path1['current_description']
        })

    # User 3: Mike ML (Intermediate → Advanced)
    user3 = database.get_user(3)
    paths3 = database.get_paths_by_user(3)
    if paths3:
        path3 = paths3[0]
        depth3 = calculate_depth_score(
            target_seniority=path3['target_seniority'],
            initial_mastery=0,  # New topic for ML engineer
            module_id=module_id
        )
        test_cases.append({
            "name": user3['name'],
            "current": f"{path3['current_seniority']} {path3['current_job_title']}",
            "target": f"{path3['target_seniority']} {path3['target_job_title']} @ {path3['target_company']}",
            "mastery": 0,
            "depth_score": depth3,
            "description": path3['current_description']
        })

    # User 4: Emma Quant (Intermediate → Advanced, high mastery)
    user4 = database.get_user(4)
    paths4 = database.get_paths_by_user(4)
    if paths4:
        path4 = paths4[0]
        depth4 = calculate_depth_score(
            target_seniority=path4['target_seniority'],
            initial_mastery=60,  # High mastery from topic assessor
            module_id=module_id
        )
        test_cases.append({
            "name": user4['name'],
            "current": f"{path4['current_seniority']} {path4['current_job_title']}",
            "target": f"{path4['target_seniority']} {path4['target_job_title']} @ {path4['target_company']}",
            "mastery": 60,
            "depth_score": depth4,
            "description": path4['current_description']
        })

    print(f"📋 Testing {len(test_cases)} scenarios:\n")
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case['name']}")
        print(f"   Current: {case['current']}")
        print(f"   Target:  {case['target']}")
        print(f"   Mastery: {case['mastery']}%")
        print(f"   Depth Score: {case['depth_score']} → ", end="")
        if case['depth_score'] < 0.35:
            print("Beginner")
        elif case['depth_score'] < 0.65:
            print("Intermediate")
        else:
            print("Advanced")
        print()

    print_separator()

    # Generate content for each scenario
    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {case['name'].upper()}")
        print(f"{'='*80}\n")

        print(f"📊 Profile:")
        print(f"   Current: {case['current']}")
        print(f"   Target:  {case['target']}")
        print(f"   Background: {case['description'][:100]}...")
        print(f"   Mastery: {case['mastery']}%")
        print(f"   Depth Score: {case['depth_score']}")

        print(f"\n🤖 Generating content...")

        # Prepare user context from paths data
        user_context = {
            "current_seniority": case.get('current', 'Intermediate').split()[0],
            "current_job_title": ' '.join(case.get('current', 'Professional').split()[1:]),
            "current_description": case.get('description', 'General background'),
            "target_seniority": case.get('target', 'Advanced').split()[0],
            "target_job_title": ' '.join(case.get('target', 'Senior Professional').split()[1:]).split(' @ ')[0].strip(),
            "target_description": "Advanced quantitative skills",  # Could load from DB
            "target_company": case.get('target', '').split(' @ ')[-1] if ' @ ' in case.get('target', '') else 'Industry',
            "mastery": case['mastery']
        }

        try:
            content_data = generate_content(
                topic_id=topic_id,
                module_id=module_id,
                module_name=module_name,
                depth_score=case['depth_score'],
                user_context=user_context
            )

            results.append({
                "case": case,
                "content": content_data
            })

            # Display content
            word_count = len(content_data['content'].split())
            print(f"\n📖 CONTENT ({word_count} words):")
            print(f"   {'-'*76}")
            # Wrap content
            import textwrap
            wrapped = textwrap.fill(content_data['content'], width=76)
            for line in wrapped.split('\n'):
                print(f"   {line}")
            print(f"   {'-'*76}")

            # Display key concepts
            print(f"\n💡 KEY CONCEPTS ({len(content_data.get('key_concepts', []))} concepts):")
            for i, concept in enumerate(content_data.get('key_concepts', []), 1):
                print(f"   {i}. {concept}")

            print(f"\n❓ QUESTIONS ({len(content_data['questions'])} total):")
            for q_idx, q in enumerate(content_data['questions'], 1):
                print(f"\n   Q{q_idx}: {q['text']}")
                print(f"   ✓ Answer: {q['correct_answer'][:80]}...")
                print(f"   💡 Why: {q['explanation'][:80]}...")

            print(f"\n📚 REFERENCES ({len(content_data['references'])} total):")
            for ref in content_data['references']:
                if isinstance(ref, dict):
                    print(f"   • {ref['text']}")
                    print(f"     🔗 {ref['url']}")
                else:
                    print(f"   • {ref}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        print("\n" + "="*80)

    # Comparison analysis
    print("\n\n📈 COMPARATIVE ANALYSIS\n")
    print("="*80)

    print("\n1. CONTENT LENGTH:")
    for i, result in enumerate(results, 1):
        name = result['case']['name']
        word_count = len(result['content']['content'].split())
        depth = result['case']['depth_score']
        print(f"   {name:<20} Depth: {depth:.2f}  |  Words: {word_count}")

    print("\n2. QUESTION COMPLEXITY:")
    for i, result in enumerate(results, 1):
        name = result['case']['name']
        q1_length = len(result['content']['questions'][0]['text'].split())
        depth = result['case']['depth_score']
        print(f"   {name:<20} Depth: {depth:.2f}  |  Q1 length: {q1_length} words")
        print(f"      → {result['content']['questions'][0]['text'][:60]}...")

    print("\n3. CONTENT STRUCTURE:")
    for i, result in enumerate(results, 1):
        name = result['case']['name']
        content = result['content']['content']

        # Count paragraphs (separated by double newlines)
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])

        # Count sentences
        sentences = content.count('.') + content.count('?') + content.count('!')

        # Check for technical terms
        technical_terms = ['derivative', 'option', 'underlying', 'strike', 'volatility',
                          'Black-Scholes', 'arbitrage', 'hedging', 'delta', 'gamma']
        tech_count = sum(1 for term in technical_terms if term.lower() in content.lower())

        # Key concepts count
        key_concepts_count = len(result['content'].get('key_concepts', []))

        print(f"   {name:<20} Paragraphs: {paragraphs}  |  Sentences: {sentences}  |  Technical: {tech_count}  |  Concepts: {key_concepts_count}")

    print("\n" + "="*80)
    print("\n✅ Test Complete!")
    print("\n💡 Key Questions:")
    print("   1. Does content adapt to depth level?")
    print("   2. Are questions harder for advanced users?")
    print("   3. Is content 400-500 words? (Expected: 400-500)")
    print("   4. Is content in 4-5 paragraphs? (Expected: 4-5)")
    print("   5. Are 3-5 key concepts highlighted? (Expected: 3-5)")
    print("   6. Does technical complexity increase with depth?")
    print("\n")

if __name__ == "__main__":
    test_content_generator_adaptation()
