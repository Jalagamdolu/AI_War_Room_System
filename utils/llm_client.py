"""
LLM Client Interface
--------------------
Handles API calls to OpenAI while keeping the rest of the application
decoupled from specific LLM vendors.
"""

from __future__ import annotations

import os
from datetime import datetime

import openai

# Retrieve API key dynamically. The python-dotenv load happens in main.py or top-level.
_CLIENT = None

def _get_client() -> openai.OpenAI | None:
    global _CLIENT
    if _CLIENT is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        _CLIENT = openai.OpenAI(api_key=api_key)
    return _CLIENT

def _log_llm(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[LLM] [{ts}] {msg}")

def call_llm(system_prompt: str, user_prompt: str) -> str | None:
    """
    Call the OpenAI API using gpt-4o-mini.
    Returns the text response, or None if the API key is not configured or an error occurs.
    """
    client = _get_client()
    if not client:
        _log_llm("No OPENAI_API_KEY found in environment. Skipping LLM call.")
        return None

    _log_llm(f"Calling OpenAI for reasoning...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=600,
        )
        _log_llm("OpenAI call successful.")
        return response.choices[0].message.content.strip() if response.choices else None
    except Exception as e:
        _log_llm(f"Error calling OpenAI API: {e}")
        return None
