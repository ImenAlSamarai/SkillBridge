#!/usr/bin/env python3
"""
Content Generator Agent for learn_flow
Phase 3.2: Generate educational content + 3 comprehension questions per module
"""
import json
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, List, Tuple
from src.core.llm_engine import call_llm
from src.core import load_agent_config, load_prompts, load_learning_resources, load_thresholds


# =============================================================================
# GOLDEN RESOURCES - Curated, verified resources (no LLM hallucination)
# =============================================================================

def determine_user_tier(mastery: int, target_seniority: str) -> int:
    """
    Determine user tier (1-3) based on mastery and target role.
    
    Tier 1 (Entry): Interns, career changers, beginners
    Tier 2 (Intermediate): Analysts, junior quants, 1-3 years
    Tier 3 (Advanced): Senior quants, researchers, 5+ years
    """
    entry_keywords = ["intern", "student", "entry", "junior", "graduate", "beginner"]
    advanced_keywords = ["senior", "advanced", "director", "lead", "principal", "head", "vp", "researcher"]
    
    seniority_lower = target_seniority.lower() if target_seniority else ""
    
    if any(kw in seniority_lower for kw in entry_keywords):
        return 1
    elif any(kw in seniority_lower for kw in advanced_keywords):
        return 3
    
    # Use mastery as secondary signal
    if mastery < 30:
        return 1
    elif mastery > 70:
        return 3
    return 2


def get_golden_resources(target_role: str, module_name: str, user_tier: int = 2) -> List[Dict[str, str]]:
    """
    Select verified resources from golden list based on role, topic, and user tier.
    NO LLM HALLUCINATION - only curated, verified URLs.
    
    PRIORITY ORDER:
    1. Topic-specific resources (from role or shared) - MOST RELEVANT
    2. If NO topic matched: tier-appropriate general resources (prevents advanced books for basic topics)
    3. If topic matched but < 2 resources: role's core resources
    4. Final fallback: mathematics tier resources
    
    Args:
        target_role: e.g., "Quant Researcher", "Quant Developer"
        module_name: e.g., "Linear Algebra Fundamentals", "Neural Networks"
        user_tier: 1=Entry, 2=Intermediate, 3=Advanced
    
    Returns:
        List of 2-3 verified resources with text and url
    """
    # Use relative path from project root (consistent with other config loaders)
    config_path = Path("config/resources/golden_resources_by_role.yaml")
    
    try:
        with open(config_path, 'r') as f:
            golden = yaml.safe_load(f)
    except Exception as e:
        print(f"   ⚠️  Could not load golden resources: {e}")
        return []
    
    resources = []
    module_lower = module_name.lower()
    tier_name = f"tier_{user_tier}"
    
    # Detect topic category from module name
    topic_keywords = golden.get("topic_keywords", {})
    matched_category = None
    for category, keywords in topic_keywords.items():
        if any(kw in module_lower for kw in keywords):
            matched_category = category
            break
    
    # Map category to shared section
    category_mapping = {
        "linear_algebra": "mathematics",
        "probability": "mathematics",
        "statistics": "mathematics",
        "calculus": "mathematics",
        "stochastic": "stochastic",
        "time_series": "mathematics",
        "machine_learning": "machine_learning",
        "deep_learning": "machine_learning",
        "python": "programming",
        "algorithms": "programming",
        "derivatives": "stochastic",  # Derivatives need stochastic calculus
        "risk": "risk",  # Risk has its own section with VaR, stress testing resources
        "portfolio": "trading",  # Portfolio management uses trading resources
        "trading": "trading",
        "finance_theory": "trading",  # EMH, CAPM, asset pricing
        # Additional categories
        "fixed_income": "stochastic",  # Yield curves, duration → stochastic/derivatives math
        "credit": "risk",  # Credit risk, CDS → risk section
        "fx": "trading",  # FX, currency → trading section
        "numerical": "stochastic",  # PDEs, finite difference → stochastic math
        "interview": "mathematics",  # Brainteasers, puzzles → probability/math
    }
    
    shared_section = category_mapping.get(matched_category, None)
    roles = golden.get("roles", {})
    shared = golden.get("shared_resources", {})
    
    # =========================================================================
    # STEP 1: Try to find TOPIC-SPECIFIC resources first (most relevant)
    # =========================================================================
    
    # 1a. Check role's topic_resources
    if target_role in roles:
        role_data = roles[target_role]
        topic_resources = role_data.get("topic_resources", {})
        
        for topic_key, topic_res_list in topic_resources.items():
            topic_words = topic_key.replace("_", " ").split()
            if any(word in module_lower for word in topic_words):
                # Found topic match! Add up to 2 topic-specific resources
                for res in topic_res_list[:2]:
                    if res.get("url"):
                        resources.append({
                            "text": f"{res.get('text', '')} {res.get('note', '')}".strip(),
                            "url": res["url"]
                        })
                    elif res.get("text"):
                        resources.append({
                            "text": f"{res.get('text', '')} {res.get('note', '')}".strip(),
                            "url": "#"
                        })
                break
    
    # 1b. Check shared resources for topic category
    if len(resources) < 2 and shared_section and shared_section in shared:
        tier_resources = shared[shared_section].get(tier_name, shared[shared_section].get("tier_2", []))
        for res in tier_resources:
            if len(resources) >= 2:
                break
            # Include resources WITH or WITHOUT URLs (paid books are valid resources)
            url = res.get("url", "#")  # Use "#" for paid books without URLs
            if url not in [r["url"] for r in resources]:
                resources.append({
                    "text": f"{res.get('text', '')} {res.get('note', '')}".strip(),
                    "url": url
                })
    
    # =========================================================================
    # STEP 2: If still < 2 resources and NO topic matched, use tier-appropriate
    # general resources (NOT role's core_resources which may be too advanced)
    # =========================================================================
    if len(resources) < 2 and matched_category is None:
        # No topic matched - use general foundational resources based on tier
        # This prevents advanced books like López de Prado appearing for basic topics
        general_fallback = shared.get("mathematics", {}).get(tier_name, [])
        for res in general_fallback:
            if len(resources) >= 2:
                break
            url = res.get("url", "#")
            if url not in [r["url"] for r in resources]:
                resources.append({
                    "text": f"{res.get('text', '')} {res.get('note', '')}".strip(),
                    "url": url
                })
    
    # =========================================================================
    # STEP 3: If still < 2 resources AND topic matched, add role's core resources
    # (Only use core_resources when we have a topic match, ensuring relevance)
    # =========================================================================
    if len(resources) < 2 and matched_category is not None and target_role in roles:
        role_data = roles[target_role]
        for res in role_data.get("core_resources", []):
            if len(resources) >= 2:
                break
            url = res.get("url", "#")
            if url not in [r["url"] for r in resources]:
                resources.append({
                    "text": f"{res.get('text', '')} {res.get('note', '')}".strip(),
                    "url": url
                })
    
    # =========================================================================
    # STEP 4: Final fallback to mathematics tier resources if still < 2
    # =========================================================================
    if len(resources) < 2:
        math_tier = shared.get("mathematics", {}).get(tier_name, [])
        for res in math_tier:
            if len(resources) >= 2:
                break
            url = res.get("url", "#")
            if url not in [r["url"] for r in resources]:
                resources.append({
                    "text": f"{res.get('text', '')} {res.get('note', '')}".strip(),
                    "url": url
                })
    
    # Remove duplicates and limit to 3
    seen_urls = set()
    unique = []
    for res in resources:
        if res["url"] not in seen_urls:
            seen_urls.add(res["url"])
            unique.append(res)
    
    print(f"   📚 Golden resources: {len(unique[:3])} for '{module_name[:30]}' → {matched_category or 'general'} (Tier {user_tier})")
    return unique[:3]


