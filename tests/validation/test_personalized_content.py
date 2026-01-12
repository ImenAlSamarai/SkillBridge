#!/usr/bin/env python3
"""
Test personalized content generation
Demonstrates: Quant Researcher (Advanced) → Quant Trader (Advanced) at Citadel
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.core import database
from src.agents.content_generator import generate_content, generate_module_names

def test_advanced_quant_transition():
    """Test content for advanced user transition - should NOT be basic!"""

    print("🧪 TESTING PERSONALIZED CONTENT GENERATION\n")
    print("="*80)

    # Scenario: Advanced Quant Researcher → Advanced Quant Trader at Citadel
    topic_id = "data_analysis"
    module_id = 1

    # Generate module name
    print(f"\n📝 Topic: {topic_id}")
    module_names = generate_module_names(topic_id)
    module_name = module_names.get(module_id, "Module 1")
    print(f"   Module {module_id}: {module_name}")

    # User context - Advanced Quant Researcher
    user_context = {
        "current_seniority": "Advanced",
        "current_job_title": "Quant Researcher",
        "current_description": "Building statistical models, risk analysis, portfolio optimization using Python, R, SQL",
        "target_seniority": "Advanced",
        "target_job_title": "Quant Trader",
        "target_description": "Designing and implementing trading strategies, execution algorithms, market microstructure analysis",
        "target_company": "Citadel",
        "mastery": 60  # Already knows data analysis basics
    }

    print(f"\n👤 User Profile:")
    print(f"   Current: {user_context['current_seniority']} {user_context['current_job_title']}")
    print(f"   Target:  {user_context['target_seniority']} {user_context['target_job_title']} @ {user_context['target_company']}")
    print(f"   Current mastery: {user_context['mastery']}%")
    print(f"   Current skills: {user_context['current_description'][:80]}...")

    # Depth score for Advanced → Advanced with 60% mastery
    depth_score = 0.88
    print(f"   Depth score: {depth_score} (Advanced)")

    print(f"\n🤖 Generating content...\n")

    # Generate content
    content_data = generate_content(
        topic_id=topic_id,
        module_id=module_id,
        module_name=module_name,
        depth_score=depth_score,
        user_context=user_context
    )

    print("="*80)
    print("📖 GENERATED CONTENT")
    print("="*80)
    print(content_data['content'])
    print("\n" + "="*80)

    print(f"\n💡 KEY CONCEPTS ({len(content_data['key_concepts'])}):")
    for i, concept in enumerate(content_data['key_concepts'], 1):
        print(f"   {i}. {concept}")

    print(f"\n❓ QUESTIONS ({len(content_data['questions'])}):")
    for i, q in enumerate(content_data['questions'], 1):
        print(f"\n   Q{i}: {q['text']}")
        print(f"        Answer: {q['correct_answer'][:100]}...")

    print(f"\n📚 REFERENCES ({len(content_data['references'])}):")
    for ref in content_data['references']:
        if isinstance(ref, dict):
            print(f"   • {ref['text']}")
            print(f"     🔗 {ref['url']}")
        else:
            print(f"   • {ref}")

    print("\n" + "="*80)
    print("\n✅ VALIDATION:")

    # Check if content is appropriate for advanced user
    word_count = len(content_data['content'].split())
    sections = content_data['content'].count('##')
    bold_terms = content_data['content'].count('**') // 2

    print(f"   ✓ Word count: {word_count} words (target: 400-500)")
    print(f"   ✓ Numbered sections: {sections} sections")
    print(f"   ✓ Bold formatting: {bold_terms} bold terms")
    print(f"   ✓ Key concepts: {len(content_data['key_concepts'])} concepts")

    # Check if content mentions basics (should NOT for advanced user with 60% mastery)
    content_lower = content_data['content'].lower()
    basic_terms = ["mean", "median", "mode", "what is", "introduction to"]
    advanced_terms = ["trading", "execution", "microstructure", "strategy", "algorithms", "citadel"]

    basics_found = sum(1 for term in basic_terms if term in content_lower)
    advanced_found = sum(1 for term in advanced_terms if term in content_lower)

    print(f"\n   Content analysis:")
    print(f"   • Basic terms found: {basics_found} (should be LOW for advanced user)")
    print(f"   • Advanced/trading terms: {advanced_found} (should be HIGH for trader)")

    if basics_found > advanced_found:
        print(f"\n   ⚠️  WARNING: Content seems too basic for Advanced Quant Researcher!")
        print(f"   ⚠️  Should focus on trading strategies, not statistics 101")
    else:
        print(f"\n   ✅ Content appropriately adapted for advanced professional")

    print("\n")

if __name__ == "__main__":
    test_advanced_quant_transition()
