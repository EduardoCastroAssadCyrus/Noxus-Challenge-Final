from typing import Literal
from pydantic import BaseModel, Field


class VulnerabilityFinding(BaseModel):
    id: str
    classification: Literal["true_positive", "false_positive"]
    confidence: float = Field(ge=0.0, le=1.0)

    original_finding: dict

    reason: str
    evidence: list[str]


class VulnerabilityFilterResult(BaseModel):
    true_positives: list[VulnerabilityFinding]
    false_positives: list[VulnerabilityFinding]