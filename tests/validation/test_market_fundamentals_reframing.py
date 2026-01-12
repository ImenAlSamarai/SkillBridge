#!/usr/bin/env python3
"""
Test module reframing for Market Fundamentals
Demonstrates fix for: "Market Fundamentals is a waste of time for Advanced Quant Researcher"
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import generate_content, generate_module_names, reframe_module_for_user

def test_market_fundamentals_reframing():
    """
    Test that "Market Fundamentals" is reframed for advanced users
    Should NOT be generic "fundamentals" for someone who already knows markets
    """

    print("🧪 TESTING MODULE REFRAMING - Market Fundamentals\n")
    print("="*80)

    # Advanced Quant Researcher → Advanced Quant Trader at Citadel
    user_context = {
        "current_seniority": "Advanced",
        "current_job_title": "Quant Researcher",
        "current_description": "Statistical arbitrage models, risk analysis, portfolio optimization",
        "target_seniority": "Advanced",
        "target_job_title": "Quant Trader",
        "target_description": "Trading strategies, execution algorithms, market making",
        "target_company": "Citadel",
        "mastery": 65  # Already knows market fundamentals!
    }

    print(f"👤 User Profile:")
    print(f"   {user_context['current_job_title']} → {user_context['target_job_title']} @ {user_context['target_company']}")
    print(f"   Current mastery: {user_context['mastery']}%")
    print(f"   ⚠️  Issue: This user doesn't need 'Market Fundamentals 101'!")

    # Original generic module name
    original_module = "Market Fundamentals"
    print(f"\n📝 Original Module: '{original_module}'")

    # Test reframing
    print(f"\n🔄 Reframing module for user context...")
    reframed_module = reframe_module_for_user(original_module, user_context)

    print(f"\n✅ Reframed Module: '{reframed_module}'")

    if reframed_module == original_module:
        print(f"   ⚠️  Warning: Module name unchanged - reframing may have failed")
    else:
        print(f"   ✓ Module successfully adapted for {user_context['target_job_title']}")

    # Generate content with reframed module
    print(f"\n🤖 Generating content...\n")

    content_data = generate_content(
        topic_id="market_fundamentals",
        module_id=1,
        module_name=original_module,  # Pass original, function will reframe internally
        depth_score=0.88,
        user_context=user_context
    )

    print("="*80)
    print("📖 GENERATED CONTENT (First 600 chars)")
    print("="*80)
    print(content_data['content'][:600] + "...")
    print("\n" + "="*80)

    # Validate personalization
    content_lower = content_data['content'].lower()

    print(f"\n✅ VALIDATION:")

    # Check if actual job titles are mentioned
    has_researcher = "quant researcher" in content_lower or "researcher" in content_lower
    has_trader = "quant trader" in content_lower or "trader" in content_lower
    has_citadel = "citadel" in content_lower
    has_generic = "professionals" in content_lower or "finance industry" in content_lower

    print(f"   ✓ Mentions 'Quant Researcher': {has_researcher}")
    print(f"   ✓ Mentions 'Quant Trader': {has_trader}")
    print(f"   ✓ Mentions 'Citadel': {has_citadel}")
    print(f"   ✗ Uses generic 'Professionals' phrase: {has_generic}")

    # Check for advanced vs basic content
    basic_terms = ["what is", "introduction to", "basics of", "fundamental concept"]
    advanced_terms = ["microstructure", "execution", "liquidity", "order flow", "hft", "trading"]

    basics_count = sum(1 for term in basic_terms if term in content_lower)
    advanced_count = sum(1 for term in advanced_terms if term in content_lower)

    print(f"\n   Content Analysis:")
    print(f"   • Basic/intro phrases: {basics_count} (should be 0 for 65% mastery)")
    print(f"   • Advanced trading terms: {advanced_count} (should be HIGH)")

    # Overall verdict
    print(f"\n{'='*80}")
    if has_trader and has_citadel and not has_generic and advanced_count > basics_count:
        print("✅ SUCCESS: Content properly personalized for Advanced Quant Researcher")
        print("   → No generic 'Professionals' phrases")
        print("   → Mentions actual job titles and target company")
        print("   → Focuses on advanced concepts, not basics")
    else:
        print("⚠️  ISSUE: Content still has personalization problems:")
        if has_generic:
            print("   → Still uses generic 'Professionals' instead of job titles")
        if not has_trader or not has_citadel:
            print("   → Doesn't mention target role/company")
        if basics_count >= advanced_count:
            print("   → Still teaching basics despite 65% mastery")

    print("\n")

if __name__ == "__main__":
    test_market_fundamentals_reframing()
