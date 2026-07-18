"""Thin Claude wrapper: one call shape, JSON in/out, pydantic-validated."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TypeVar

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()  # reads .env at repo root so ANTHROPIC_API_KEY 'just works'

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


def text_of(resp) -> str:
    """Concatenate the text blocks of a response, skipping thinking/tool blocks.
    (Models may emit a ThinkingBlock before the text, so content[0].text is unsafe.)"""
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


def _parse_json(raw: str):
    """Try to load a JSON object from model text: whole string first, then the
    largest brace-delimited span. Returns a dict/list or None."""
    candidates = [raw]
    match = re.search(r"\{.*\}", raw, re.S)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return None


def _repair_json(raw: str, max_tokens: int):
    """Last resort: ask the model to re-emit the payload as strictly valid JSON.
    Handles the occasional unescaped quote / missing delimiter in a long brief."""
    resp = client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=("You are a JSON repair tool. The user message is meant to be a single "
                "JSON object but has syntax errors (unescaped quotes, missing commas, "
                "trailing text, code fences). Output ONLY the corrected, strictly valid "
                "JSON object — no prose, no markdown."),
        messages=[{"role": "user", "content": raw}],
    )
    return _parse_json(text_of(resp))


def call_json(system_prompt: str, user_content: str, out_model: type[T], max_tokens: int = 4096) -> T:
    """One-shot call expecting a single JSON object matching `out_model`.

    Note: no assistant-message prefill — the current default models reject it
    ("conversation must end with a user message"). We instruct the prompt to emit
    JSON only, salvage the object if the model wraps it in prose, and fall back to
    a one-shot repair pass if the JSON itself is malformed."""
    resp = client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt + "\n\nRespond with the JSON object only — no prose, no markdown fences. Escape any double-quotes that appear inside string values.",
        messages=[{"role": "user", "content": user_content}],
    )
    raw = text_of(resp)
    obj = _parse_json(raw)
    if obj is None:
        obj = _repair_json(raw, max_tokens)
    if obj is None:
        raise ValueError(f"could not parse JSON from model output: {raw[:300]!r}")
    return out_model.model_validate(obj)
