"""
Configuration loader for learn_flow
Loads and caches YAML configuration files
"""
import yaml
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Set, Any


CONFIG_DIR = Path(__file__).parent / "config"


@lru_cache(maxsize=1)
def load_field_options() -> Dict[str, List[str]]:
    """Load dropdown field options from YAML (cached)"""
    with open(CONFIG_DIR / "fields.yaml") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_admin_emails() -> Set[str]:
    """Load admin email list (cached)"""
    with open(CONFIG_DIR / "admin_users.yaml") as f:
        data = yaml.safe_load(f)
        return set(data.get("admin_emails", []))


@lru_cache(maxsize=1)
def load_golden_sources() -> List[Dict[str, Any]]:
    """Load reference books (cached)"""
    with open(CONFIG_DIR / "golden_sources.yaml") as f:
        return yaml.safe_load(f).get("books", [])


def is_admin_user(email: str) -> bool:
    """Check if email is in admin list"""
    return email in load_admin_emails()