def load_prompt_template() -> str:
    """Load content generator prompt from config using config loader"""
    prompts = load_prompts("agent3")
    return prompts["content_generator_prompt"]


def check_url_accessible(url: str, timeout: int = 5) -> Tuple[bool, int]:
    """
    Check if a URL is accessible and returns 200 OK
    Special handling for YouTube playlists (check if playlist actually exists)

    Args:
        url: URL to check
        timeout: Request timeout in seconds

    Returns:
        Tuple of (is_accessible, status_code)
    """
    try:
        # Special handling for YouTube playlists
        if 'youtube.com/playlist' in url:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            # YouTube returns 200 even for non-existent playlists
            # Check page content for error indicators
            if response.status_code == 200:
                content = response.text
                content_lower = content.lower()

                # Check for playlist errors/issues
                # 1. Check for "0 videos" or empty playlist
                if ('\"videoCount\":0' in content or
                    '\"videoCount\":\"0\"' in content or
                    '0 videos' in content_lower):
                    print(f"   ⚠️  YouTube playlist is empty (0 videos)")
                    return (False, 404)

                # 2. Check for explicit error messages
                if ('playlist does not exist' in content_lower or
                    'playlist not found' in content_lower or
                    'this playlist is private' in content_lower or
                    'playlist is unavailable' in content_lower):
                    print(f"   ⚠️  YouTube playlist not found or private")
                    return (False, 404)

                # 3. Check for generic unavailability (be cautious)
                # Only flag as error if "unavailable" appears with playlist context
                if 'unavailable' in content_lower and 'playlist' in content_lower[:5000]:
                    # Check if it's in the title or early in the page
                    if 'playlist unavailable' in content_lower[:2000]:
                        print(f"   ⚠️  YouTube playlist unavailable")
                        return (False, 404)

            return (response.status_code == 200, response.status_code)

        # Standard URL check for non-YouTube
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        # Some servers don't support HEAD, try GET if HEAD fails
        if response.status_code == 405:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        return (response.status_code == 200, response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  URL check failed for {url}: {e}")
        return (False, 0)


def get_fallback_references(topic_id: str, module_name: str) -> List[Dict[str, str]]:
    """
    Provide curated, verified fallback references for common topics
    These are guaranteed to work and are well-established resources

    Args:
        topic_id: Topic identifier
        module_name: Module name for context

    Returns:
        List of reference dicts with 'text' and 'url'
    """
    # Load fallback references from config
    resources = load_learning_resources()
    fallback_map = resources["fallback_references"]

    # Check if topic_id has specific fallback references
    if topic_id in fallback_map:
        return fallback_map[topic_id]

    # Return default fallback
    default_refs = [
        {
            "text": f"MIT OpenCourseWare: {module_name}",
            "url": f"https://ocw.mit.edu/search/?q={module_name.replace(' ', '+')}"
        },
        {
            "text": f"Coursera: {module_name}",
            "url": f"https://www.coursera.org/courses?query={module_name.replace(' ', '+')}"
        }
    ]
    return default_refs


def validate_and_fix_references(
    references: List[Dict[str, str]],
    topic_id: str,
    module_name: str
) -> List[Dict[str, str]]:
    """
    Validate reference URLs and replace broken ones with fallback references

    Args:
        references: List of reference dicts with 'text' and 'url'
        topic_id: Topic identifier for fallback selection
        module_name: Module name for fallback generation

    Returns:
        List of validated references with working URLs
    """
    validated_refs = []
    fallback_refs = get_fallback_references(topic_id, module_name)
    fallback_index = 0

    print(f"   🔍 Validating {len(references)} reference URLs...")

    for i, ref in enumerate(references):
        url = ref.get('url', '')
        text = ref.get('text', '').lower()

        # Check for YouTube search results (NOT ALLOWED)
        if 'youtube.com/results?search_query=' in url.lower():
            print(f"      ⚠️  Reference {i+1}: YouTube search results not allowed ({url[:60]}...)")
            print(f"         → Replacing with Coursera or MIT OCW...")

            # Use fallback reference
            if fallback_index < len(fallback_refs):
                fallback_ref = fallback_refs[fallback_index]
                print(f"         → Replaced with: {fallback_ref['url'][:60]}...")
                validated_refs.append(fallback_ref)
                fallback_index += 1
            else:
                print(f"         → Keeping original (no more fallbacks)")
                validated_refs.append(ref)
            continue

        # Check for Khan Academy (NOT ALLOWED - we don't use Khan Academy anymore)
        if 'khanacademy.org' in url.lower():
            print(f"      ⚠️  Reference {i+1}: Khan Academy not allowed ({url[:60]}...)")
            print(f"         → Replacing with Coursera or MIT OCW...")

            # Use fallback reference
            if fallback_index < len(fallback_refs):
                fallback_ref = fallback_refs[fallback_index]
                print(f"         → Replaced with: {fallback_ref['url'][:60]}...")
                validated_refs.append(fallback_ref)
                fallback_index += 1
            else:
                print(f"         → Keeping original (no more fallbacks)")
                validated_refs.append(ref)
            continue

        # Check for YouTube channel homepages (NOT ALLOWED - need specific videos/playlists)
        if 'youtube.com/@' in url.lower() and '/courses' not in url.lower():
            # This is a channel homepage like youtube.com/@statquest
            # We need specific videos or playlists, not channel pages
            print(f"      ⚠️  Reference {i+1}: YouTube channel homepage not allowed ({url[:60]}...)")
            print(f"         → Need specific video/playlist. Replacing...")

            # Use fallback reference
            if fallback_index < len(fallback_refs):
                fallback_ref = fallback_refs[fallback_index]
                print(f"         → Replaced with: {fallback_ref['url'][:60]}...")
                validated_refs.append(fallback_ref)
                fallback_index += 1
            else:
                print(f"         → Keeping original (no more fallbacks)")
                validated_refs.append(ref)
            continue

        # Check for false "FREE" claims (paid publishers)
        paid_publishers = ['packtpub.com', 'manning.com', 'oreilly.com', 'apress.com', 'amazon.com/dp', 'amazon.com/gp']
        claims_free = 'free' in text
        is_paid_publisher = any(publisher in url.lower() for publisher in paid_publishers)

        if claims_free and is_paid_publisher:
            print(f"      ⚠️  Reference {i+1}: Falsely labeled as FREE but URL is paid publisher ({url[:60]}...)")
            print(f"         → This is Packt/Manning/O'Reilly/Amazon - NOT FREE! Replacing...")

            # Use fallback reference
            if fallback_index < len(fallback_refs):
                fallback_ref = fallback_refs[fallback_index]
                print(f"         → Replaced with truly FREE resource: {fallback_ref['url'][:60]}...")
                validated_refs.append(fallback_ref)
                fallback_index += 1
            else:
                print(f"         → Keeping original (no more fallbacks)")
                validated_refs.append(ref)
            continue

        # Check if URL is accessible
        is_accessible, status_code = check_url_accessible(url)

        if is_accessible:
            print(f"      ✅ Reference {i+1}: {url[:60]}... (Status: {status_code})")
            validated_refs.append(ref)
        else:
            print(f"      ❌ Reference {i+1}: {url[:60]}... (Status: {status_code}) - Using fallback")

            # Use fallback reference
            if fallback_index < len(fallback_refs):
                fallback_ref = fallback_refs[fallback_index]
                print(f"         → Replaced with: {fallback_ref['url'][:60]}...")
                validated_refs.append(fallback_ref)
                fallback_index += 1
            else:
                # If we run out of fallbacks, keep the original (at least the text is useful)
                print(f"         → Keeping original (no more fallbacks)")
                validated_refs.append(ref)

    return validated_refs


def get_depth_instructions(depth_score: float) -> Dict[str, str]:
    """
    Map depth score to LLM instructions

    Args:
        depth_score: 0.0 to 1.0

    Returns:
        Dictionary with depth_level, explanation_style, question_difficulty
    """
    # Depth thresholds are part of the algorithm logic
    # (not user-configurable parameters, so kept in code)
    if depth_score < 0.35:
        return {
            "depth_level": "Beginner",
            "explanation_style": "simple analogies and step-by-step breakdowns with everyday examples",
            "question_difficulty": "basic recall and simple application of concepts"
        }
    elif depth_score < 0.65:
        return {
            "depth_level": "Intermediate",
            "explanation_style": "clear explanations with practical examples and real-world applications",
            "question_difficulty": "understanding, problem-solving, and practical application"
        }
    else:
        return {
            "depth_level": "Advanced",
            "explanation_style": "technical detail, mathematical rigor, and theoretical foundations",
            "question_difficulty": "deep understanding, synthesis, and advanced problem-solving"
        }


def reframe_module_for_user(
    module_name: str,
    user_context: Dict[str, Any]
) -> str:
    """
    Reframe a generic module name based on user's context

    Example:
    - "Market Fundamentals" + Quant Researcher → Quant Trader @ Citadel
    - Becomes: "Market Microstructure for Quantitative Trading"

    Args:
        module_name: Generic module name (e.g., "Market Fundamentals")
        user_context: User's current/target job context

    Returns:
        Reframed module name tailored to user transition
    """
    if not user_context or user_context.get("mastery", 0) < 50:
        # For beginners or without context, keep original name
        return module_name

    current_job = user_context.get("current_job_title", "Professional")
    target_job = user_context.get("target_job_title", "Senior Professional")
    target_company = user_context.get("target_company", "Industry")
    mastery = user_context.get("mastery", 0)

    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Module Name Reframing Agent. Reframe generic module names for specific user transitions.

**TASK**: Reframe "{module_name}" for this user transition:
- Current role: {current_job}
- Target role: {target_job} @ {target_company}
- Current mastery of this topic: {mastery}%

**RULES**:
- If mastery > 50%: Focus on advanced applications, NOT basics
- Match target role: Trader → trading/execution, Researcher → modeling, Engineer → systems
- Keep it concise: 3-6 words max
- Make it actionable and specific

**EXAMPLES**:
- "Market Fundamentals" + Quant Trader @ Citadel → "Market Microstructure for HFT"
- "Data Analysis" + ML Engineer → Senior → "Production ML Pipeline Analysis"
- "Python Basics" + Already knows Python → "Python Optimization Techniques"

**OUTPUT**: Return ONLY the reframed module name, nothing else.

<|eot_id|><|start_header_id|>user<|end_header_id|>

Reframe: "{module_name}"<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    try:
        # Load LLM config for reframing
        agent_config = load_agent_config("agent3_content_generator")
        reframe_config = agent_config["llm_config"]["module_reframing"]

        response, _ = call_llm(
            prompt,
            temperature=reframe_config["temperature"],
            max_tokens=reframe_config["max_tokens"]
        )
        reframed = response.strip().strip('"').strip("'")

        # Validate it's not too long or just the original
        if len(reframed.split()) <= 8 and reframed != module_name:
            return reframed
        else:
            return module_name
    except Exception as e:
        print(f"Warning: Failed to reframe module name: {e}")
        return module_name


def generate_module_names(
    topic_id: str,
    target_role: str = None,
    target_seniority: str = None,
    mastery: int = 0
) -> Dict[int, str]:
    """
    Generate names for all 8 modules in a single LLM call.
    
    Module names are tailored to:
    - Target role (e.g., "Quant Trader" → trading-focused modules)
    - Target seniority (e.g., "Senior" → advanced topics, skip basics)
    - Current mastery (e.g., 70% → focus on gaps, not fundamentals)

    Args:
        topic_id: Topic identifier (e.g., "python", "derivative_pricing")
        target_role: Target job title (e.g., "Quant Trader", "ML Engineer")
        target_seniority: Target seniority level (e.g., "Junior", "Senior")
        mastery: Current mastery percentage (0-100)

    Returns:
        Dictionary mapping module_id (1-8) to module names
    """
    # Build role context
    role_context = ""
    if target_role:
        role_context = f"""
**TARGET ROLE**: {target_seniority or 'Mid-level'} {target_role}
**USER'S CURRENT MASTERY**: {mastery}%

**CRITICAL CONSTRAINTS**:
- Focus ONLY on aspects of "{topic_id}" relevant to {target_role}
- If mastery > 50%: Skip basics, focus on advanced applications
- If mastery < 30%: Include foundational concepts
- Each module must cover a DIFFERENT subtopic (NO OVERLAP)

**ROLE-SPECIFIC EXAMPLES**:
- "Python" for Quant Trader → backtesting, execution, vectorization, NOT web dev
- "Python" for ML Engineer → sklearn, pytorch, pipelines, NOT trading
- "Statistics" for Risk Analyst → VaR, stress testing, NOT A/B testing
- "Linear Algebra" for Quant Researcher → PCA, optimization, covariance, NOT graphics
"""
    
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Module Name Generator. Create 8 DISTINCT module names for a specific learning path.

**TASK**: Generate 8 module names for topic "{topic_id}"
{role_context}
**MODULE PROGRESSION**:
- Modules 1-2: Foundational concepts (or intermediate if mastery > 50%)
- Modules 3-4: Core principles and techniques
- Modules 5-6: Advanced topics and edge cases
- Modules 7-8: Real-world applications & synthesis

**REQUIREMENTS**:
- Each name: 2-5 words, clear and SPECIFIC
- Each module covers a DISTINCT subtopic (zero overlap)
- Progressive difficulty from module 1 to 8
- Names should be specific enough that content won't overlap

**GOOD EXAMPLE** (Python for Quant Trader):
{{
  "1": "NumPy Array Operations",
  "2": "Pandas Time Series",
  "3": "Vectorized Backtesting",
  "4": "Order Book Data Handling",
  "5": "Async Execution Patterns",
  "6": "Memory Optimization",
  "7": "Production Code Patterns",
  "8": "Testing Trading Systems"
}}

**BAD EXAMPLE** (overlapping, generic):
{{
  "1": "Introduction to Python",
  "2": "Python Basics",
  "3": "Python Fundamentals",
  ...
}}

**JSON OUTPUT** (STRICT):
{{
  "1": "Module 1 Name",
  "2": "Module 2 Name",
  "3": "Module 3 Name",
  "4": "Module 4 Name",
  "5": "Module 5 Name",
  "6": "Module 6 Name",
  "7": "Module 7 Name",
  "8": "Module 8 Name"
}}

RETURN ONLY THE JSON OBJECT.

<|eot_id|><|start_header_id|>user<|end_header_id|>

Generate 8 DISTINCT module names for topic: {topic_id}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

    try:
        # Load LLM config for module name generation
        agent_config = load_agent_config("agent3_content_generator")
        module_names_config = agent_config["llm_config"]["module_naming"]

        response, _ = call_llm(
            prompt,
            temperature=module_names_config["temperature"],
            max_tokens=module_names_config["max_tokens"]
        )

        # Parse JSON
        import re
        response_clean = response.strip()

        # Extract JSON object
        if response_clean.startswith("{"):
            names_data = json.loads(response_clean)
        else:
            # Find JSON object
            start_idx = response_clean.find("{")
            if start_idx == -1:
                raise ValueError("No JSON object found")

            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response_clean)):
                if response_clean[i] == '{':
                    brace_count += 1
                elif response_clean[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

            json_str = response_clean[start_idx:end_idx]
            names_data = json.loads(json_str)

        # Convert string keys to integers
        module_names = {int(k): v for k, v in names_data.items()}

        # Validate we have all 8 modules
        assert all(i in module_names for i in range(1, 9)), "Missing module names"

        return module_names

    except Exception as e:
        # Fallback to generic names
        print(f"Warning: Failed to generate module names: {e}")
        return {i: f"Module {i}" for i in range(1, 9)}


def clean_json_string(json_str: str) -> str:
    """
    Clean JSON string by fixing common LLM JSON formatting errors

    LLMs sometimes output JSON with:
    1. Literal newlines in string values (invalid)
    2. Invalid escape sequences like \$ or LaTeX \frac, \sigma (should be escaped)
    3. Bold markdown ** mixed with escaped chars

    This function cleans these issues to make JSON parseable while preserving
    LaTeX rendering (e.g., \sigma becomes \\sigma in JSON, which parses to \sigma).
    """
    import re

    # Step 1: Replace literal newlines with space
    cleaned = json_str.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

    # Step 2: Fix ALL invalid escape sequences using regex
    # JSON only allows: \" \\ \/ \b \f \n \r \t \uXXXX
    # Any other \X is invalid and needs to be \\X for JSON parsing
    # This preserves LaTeX: \sigma -> \\sigma in JSON -> \sigma after parsing
    
    def fix_escape(match):
        full_match = match.group(0)  # e.g., \sigma, \$, \"
        char = match.group(1)        # e.g., s, $, "
        
        # Valid JSON escapes - leave alone
        if char in '"\\bfnrt/':
            return full_match
        # Unicode escape \uXXXX - leave alone  
        if char == 'u':
            return full_match
        # Everything else (LaTeX \sigma, \frac, etc.) - double the backslash
        # This turns \sigma into \\sigma in JSON string
        # When JSON parses \\sigma, it becomes \sigma in the actual string
        # Then LaTeX/Markdown can render \sigma as σ
        return '\\\\' + char
    
    # Match backslash followed by any character
    cleaned = re.sub(r'\\(.)', fix_escape, cleaned)

    # Step 3: Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned


def generate_content(
    topic_id: str,
    module_id: int,
    module_name: str = None,
    depth_score: float = 0.5,
    user_context: Dict[str, Any] = None,
    all_module_names: Dict[int, str] = None
) -> Dict[str, Any]:
    """
    Generate educational content and 3 questions for a topic module

    Args:
        topic_id: Topic identifier (e.g., "linear_algebra")
        module_id: Module number (1-8)
        module_name: Pre-generated module name (optional)
        depth_score: Content depth 0.0 (basic) to 1.0 (expert)
        user_context: Dictionary with user's current/target job info, mastery, etc.
            Expected keys:
            - current_seniority: e.g., "Advanced"
            - current_job_title: e.g., "Quant Researcher"
            - current_description: e.g., "Building statistical models..."
            - target_seniority: e.g., "Advanced"
            - target_job_title: e.g., "Quant Trader"
            - target_description: e.g., "Designing trading strategies..."
            - target_company: e.g., "Citadel"
            - mastery: Current mastery % for this topic (0-100)
        all_module_names: Dictionary mapping module_id (1-8) to module names.
            Used to prevent content overlap between modules.

    Returns:
        Dictionary with:
        - module_name: Short descriptive name for the module
        - content: 400-500 word explanation in 4-5 numbered sections with bold formatting
        - key_concepts: List of 3-5 essential concepts
        - questions: List of 3 question dicts with id, text, correct_answer, explanation
        - references: List of quality learning resources

    Raises:
        ValueError: If LLM returns invalid JSON or missing fields
    """
    # Get depth instructions
    depth_instructions = get_depth_instructions(depth_score)

    # Load prompt template
    prompt_template = load_prompt_template()

    # Prepare user context with defaults
    if user_context is None:
        user_context = {}

    ctx = {
        "current_seniority": user_context.get("current_seniority", "Intermediate"),
        "current_job_title": user_context.get("current_job_title", "Professional"),
        "current_description": user_context.get("current_description", "General background"),
        "target_seniority": user_context.get("target_seniority", "Advanced"),
        "target_job_title": user_context.get("target_job_title", "Senior Professional"),
        "target_description": user_context.get("target_description", "Advanced skills required"),
        "target_company": user_context.get("target_company", "Industry"),
        "mastery": user_context.get("mastery", 0)
    }

    # CRITICAL: Reframe module name based on user context
    # This ensures "Market Fundamentals" → "Market Microstructure for HFT" for advanced traders
    # BUT: DO NOT reframe foundational modules (depth < foundational_threshold or contains keywords)
    original_module_name = module_name if module_name else f"Module {module_id}"

    # Load thresholds from config
    thresholds = load_thresholds()
    content_config = thresholds["content_personalization"]
    foundational_threshold = content_config["foundational_threshold"]
    reframing_threshold = content_config["reframing_threshold"]
    skip_basics_mastery = content_config["skip_basics_mastery"]
    foundational_keywords = content_config["foundational_keywords"]

    # Check if this is a foundational module
    is_foundational = (
        depth_score < foundational_threshold or
        any(keyword in original_module_name.lower() for keyword in foundational_keywords)
    )

    if user_context and ctx["mastery"] >= skip_basics_mastery and not is_foundational and depth_score >= reframing_threshold:
        reframed_module_name = reframe_module_for_user(original_module_name, user_context)
        print(f"   🔄 Reframed: '{original_module_name}' → '{reframed_module_name}'")
        module_name = reframed_module_name
    else:
        module_name = original_module_name
        if is_foundational:
            print(f"   📚 Foundational module: '{original_module_name}' (depth={depth_score:.2f}) - NO reframing")

    # Build curriculum context string for preventing overlap
    if all_module_names:
        curriculum_lines = []
        for i in range(1, 9):
            name = all_module_names.get(i, f"Module {i}")
            marker = "← YOU ARE HERE" if i == module_id else ""
            curriculum_lines.append(f"  Module {i}: {name} {marker}")
        curriculum_str = "\n".join(curriculum_lines)
    else:
        curriculum_str = "(Not provided - generate standalone content)"

    # Fill in template with all variables (module_name is already set above)
    prompt = prompt_template.format(
        topic_id=topic_id,
        module_id=module_id,
        module_name=module_name,
        depth_score=depth_score,
        depth_level=depth_instructions["depth_level"],
        explanation_style=depth_instructions["explanation_style"],
        question_difficulty=depth_instructions["question_difficulty"],
        current_seniority=ctx["current_seniority"],
        current_job_title=ctx["current_job_title"],
        current_description=ctx["current_description"],
        target_seniority=ctx["target_seniority"],
        target_job_title=ctx["target_job_title"],
        target_description=ctx["target_description"],
        target_company=ctx["target_company"],
        mastery=ctx["mastery"],
        all_module_names=curriculum_str
    )

    # Load LLM config and call LLM
    agent_config = load_agent_config("agent3_content_generator")
    content_gen_config = agent_config["llm_config"]["content_generation"]
    response, tokens = call_llm(
        prompt,
        temperature=content_gen_config["temperature"],
        max_tokens=content_gen_config["max_tokens"]
    )

    # Parse JSON from response
    import re
    import logging

    logger = logging.getLogger(__name__)
    response_clean = response.strip()

    try:
        # Helper function to parse JSON with fallback to cleaning
        def parse_json_with_fallback(json_str: str) -> dict:
            """Try direct parse, fall back to clean_json_string if needed."""
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode failed ({e}), attempting to clean JSON string")
                json_str_clean = clean_json_string(json_str)
                return json.loads(json_str_clean)
        
        # Method 1: Direct parse if starts with {
        if response_clean.startswith("{"):
            content_data = parse_json_with_fallback(response_clean)

        # Method 2: Extract from markdown code block
        elif "```json" in response_clean or "```" in response_clean:
            # Extract JSON from markdown code block
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_clean, re.DOTALL)
            if match:
                json_str = match.group(1)
                content_data = parse_json_with_fallback(json_str)
            else:
                raise ValueError("Found code block but couldn't extract JSON")

        # Method 3: Find JSON object using brace matching
        else:
            start_idx = response_clean.find("{")
            if start_idx == -1:
                logger.error(f"No JSON object found in response: {response[:300]}")
                raise ValueError("Response contains no JSON object")

            # Count braces to find matching }
            brace_count = 0
            end_idx = start_idx
            for i in range(start_idx, len(response_clean)):
                if response_clean[i] == '{':
                    brace_count += 1
                elif response_clean[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break

            if brace_count != 0:
                logger.error(f"Unmatched braces in response: {response[:300]}")
                raise ValueError("Unmatched braces in JSON object")

            json_str = response_clean[start_idx:end_idx]
            content_data = parse_json_with_fallback(json_str)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode failed: {e}")
        logger.debug(f"Response: {response[:500]}")
        print(f"\n=== JSON DECODE ERROR ===")
        print(f"Error: {e}")
        print(f"Full Response:\n{response}\n")
        print(f"=========================\n")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"JSON extraction failed: {e}")
        logger.debug(f"Response: {response[:500]}")
        print(f"\n=== EXTRACTION ERROR ===")
        print(f"Error: {e}")
        print(f"Full Response:\n{response}\n")
        print(f"========================\n")
        raise ValueError(f"Failed to extract JSON: {e}")

    # =========================================================================
    # TRUNCATION DETECTION - Check if content appears to be cut off
    # =========================================================================
    content_text = content_data.get("content", "") if isinstance(content_data.get("content"), str) else ""
    word_count = len(content_text.split())
    
    # Detect potential truncation indicators
    truncation_indicators = [
        "..." in content_text[-50:] if len(content_text) > 50 else False,  # Ellipsis at end
        content_text.rstrip().endswith((",", ":", "-", "(")),  # Cut off mid-sentence
        word_count < 300,  # Significantly below 600-700 word target
    ]
    
    if any(truncation_indicators) and word_count < 400:
        logger.warning(f"⚠️  POSSIBLE TRUNCATION DETECTED: Content has only {word_count} words (target: 600-700)")
        print(f"\n   ⚠️  WARNING: Content may be truncated ({word_count} words, target: 600-700)")
        print(f"   Consider increasing max_tokens in agent3_content_generator.yaml")
    
    # Validate structure
    assert isinstance(content_data, dict), "Content must be object"
    assert "module_name" in content_data, "Missing 'module_name' field"
    assert "content" in content_data, "Missing 'content' field"
    assert "key_concepts" in content_data, "Missing 'key_concepts' field"
    assert "questions" in content_data, "Missing 'questions' field"
    assert "references" in content_data, "Missing 'references' field"

    # Validate questions
    questions = content_data["questions"]
    assert isinstance(questions, list), "Questions must be array"
    assert len(questions) == 3, f"Must have exactly 3 questions, got {len(questions)}"

    for i, q in enumerate(questions):
        assert isinstance(q, dict), f"Question {i} must be object"
        assert "id" in q, f"Question {i} missing 'id'"
        assert "text" in q, f"Question {i} missing 'text'"
        assert "correct_answer" in q, f"Question {i} missing 'correct_answer'"
        assert "explanation" in q, f"Question {i} missing 'explanation'"

    # Validate references
    references = content_data["references"]
    assert isinstance(references, list), "References must be array"
    assert len(references) >= 2, f"Must have at least 2 references, got {len(references)}"

    # Validate each reference has text and url
    for i, ref in enumerate(references):
        if isinstance(ref, dict):
            assert "text" in ref, f"Reference {i} missing 'text' field"
            assert "url" in ref, f"Reference {i} missing 'url' field"
            assert ref["url"].startswith("http"), f"Reference {i} URL must start with http"
        # Allow legacy string format for backward compatibility
        elif not isinstance(ref, str):
            raise AssertionError(f"Reference {i} must be dict with text/url or string")

    # Validate key concepts
    key_concepts = content_data["key_concepts"]
    assert isinstance(key_concepts, list), "Key concepts must be array"
    assert 3 <= len(key_concepts) <= 5, f"Must have 3-5 key concepts, got {len(key_concepts)}"

    # =========================================================================
    # REPLACE LLM REFERENCES WITH GOLDEN RESOURCES (NO HALLUCINATION)
    # =========================================================================
    # Instead of validating potentially hallucinated LLM references,
    # we completely replace them with curated, verified resources
    print(f"\n   📚 Using Golden Resources (no LLM hallucination):")
    
    # Determine user tier from context
    target_role = ctx.get("target_job_title", "Quant Analyst")
    target_seniority = ctx.get("target_seniority", "Intermediate")
    mastery = ctx.get("mastery", 50)
    user_tier = determine_user_tier(mastery, target_seniority)
    
    # Get golden resources based on role, module, and tier
    golden_refs = get_golden_resources(
        target_role=target_role,
        module_name=module_name or f"Topic {topic_id} Module {module_id}",
        user_tier=user_tier
    )
    
    # Use golden resources if available, otherwise fall back to validated LLM refs
    if golden_refs:
        content_data["references"] = golden_refs
    else:
        # Fallback: validate LLM references (legacy behavior)
        print(f"   ⚠️  No golden resources found, falling back to LLM validation")
        validated_references = validate_and_fix_references(
            references=content_data["references"],
            topic_id=topic_id,
            module_name=module_name or f"Topic {topic_id} Module {module_id}"
        )
        content_data["references"] = validated_references

    return content_data


if __name__ == "__main__":
    # Quick test
    print("Content Generator Agent ready.")
    print("Use: generate_content(topic_id, module_id)")
    print("\nExample test:")
    try:
        result = generate_content("linear_algebra", 1)
        print(f"✓ Content length: {len(result['content'])} chars")
        print(f"✓ Questions: {len(result['questions'])}")
        print(f"✓ References: {len(result['references'])}")
        print(f"\nFirst question: {result['questions'][0]['text']}")
    except Exception as e:
        print(f"✗ Error: {e}")
