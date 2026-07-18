"""Thin Claude wrapper: one call shape, JSON in/out, pydantic-validated."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TypeVar

import anthropic
from pydantic import BaseModel

MODEL = os.environ.get("ALORA_MODEL", "claude-sonnet-5")
PROMPTS = Path(__file__).parent / "prompts"

_client: anthropic.Anthropic | None = None

T = TypeVar("T", bound=BaseModel)


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    return _client


def load_prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text()


def call_json(system_prompt: str, user_content: str, out_model: type[T], max_tokens: int = 4096) -> T:
    """One-shot call expecting a single JSON object matching `out_model`."""
    resp = client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": "{"},  # prefill: force JSON from the first byte
        ],
    )
    raw = "{" + resp.content[0].text
    try:
        return out_model.model_validate_json(raw)
    except Exception:
        # salvage the largest JSON object in the output before giving up
        match = re.search(r"\{.*\}", raw, re.S)
        if match:
            return out_model.model_validate(json.loads(match.group(0)))
        raise
