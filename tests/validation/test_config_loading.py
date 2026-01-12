#!/usr/bin/env python3
"""
Test that all new configuration files load correctly
Task 1 Verification - No code changes, just testing config loading
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


import yaml
from pathlib import Path


def test_config_file(config_path: str, description: str) -> bool:
    """Test loading a single config file"""
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            print(f"  ❌ {description}: Empty config file")
            return False

        print(f"  ✅ {description}: Loaded successfully")
        return True

    except yaml.YAMLError as e:
        print(f"  ❌ {description}: YAML parsing error - {e}")
        return False
    except FileNotFoundError:
        print(f"  ❌ {description}: File not found - {config_path}")
        return False
    except Exception as e:
        print(f"  ❌ {description}: Unexpected error - {e}")
        return False


def main():
    print("="*80)
    print("TASK 1: CONFIG FILES LOADING TEST")
    print("="*80)
    print("\nTesting all new configuration files...")
    print()

    results = []

    # Test thresholds
    print("1. Thresholds Configuration:")
    results.append(test_config_file(
        "config/thresholds.yaml",
        "Depth calculation and thresholds"
    ))

    # Test learning resources
    print("\n2. Learning Resources:")
    results.append(test_config_file(
        "config/resources/learning_resources.yaml",
        "Fallback references and resources"
    ))

    # Test agent configs
    print("\n3. Agent Configurations:")
    results.append(test_config_file(
        "config/agents/agent1_job_parser.yaml",
        "Agent 1 (Job Parser)"
    ))
    results.append(test_config_file(
        "config/agents/agent2_topic_assessor.yaml",
        "Agent 2 (Topic Assessor)"
    ))
    results.append(test_config_file(
        "config/agents/agent3_content_generator.yaml",
        "Agent 3 (Content Generator)"
    ))

    # Test prompts
    print("\n4. Prompt Files:")
    results.append(test_config_file(
        "config/prompts/agent1_prompts.yaml",
        "Agent 1 prompts"
    ))
    results.append(test_config_file(
        "config/prompts/agent2_prompts.yaml",
        "Agent 2 prompts"
    ))
    results.append(test_config_file(
        "config/prompts/agent3_prompts_v1.yaml",
        "Agent 3 prompts"
    ))
    results.append(test_config_file(
        "config/prompts/workflow_prompts.yaml",
        "Workflow prompts"
    ))

    # Test existing configs (should still work)
    print("\n5. Existing Configurations (Preserved):")
    results.append(test_config_file(
        "config/fields.yaml",
        "Form fields"
    ))
    results.append(test_config_file(
        "config/admin_users.yaml",
        "Admin users"
    ))
    results.append(test_config_file(
        "config/golden_sources.yaml",
        "Golden sources"
    ))
    results.append(test_config_file(
        "config/llm.yaml",
        "Original LLM config (preserved)"
    ))

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\nTotal config files: {total}")
    print(f"  ✅ Passed: {passed}")
    if failed > 0:
        print(f"  ❌ Failed: {failed}")

    if passed == total:
        print("\n🎉 ALL CONFIG FILES LOAD SUCCESSFULLY!")
        print("\n✅ TASK 1 COMPLETE")
        print("   - All configuration files created")
        print("   - All files parse correctly")
        print("   - Existing configs preserved")
        print("   - Ready for Task 2 (Config Loader)")
        return True
    else:
        print("\n❌ SOME CONFIG FILES FAILED TO LOAD")
        print("   - Fix errors above before proceeding")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
