#!/usr/bin/env python3
"""
Core calculation functions for learn_flow
Depth scoring, mastery estimation, and other mathematical operations
"""
from typing import Dict, Any
from src.core import load_thresholds


def calculate_depth_score(target_seniority: str, initial_mastery: int, module_id: int) -> float:
    """
    Calculate content depth score with natural progression through modules

    Args:
        target_seniority: "Student", "Junior", "Intermediate", "Senior", "Advanced"
        initial_mastery: 0-100% current mastery of this topic
        module_id: 1-8 module number

    Returns:
        Depth score: 0.0 (very basic) to 1.0 (expert)

    Example:
        >>> calculate_depth_score("Student", 0, 1)
        0.11
        >>> calculate_depth_score("Advanced", 80, 8)
        1.0
    """
    # Load thresholds from config
    thresholds = load_thresholds()
    depth_config = thresholds["depth_calculation"]

    # Map seniority to base level (from config)
    seniority_map = depth_config["seniority_levels"]
    base_level = seniority_map.get(target_seniority, 0.5)

    # Mastery level (0.0 to 1.0)
    mastery_level = initial_mastery / 100.0

    # User's starting depth (weights from config)
    weights = depth_config["weights"]
    user_depth = (weights["target_seniority"] * base_level) + (weights["mastery"] * mastery_level)

    # Module progression bonus (from config)
    module_config = depth_config["module_progression"]
    max_bonus = module_config["max_bonus"]
    divisor = module_config["divisor"]
    module_bonus = (module_id - 1) / divisor

    # Final depth with natural progression
    depth_score = user_depth + module_bonus

    # Cap at max_depth (from config)
    max_depth = depth_config.get("max_depth", 1.0)
    return min(round(depth_score, 2), max_depth)


def get_seniority_level(seniority: str) -> float:
    """
    Get the base level for a seniority (0.0 to 1.0)

    Args:
        seniority: "Student", "Junior", "Intermediate", "Senior", "Advanced"

    Returns:
        Base level from config (0.0 to 1.0)

    Example:
        >>> get_seniority_level("Student")
        0.15
        >>> get_seniority_level("Advanced")
        1.0
    """
    thresholds = load_thresholds()
    seniority_map = thresholds["depth_calculation"]["seniority_levels"]
    return seniority_map.get(seniority, 0.5)


def is_foundational_content(depth_score: float, module_name: str = "") -> bool:
    """
    Determine if content should be foundational (basic) level

    Args:
        depth_score: Calculated depth score (0.0 to 1.0)
        module_name: Optional module name to check for keywords

    Returns:
        True if content should be foundational/basic

    Example:
        >>> is_foundational_content(0.2)
        True
        >>> is_foundational_content(0.5, "Statistical Basis")
        True
        >>> is_foundational_content(0.8, "Advanced Derivatives")
        False
    """
    thresholds = load_thresholds()
    content_config = thresholds["content_personalization"]

    foundational_threshold = content_config["foundational_threshold"]
    foundational_keywords = content_config["foundational_keywords"]

    # Check depth score
    if depth_score < foundational_threshold:
        return True

    # Check module name for foundational keywords
    if module_name:
        module_lower = module_name.lower()
        if any(keyword in module_lower for keyword in foundational_keywords):
            return True

    return False
