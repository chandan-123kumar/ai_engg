from dataclasses import dataclass, field
from typing import Optional

@dataclass
class LeadState:
    lead_id: str
    name: str
    email: str
    company: str
    message: str

    company_size: Optional[str] = None
    industry: Optional[str] = None
    budget: Optional[str] = None
    tech_stack: Optional[str] = field(default_factory=list)

    icp_score: Optional[int] = None
    bant_notes: Optional[str] = None
    qualification: Optional[str] = None

    email_draft: Optional[str] = None

    errors: list = field(default_factory=list)
    latency_ms: dict=field(default_factory=dict)

