from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

@dataclass
class BusinessLead:
    business_name: str
    city: str = ""
    state: str = ""
    country: str = "US"
    niche: str = ""
    address: str = ""
    phone: str = ""
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    website: Optional[str] = None
    source: str = "unknown"
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Audit & Diagnostics
    has_website: bool = False
    dns_resolves: bool = False
    ip: Optional[str] = None
    http_status: Optional[int] = None
    is_reachable: bool = False
    has_ssl: bool = False
    ssl_valid: bool = False
    ssl_expires: Optional[str] = None
    is_parked: bool = False
    parking_provider: Optional[str] = None
    has_viewport: bool = False
    copyright_year: Optional[int] = None
    outdated_signals: List[str] = field(default_factory=list)
    
    # Classification & Scoring
    classification: str = "UNAUDITED"  # NO_WEBSITE, EXPIRED_DOMAIN, PARKED_PAGE, BROKEN_WEBSITE, OUTDATED_WEBSITE, HEALTHY_WEBSITE
    opportunity_grade: str = "N/A"    # A+, A, B+, C
    opportunity_score: int = 0         # 0 - 100
    
    # Generated Outreach Pitches
    pitch_email_subject: str = ""
    pitch_email_body: str = ""
    pitch_cold_call: str = ""
    pitch_sms: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusinessLead":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
