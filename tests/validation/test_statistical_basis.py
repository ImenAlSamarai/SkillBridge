#!/usr/bin/env python3
"""
Test "Statistical Basis" Module 1 gets BASIC statistics content
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.content_generator import generate_content

def test_statistical_basis():
    print("🧪 STATISTICAL BASIS MODULE TEST\n")
    print("="*80)
    print("Testing 'Statistical Basis' Module 1")
    print("Expected: Basic statistics (mean, median, distributions, variance)")
    print("NOT: Statistical Arbitrage, Derivatives Pricing, Market Microstructure")
    print("="*80)

    try:
        # Generate content for Statistical Basis (Module 1)
        content_data = generate_content(
            topic_id="statistics",
            module_id=1,
            module_name="Statistical Basis",
            depth_score=0.21,  # Module 1 depth
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

        # Check for GOOD content (basic statistics)
        good_terms = [
            'mean', 'median', 'mode',
            'variance', 'standard deviation',
            'distribution', 'normal distribution',
            'probability', 'histogram',
            'quartile', 'percentile',
            'descriptive statistics'
        ]

        # Check for BAD content (advanced finance/trading)
        bad_terms = [
            'statistical arbitrage', 'arbitrage',
            'derivatives pricing', 'black-scholes',
            'market microstructure', 'order book',
            'python backtesting', 'backtest',
            'trading strategy', 'execution algorithm',
            'high-frequency trading', 'hft'
        ]

        content_lower = content.lower()

        good_count = sum(1 for term in good_terms if term in content_lower)
        bad_count = sum(1 for term in bad_terms if term in content_lower)

        print(f"\n🔍 VALIDATION:")
        print(f"  Basic statistics terms found: {good_count}/{len(good_terms)}")
        print(f"  Advanced trading terms found: {bad_count}/{len(bad_terms)}")

        if good_count >= 4:
            print(f"  ✅ Contains basic statistics concepts")
            found = [t for t in good_terms if t in content_lower]
            print(f"     Found: {found[:5]}")
        else:
            print(f"  ❌ Missing basic statistics concepts")
            found = [t for t in good_terms if t in content_lower]
            print(f"     Only found: {found}")

        if bad_count == 0:
            print(f"  ✅ No advanced trading/finance content")
        else:
            print(f"  ❌ Contains advanced trading/finance content!")
            found = [t for t in bad_terms if t in content_lower]
            print(f"     Found: {found}")

        # Extract section titles
        import re
        print(f"\n📋 SECTION TITLES:")
        for match in re.finditer(r'## (\d+)\. (.+)', content):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            print(f"  {section_num}. {section_title}")

        if good_count >= 4 and bad_count == 0:
            print(f"\n✅ SUCCESS: Content is appropriate for Statistical Basis!")
            return True
        else:
            print(f"\n❌ FAILED: Content is not appropriate for foundational statistics module")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_statistical_basis()
