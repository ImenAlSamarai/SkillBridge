#!/usr/bin/env python3
"""
Unit tests for config_loader.py
Simple tests - verify functions load configs and return expected structure
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config_loader import (
    load_agent_config,
    load_prompts,
    load_thresholds,
    load_learning_resources,
    clear_cache
)


def test_load_agent_config():
    """Test loading agent configurations"""
    print("\n1. Testing load_agent_config()...")

    # Test Agent 1
    config1 = load_agent_config("agent1_job_parser")
    assert isinstance(config1, dict), "Should return dict"
    assert "llm_config" in config1, "Should have llm_config"
    assert "validation" in config1, "Should have validation"
    print("   ✅ Agent 1 config loaded")

    # Test Agent 2
    config2 = load_agent_config("agent2_topic_assessor")
    assert isinstance(config2, dict), "Should return dict"
    assert "llm_config" in config2, "Should have llm_config"
    assert "module_structure" in config2, "Should have module_structure"
    print("   ✅ Agent 2 config loaded")

    # Test Agent 3
    config3 = load_agent_config("agent3_content_generator")
    assert isinstance(config3, dict), "Should return dict"
    assert "llm_config" in config3, "Should have llm_config"
    assert "content_structure" in config3, "Should have content_structure"
    print("   ✅ Agent 3 config loaded")


def test_load_prompts():
    """Test loading prompt files"""
    print("\n2. Testing load_prompts()...")

    # Test Agent 1 prompts
    prompts1 = load_prompts("agent1")
    assert isinstance(prompts1, dict), "Should return dict"
    assert "job_parser_prompt" in prompts1, "Should have job_parser_prompt"
    print("   ✅ Agent 1 prompts loaded")

    # Test Agent 2 prompts
    prompts2 = load_prompts("agent2")
    assert isinstance(prompts2, dict), "Should return dict"
    assert "topic_assessor_prompt" in prompts2, "Should have topic_assessor_prompt"
    print("   ✅ Agent 2 prompts loaded")

    # Test Agent 3 prompts
    prompts3 = load_prompts("agent3")
    assert isinstance(prompts3, dict), "Should return dict"
    assert "content_generator_prompt" in prompts3, "Should have content_generator_prompt"
    print("   ✅ Agent 3 prompts loaded")


def test_load_thresholds():
    """Test loading thresholds configuration"""
    print("\n3. Testing load_thresholds()...")

    thresholds = load_thresholds()
    assert isinstance(thresholds, dict), "Should return dict"
    assert "depth_calculation" in thresholds, "Should have depth_calculation"
    assert "content_personalization" in thresholds, "Should have content_personalization"

    # Check specific values
    depth_calc = thresholds["depth_calculation"]
    assert "seniority_levels" in depth_calc, "Should have seniority_levels"
    assert depth_calc["seniority_levels"]["Student"] == 0.15, "Student level should be 0.15"

    print("   ✅ Thresholds loaded correctly")


def test_load_learning_resources():
    """Test loading learning resources"""
    print("\n4. Testing load_learning_resources()...")

    resources = load_learning_resources()
    assert isinstance(resources, dict), "Should return dict"
    assert "fallback_references" in resources, "Should have fallback_references"
    assert "blocked_sources" in resources, "Should have blocked_sources"
    assert "prestigious_institutions" in resources, "Should have prestigious_institutions"

    # Check specific fallback
    fallbacks = resources["fallback_references"]
    assert "machine_learning" in fallbacks, "Should have machine_learning fallbacks"
    assert "statistics" in fallbacks, "Should have statistics fallbacks"

    print("   ✅ Learning resources loaded correctly")


def test_caching():
    """Test that caching works"""
    print("\n5. Testing caching...")

    # Clear cache first
    clear_cache()

    # Load once
    config1 = load_agent_config("agent1_job_parser")

    # Load again - should come from cache
    config2 = load_agent_config("agent1_job_parser")

    # Should be same object (cached)
    assert config1 is config2, "Should return cached object"

    print("   ✅ Caching works correctly")


def test_error_handling():
    """Test error handling for missing files"""
    print("\n6. Testing error handling...")

    try:
        load_agent_config("nonexistent_agent")
        assert False, "Should raise FileNotFoundError"
    except FileNotFoundError as e:
        assert "Config file not found" in str(e)
        print("   ✅ FileNotFoundError raised correctly")


def main():
    """Run all tests"""
    print("="*80)
    print("TASK 2: CONFIG LOADER UNIT TESTS")
    print("="*80)

    try:
        test_load_agent_config()
        test_load_prompts()
        test_load_thresholds()
        test_load_learning_resources()
        test_caching()
        test_error_handling()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nConfig loader working correctly:")
        print("  ✅ All agent configs load")
        print("  ✅ All prompts load")
        print("  ✅ Thresholds load")
        print("  ✅ Learning resources load")
        print("  ✅ Caching works")
        print("  ✅ Error handling works")
        print("\n✅ TASK 2 COMPLETE - Config loader ready to use")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
