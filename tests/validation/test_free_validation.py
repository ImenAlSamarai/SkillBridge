#!/usr/bin/env python3
"""
Test validation of FALSE "FREE" claims
Ensures that paid publishers (Packt, Manning, O'Reilly, Amazon) are not labeled as FREE
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from src.agents.content_generator import validate_and_fix_references

def test_false_free_claims():
    print("🧪 TESTING FALSE 'FREE' CLAIM DETECTION\n")
    print("="*80)

    # Test case: Reference falsely claims "FREE" but links to paid publisher
    fake_free_references = [
        {
            "text": "FREE Book: Python Machine Learning by Sebastian Raschka",
            "url": "https://www.packtpub.com/en-us/product/python-machine-learning-9781783555130"
        },
        {
            "text": "Machine Learning with Python Course (FREE)",
            "url": "https://www.manning.com/books/machine-learning-with-python"
        }
    ]

    print("\n📝 TEST INPUT (falsely labeled as FREE):")
    for i, ref in enumerate(fake_free_references, 1):
        print(f"\n{i}. {ref['text']}")
        print(f"   🔗 {ref['url']}")
        print(f"   ⚠️  This is a PAID book from Packt/Manning!")

    print("\n" + "="*80)
    print("🔍 Running validation...\n")

    # Validate and fix
    validated_refs = validate_and_fix_references(
        references=fake_free_references,
        topic_id="machine_learning",
        module_name="Python Machine Learning"
    )

    print("\n" + "="*80)
    print("📚 VALIDATED REFERENCES (after fixing):")
    print("="*80)

    for i, ref in enumerate(validated_refs, 1):
        print(f"\n{i}. {ref['text']}")
        print(f"   🔗 {ref['url']}")

        # Check if it's truly free
        if 'packtpub.com' in ref['url'] or 'manning.com' in ref['url']:
            print(f"   ❌ FAILED: Still pointing to paid publisher!")
        else:
            print(f"   ✅ SUCCESS: Replaced with truly FREE resource")

    print("\n" + "="*80)
    print("✅ VALIDATION SUMMARY:")
    print("="*80)

    # Check that no paid publishers remain
    has_packt = any('packtpub.com' in ref['url'] for ref in validated_refs)
    has_manning = any('manning.com' in ref['url'] for ref in validated_refs)
    has_oreilly = any('oreilly.com' in ref['url'] for ref in validated_refs)

    all_truly_free = not (has_packt or has_manning or has_oreilly)

    print(f"   • Removed Packt publishers: {not has_packt}")
    print(f"   • Removed Manning publishers: {not has_manning}")
    print(f"   • Removed O'Reilly publishers: {not has_oreilly}")
    print(f"   • All references truly FREE: {all_truly_free}")

    if all_truly_free:
        print(f"\n   🎉 SUCCESS: False 'FREE' claims detected and replaced!")
        print(f"   → Users will only see genuinely free resources")
    else:
        print(f"\n   ❌ FAILURE: Some paid publishers still present")

    print("\n")


if __name__ == "__main__":
    test_false_free_claims()
