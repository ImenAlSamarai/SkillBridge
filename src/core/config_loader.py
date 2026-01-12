#!/usr/bin/env python3
"""
Config Loader - Simple YAML config file loader with basic caching
No overengineering - just load files and return dicts
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


# Simple cache - just a dict to avoid reloading same files
_config_cache: Dict[str, Dict[str, Any]] = {}


def _load_yaml(file_path: Path) -> Dict[str, Any]:
    """
    Load a YAML file and return parsed data

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML data as dict

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If file has invalid YAML syntax
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Config file is empty: {file_path}")

    return data


def load_agent_config(agent_name: str) -> Dict[str, Any]:
    """
    Load agent configuration from config/agents/{agent_name}.yaml

    Args:
        agent_name: Agent name (e.g., "agent1_job_parser", "agent2_topic_assessor")

    Returns:
        Agent configuration dict

    Example:
        >>> config = load_agent_config("agent1_job_parser")
        >>> print(config["llm_config"]["temperature"])
        0.3
    """
    cache_key = f"agent_{agent_name}"

    if cache_key in _config_cache:
        return _config_cache[cache_key]

    config_path = Path("config/agents") / f"{agent_name}.yaml"
    config = _load_yaml(config_path)

    _config_cache[cache_key] = config
    return config


def load_prompts(agent_name: str) -> Dict[str, Any]:
    """
    Load agent prompts from config/prompts/{agent_name}_prompts.yaml

    Args:
        agent_name: Agent name (e.g., "agent1", "agent2", "agent3")

    Returns:
        Prompts dict with prompt templates

    Example:
        >>> prompts = load_prompts("agent1")
        >>> print(prompts["job_parser_prompt"])
    """
    cache_key = f"prompts_{agent_name}"

    if cache_key in _config_cache:
        return _config_cache[cache_key]

    config_path = Path("config/prompts") / f"{agent_name}_prompts.yaml"
    prompts = _load_yaml(config_path)

    _config_cache[cache_key] = prompts
    return prompts


def load_thresholds() -> Dict[str, Any]:
    """
    Load thresholds configuration from config/thresholds.yaml

    Returns:
        Thresholds dict with all calculation parameters

    Example:
        >>> thresholds = load_thresholds()
        >>> print(thresholds["depth_calculation"]["foundational_threshold"])
        0.3
    """
    cache_key = "thresholds"

    if cache_key in _config_cache:
        return _config_cache[cache_key]

    config_path = Path("config/thresholds.yaml")
    thresholds = _load_yaml(config_path)

    _config_cache[cache_key] = thresholds
    return thresholds


def load_learning_resources() -> Dict[str, Any]:
    """
    Load learning resources from config/resources/learning_resources.yaml

    Returns:
        Learning resources dict with fallback references, blocked sources, etc.

    Example:
        >>> resources = load_learning_resources()
        >>> fallbacks = resources["fallback_references"]["machine_learning"]
    """
    cache_key = "learning_resources"

    if cache_key in _config_cache:
        return _config_cache[cache_key]

    config_path = Path("config/resources/learning_resources.yaml")
    resources = _load_yaml(config_path)

    _config_cache[cache_key] = resources
    return resources


def clear_cache() -> None:
    """
    Clear the config cache - useful for testing or reloading configs
    """
    global _config_cache
    _config_cache.clear()
