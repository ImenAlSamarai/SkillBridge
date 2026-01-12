#!/usr/bin/env python3
"""
LLM Engine for learn_flow
Phase 2A.2: Dual-mode Llama 3.3 70B (Ollama dev + Groq deploy)
"""
import os
from typing import Tuple
from pathlib import Path

# Load .env file from project root (not src/core/)
try:
    from dotenv import load_dotenv
    # .env is in project root, not in src/core/
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, skip


def call_llm(prompt: str, temperature: float = 0.1, max_tokens: int = 2000) -> Tuple[str, int]:
    """
    Dual-mode LLM: Ollama (LOCAL_MODE=true) or Groq (LOCAL_MODE=false)

    SAME FUNCTION SIGNATURE - Zero changes to job_parser.py or topic_assessor.py

    Args:
        prompt: User prompt string
        temperature: Model temperature (default 0.1)
        max_tokens: Maximum tokens in response (default 2000)

    Returns:
        Tuple of (response_text, tokens_used)

    Raises:
        ImportError: If Ollama not installed in LOCAL_MODE
        ValueError: If GROQ_API_KEY not set in deploy mode
    """
    local_mode = os.getenv("LOCAL_MODE", "false").lower() == "true"

    if local_mode:
        # DEV MODE: FREE Ollama (unlimited local inference)
        try:
            import ollama
        except ImportError:
            raise ImportError(
                "Ollama not installed. Install with:\n"
                "  brew install ollama  # macOS\n"
                "  ollama pull llama3.3:70b"
            )

        response = ollama.chat(
            model='llama3.1:8b',  # 8B for local dev (18GB RAM compatible)
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'num_predict': max_tokens,
                'temperature': temperature
            }
        )

        response_text = response['message']['content']
        # Ollama doesn't return token count, estimate as ~4 chars per token
        tokens_used = len(prompt + response_text) // 4

        return response_text, tokens_used

    else:
        # DEPLOY MODE: Groq API (for beta testers)
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set.\n"
                "Set LOCAL_MODE=true for free Ollama, or add GROQ_API_KEY for deploy."
            )

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )

        tokens_used = response.usage.total_tokens
        response_text = response.choices[0].message.content

        return response_text, tokens_used


if __name__ == "__main__":
    # Quick test
    local_mode = os.getenv("LOCAL_MODE", "false").lower() == "true"
    mode_name = "Ollama (LOCAL)" if local_mode else "Groq (DEPLOY)"

    print(f"Testing LLM Engine in {mode_name} mode...")
    print(f"LOCAL_MODE={os.getenv('LOCAL_MODE', 'false')}")
    print()

    try:
        response, tokens = call_llm("Say 'Hello from Llama 3.3 70B!'")
        print(f"✓ Response: {response[:100]}...")
        print(f"✓ Tokens used: {tokens}")
        print(f"\n✅ {mode_name} mode working!")
    except (ValueError, ImportError) as e:
        print(f"❌ Error: {e}")
