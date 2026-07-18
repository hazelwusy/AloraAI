"""Deterministic span verifier — the trust gate of the whole pipeline.

An agent claim survives only if its citation quote is actually present in the
source document. Matching is whitespace-normalized and case-insensitive, with a
light fuzzy fallback for punctuation drift, but it is NOT semantic: if the model
paraphrased, the claim is dropped and surfaced in `dropped_claims`.
"""
from __future__ import annotations

import re

from .schemas import Citation, Fact, MinerOutput


def _normalize(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace; return normalized text + map from normalized index
    back to original index so we can report true offsets."""
    out: list[str] = []
    index_map: list[int] = []
    prev_space = False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_space and out:
                out.append(" ")
                index_map.append(i)
            prev_space = True
        else:
            out.append(ch.lower())
            index_map.append(i)
            prev_space = False
    return "".join(out), index_map


def _strip_punct(s: str) -> str:
    return re.sub(r"[^\w\s]", "", s)


def verify_citation(citation: Citation, sources: dict[str, str]) -> Citation:
    source_text = sources.get(citation.source, "")
    if not source_text:
        citation.verified = False
        return citation

    norm_src, index_map = _normalize(source_text)
    norm_quote, _ = _normalize(citation.quote)

    pos = norm_src.find(norm_quote)
    if pos < 0:
        # fuzzy fallback: ignore punctuation on both sides
        pos = _strip_punct(norm_src).find(_strip_punct(norm_quote))
        if pos < 0:
            citation.verified = False
            return citation
        # punctuation-stripped offsets don't map cleanly; mark verified without offsets
        citation.verified = True
        return citation

    citation.start = index_map[pos]
    citation.end = index_map[min(pos + len(norm_quote) - 1, len(index_map) - 1)] + 1
    citation.verified = True
    return citation


def verify_facts(miner: MinerOutput, sources: dict[str, str]) -> tuple[MinerOutput, list[Fact]]:
    """Return (verified_output, dropped). A fact survives if >=1 citation verifies;
    unverified citations are removed from surviving facts."""
    kept: list[Fact] = []
    dropped: list[Fact] = []
    for fact in miner.facts:
        fact.citations = [verify_citation(c, sources) for c in fact.citations]
        verified = [c for c in fact.citations if c.verified]
        if verified:
            fact.citations = verified
            kept.append(fact)
        else:
            dropped.append(fact)
    return MinerOutput(encounter_id=miner.encounter_id, facts=kept), dropped
