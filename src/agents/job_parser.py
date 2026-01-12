#!/usr/bin/env python3
"""
Job Parser Agent for learn_flow
Phase 2B: Extract topics from 12 form fields → JSON topics array
"""
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.core import database
from src.core.llm_engine import call_llm
from src.core import load_agent_config, load_prompts


def get_recent_skills(user_id: int, days: int = 30) -> List[str]:
    """
    Get recently mastered topics (mastery >= 80%) within last N days

    Args:
        user_id: User ID
        days: Look back period

    Returns:
        List of topic IDs that were recently mastered
    """
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor.execute("""
            SELECT topic_id FROM user_skills
            WHERE user_id = ? AND mastery_percent >= 80 AND last_completed >= ?
        """, (user_id, cutoff_date))
        return [row['topic_id'] for row in cursor.fetchall()]


def validate_topics_json(topics: Any) -> List[Dict[str, Any]]:
    """
    Validate topics JSON structure

    Args:
        topics: Parsed JSON (should be list of dicts)

    Returns:
        Validated topics list

    Raises:
        AssertionError: If validation fails
        ValueError: If prereq chain is invalid
    """
    assert isinstance(topics, list), "Topics must be array"
    valid_difficulties = ["foundational", "intermediate", "advanced"]

    # Build ID set for fast lookup
    topic_ids = [t.get("id") for t in topics if isinstance(t, dict)]
    topic_id_set = set(topic_ids)

    # Fix #5: Check for duplicate IDs
    duplicates = [tid for tid in topic_id_set if topic_ids.count(tid) > 1]
    if duplicates:
        raise ValueError(f"Duplicate topic IDs found: {duplicates}")

    for i, topic in enumerate(topics):
        try:
            assert isinstance(topic, dict), f"Topic {i} must be object, got: {type(topic).__name__}"
            assert "id" in topic, f"Topic {i} missing 'id' field. Keys: {list(topic.keys())}"
            assert "prereq" in topic, f"Topic {i} missing 'prereq' field. Keys: {list(topic.keys())}"
            assert "difficulty" in topic, f"Topic {i} missing 'difficulty' field. Keys: {list(topic.keys())}"

            # Auto-fix: Handle list prereqs (8B model error - takes first item)
            if isinstance(topic["prereq"], list):
                print(f"  ⚠️  Fixing list prereq: {topic['prereq']} → {topic['prereq'][0] if topic['prereq'] else None} for '{topic['id']}'")
                topic["prereq"] = topic["prereq"][0] if topic["prereq"] else None

            # Auto-fix: Map invalid difficulties to valid ones
            if topic["difficulty"] not in valid_difficulties:
                difficulty_map = {"expert": "advanced", "basic": "foundational", "beginner": "foundational"}
                new_difficulty = difficulty_map.get(topic["difficulty"], "intermediate")
                print(f"  ⚠️  Fixing difficulty: '{topic['difficulty']}' → '{new_difficulty}' for '{topic['id']}'")
                topic["difficulty"] = new_difficulty

            assert topic["difficulty"] in valid_difficulties, f"Topic {i} invalid difficulty: {topic['difficulty']}"
        except AssertionError as e:
            print(f"\n=== VALIDATION ERROR ===")
            print(f"Topic index: {i}")
            print(f"Topic value: {topic}")
            print(f"All topics: {topics}")
            print(f"Error: {e}")
            print(f"========================\n")
            raise

        # Check for self-reference
        if topic["prereq"] == topic["id"]:
            raise ValueError(f"Topic '{topic['id']}' cannot be its own prereq")

        # Prereq must exist in topics or be null
        # Auto-fix: Set to null if prereq doesn't exist (handles 8B model imprecision)
        if topic["prereq"] is not None:
            if topic["prereq"] not in topic_id_set:
                print(f"  ⚠️  Fixing invalid prereq: '{topic['prereq']}' → null for topic '{topic['id']}'")
                topic["prereq"] = None

    # Fix #3: Check for circular dependencies using DFS
    def has_cycle(topic_id: str, visited: set, rec_stack: set) -> bool:
        visited.add(topic_id)
        rec_stack.add(topic_id)

        # Find prereq of current topic
        prereq = next((t["prereq"] for t in topics if t["id"] == topic_id), None)
        if prereq:
            if prereq not in visited:
                if has_cycle(prereq, visited, rec_stack):
                    return True
            elif prereq in rec_stack:
                return True

        rec_stack.remove(topic_id)
        return False

    visited = set()
    for topic in topics:
        if topic["id"] not in visited:
            if has_cycle(topic["id"], visited, set()):
                raise ValueError(f"Circular prereq dependency detected involving '{topic['id']}'")

    return topics


