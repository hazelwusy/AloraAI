"""Typed contracts between agents. Every claim carries a citation; the grounding
verifier enforces that the citation is real before anything reaches the packet."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

SourceDoc = Literal["transcript", "note", "fhir"]

FactCategory = Literal[
    "medication",        # drug, dose, schedule, recent changes
    "allergy",           # allergen + reaction, severity
    "functional",        # mobility, transfers, ADLs, assist level
    "risk",              # falls, aspiration, skin integrity, safety flags
    "goals_of_care",     # patient's stated goals — keep verbatim
    "caregiver",         # tasks/commitments assigned to family or staff
    "pending",           # follow-ups, labs, appointments promised
    "context",           # living situation, language, sensitive constraints
]


class Citation(BaseModel):
    """A verbatim span in a source document. `quote` must appear in the source
    text exactly (after whitespace normalization) or the claim is dropped."""
    source: SourceDoc
    quote: str = Field(min_length=8, description="verbatim excerpt from the source")
    # filled in by the grounding verifier:
    start: Optional[int] = None
    end: Optional[int] = None
    verified: bool = False


class Fact(BaseModel):
    """One transferable fact extracted by the Context Miner."""
    category: FactCategory
    statement: str = Field(description="the fact, stated for the receiving clinician")
    citations: list[Citation] = Field(min_length=1)
    sensitive: bool = Field(
        default=False,
        description="true if disclosure needs channel control (IPV, substance use, psych screens)",
    )


class MinerOutput(BaseModel):
    encounter_id: str
    facts: list[Fact]


class PacketSection(BaseModel):
    title: str
    body_md: str = Field(description="markdown; verbatim patient quotes in blockquotes")
    fact_indices: list[int] = Field(description="indices into MinerOutput.facts backing this section")


class TransferPacket(BaseModel):
    encounter_id: str
    one_liner: str
    sections: list[PacketSection]
    sensitive_addendum: Optional[str] = Field(
        default=None,
        description="sensitive content routed to a controlled channel, never the fax cover",
    )


class GapQuestion(BaseModel):
    question: str
    why_it_matters: str
    category: FactCategory


class GapReport(BaseModel):
    encounter_id: str
    questions: list[GapQuestion]


class PipelineResult(BaseModel):
    encounter_id: str
    visit_title: str
    miner: MinerOutput
    dropped_claims: list[Fact] = Field(description="claims that failed grounding — shown in UI for honesty")
    packet: TransferPacket
    gaps: GapReport


# ---- placement call (voice agent) ----

CallOutcomeKind = Literal["accepted", "declined", "info_requested"]


class CallOutcome(BaseModel):
    outcome: CallOutcomeKind
    reason: str
    bed_hold_until: Optional[str] = None
    documents_requested: list[str] = []
    callback: Optional[str] = None
    next_step_for_nurse: str
    flagged_questions: list[str] = []


class CallResult(BaseModel):
    facility_id: str
    transcript: list[dict]  # [{"speaker": "agent"|"intake", "text": str}]
    outcome: CallOutcome
    simulated_far_end: bool = True


# ---- referral state machine ----

ReferralStatus = Literal["draft", "authorized", "calling", "accepted", "declined", "info_requested"]


class ReferralEvent(BaseModel):
    ts: str
    status: ReferralStatus
    facility_id: str
    note: str = ""
    call: Optional[CallResult] = None
