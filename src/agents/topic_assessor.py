#!/usr/bin/env python3
"""
Topic Assessor Agent for learn_flow
Phase 2C: Breaks topics into subtopics with mastery% and estimated hours
"""
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from src.core.llm_engine import call_llm
from src.agents.job_parser import get_recent_skills
from src.core import load_agent_config, load_prompts


def load_assessor_prompt() -> str:
    """Load topic assessor prompt from config using config loader"""
    prompts = load_prompts("agent2")
    return prompts["topic_assessor_prompt"]


def assess_topics(user_id: int, topics: List[Dict[str, Any]], current_job_context: str = "") -> List[Dict[str, Any]]:
    """
    Break down topics into subtopics with mastery and hours estimation

    Args:
        user_id: User ID for recent skills lookup
        topics: List of topic dicts from Phase 2B (id, prereq, difficulty)

    Returns:
        List of assessed topics with mastery%, modules_complete, estimated_hours, subtopics

    Example output:
        [
            {
                "topic_id": "statistical_arbitrage",
                "mastery": 15,
                "modules_complete": "0/8",
                "estimated_hours": 24,
                "subtopics": [
                    {"id": "stat_arb_theory", "hours": 8},
                    {"id": "pairs_trading", "hours": 10}
                ]
            }
        ]
    """
    # Get recent skills for mastery estimation
    recent_skills = get_recent_skills(user_id, days=30)
    recent_skills_str = ", ".join(recent_skills) if recent_skills else "None"

    # Load prompt template
    prompt_template = load_assessor_prompt()

    # Convert topics to JSON string
    topics_json = json.dumps(topics)

    # Fill in template
    prompt = prompt_template.format(
        topics_json=topics_json,
        current_job_context=current_job_context or "No current job context",
        recent_skills=recent_skills_str
    )

    # Load LLM config and call LLM
    agent_config = load_agent_config("agent2_topic_assessor")
    llm_config = agent_config["llm_config"]
    response, tokens = call_llm(
        prompt,
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"]
    )

    # Parse JSON response
    import re
    import logging

    logger = logging.getLogger(__name__)
    response_clean = response.strip()

    try:
        # Method 1: Direct parse if starts with [
        if response_clean.startswith("["):
            assessed_topics = json.loads(response_clean)

        # Method 2: Extract from markdown code block
        elif "```json" in response_clean or "```" in response_clean:
            match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_clean, re.DOTALL)
            if match:
                assessed_topics = json.loads(match.group(1))
            else:
                raise ValueError("Found code block but couldn't extract JSON")

        # Method 3: Find JSON array using bracket matching
        else:
            start_idx = response_clean.find("[")
            if start_idx == -1:
                logger.error(f"No JSON array found in response: {response[:300]}")
                raise ValueError("Response contains no JSON array")

            # Count brackets to find matching ]
            bracket_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response_clean)):
                if response_clean[i] == '[':
                    bracket_count += 1
                elif response_clean[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break

            if bracket_count != 0:
                logger.error(f"Unmatched brackets in response: {response[:300]}")
                raise ValueError("Unmatched brackets in JSON array")

            json_str = response_clean[start_idx:end_idx]
            assessed_topics = json.loads(json_str)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode failed: {e}")
        raise ValueError(f"LLM returned invalid JSON: {e}\nResponse: {response[:300]}")
    except Exception as e:
        logger.error(f"JSON extraction failed: {e}")
        raise ValueError(f"Failed to extract JSON: {e}\nResponse: {response[:300]}")

    # Validate structure
    assessed_topics = validate_assessed_topics(assessed_topics)

    return assessed_topics


def validate_assessed_topics(assessed_topics: Any) -> List[Dict[str, Any]]:
    """Validate assessed topics structure"""
    assert isinstance(assessed_topics, list), "Assessed topics must be array"

    for i, topic in enumerate(assessed_topics):
        assert isinstance(topic, dict), f"Topic {i} must be object"
        assert "topic_id" in topic, f"Topic {i} missing 'topic_id'"
        assert "mastery" in topic, f"Topic {i} missing 'mastery'"
        assert "modules_complete" in topic, f"Topic {i} missing 'modules_complete'"
        assert "estimated_hours" in topic, f"Topic {i} missing 'estimated_hours'"
        assert "subtopics" in topic, f"Topic {i} missing 'subtopics'"

        # Validate mastery range
        assert 0 <= topic["mastery"] <= 100, f"Topic {i} mastery must be 0-100, got {topic['mastery']}"

        # Validate subtopics
        assert isinstance(topic["subtopics"], list), f"Topic {i} subtopics must be array"
        for j, subtopic in enumerate(topic["subtopics"]):
            assert isinstance(subtopic, dict), f"Topic {i} subtopic {j} must be object"
            assert "id" in subtopic, f"Topic {i} subtopic {j} missing 'id'"
            assert "hours" in subtopic, f"Topic {i} subtopic {j} missing 'hours'"

    return assessed_topics


def calculate_global_readiness(assessed_topics: List[Dict[str, Any]]) -> float:
    """
    Calculate global readiness as average mastery across all topics

    Args:
        assessed_topics: List of topics with mastery percentages

    Returns:
        Global readiness percentage (0-100)
    """
    if not assessed_topics:
        return 0.0

    total_mastery = sum(topic["mastery"] for topic in assessed_topics)
    return round(total_mastery / len(assessed_topics), 1)


if __name__ == "__main__":
    print("Topic Assessor Agent ready.")
    print("Use: assess_topics(user_id, topics)")