def load_prompt_template() -> str:
    """Load job parser prompt from config using config loader"""
    prompts = load_prompts("agent1")
    return prompts["job_parser_prompt"]


def parse_jobs(user_id: int, form_data: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Parse job form data and extract learning topics using Llama 3.3 70B

    Args:
        user_id: User ID for recent skills lookup
        form_data: Dictionary with 12 form fields:
            - current_job_title
            - current_description
            - current_seniority
            - target_job_title
            - target_description
            - target_seniority
            - target_company
            - target_industry

    Returns:
        List of topic dicts with id, prereq, difficulty

    Raises:
        ValueError: If validation fails or LLM returns invalid JSON
    """
    # Get recent skills to skip
    recent_skills = get_recent_skills(user_id, days=30)
    recent_skills_str = ", ".join(recent_skills) if recent_skills else "None"

    # Load prompt template
    prompt_template = load_prompt_template()

    # Fill in template
    prompt = prompt_template.format(
        recent_skills=recent_skills_str,
        current_seniority=form_data.get("current_seniority", ""),
        current_job_title=form_data.get("current_job_title", ""),
        current_description=form_data.get("current_description", ""),
        target_seniority=form_data.get("target_seniority", ""),
        target_job_title=form_data.get("target_job_title", ""),
        target_company=form_data.get("target_company", ""),
        target_description=form_data.get("target_description", "")
    )

    # Load LLM config and call LLM
    agent_config = load_agent_config("agent1_job_parser")
    llm_config = agent_config["llm_config"]
    response, tokens = call_llm(
        prompt,
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"]
    )

    # Parse JSON from response with robust extraction
    import re
    import logging

    logger = logging.getLogger(__name__)
    response_clean = response.strip()

    try:
        # Method 1: Direct parse if starts with [
        if response_clean.startswith("["):
            topics = json.loads(response_clean)

        # Method 2: Extract from markdown code block
        elif "```json" in response_clean or "```" in response_clean:
            match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_clean, re.DOTALL)
            if match:
                topics = json.loads(match.group(1))
            else:
                raise ValueError("Found code block but couldn't extract JSON")

        # Method 3: Find JSON array using bracket matching
        else:
            # Find first [ and match brackets
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
            topics = json.loads(json_str)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode failed: {e}")
        logger.debug(f"Response: {response[:500]}")
        # Print for debugging
        print(f"\n=== JSON DECODE ERROR ===")
        print(f"Error: {e}")
        print(f"Full Response:\n{response}\n")
        print(f"=========================\n")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"JSON extraction failed: {e}")
        logger.debug(f"Response: {response[:500]}")
        # Print for debugging
        print(f"\n=== EXTRACTION ERROR ===")
        print(f"Error: {e}")
        print(f"Full Response:\n{response}\n")
        print(f"========================\n")
        raise ValueError(f"Failed to extract JSON: {e}")

    # Validate structure
    topics = validate_topics_json(topics)

    return topics


if __name__ == "__main__":
    # Quick test
    print("Job Parser Agent ready.")
    print("Use: parse_jobs(user_id, form_data)")
