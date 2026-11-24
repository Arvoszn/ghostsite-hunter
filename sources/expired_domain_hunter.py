import re
import socket
from typing import List, Dict, Any, Generator
from core.models import BusinessLead
from auditor.website_auditor import WebsiteAuditor

class ExpiredDomainHunter:
    """
    Hunts expired, dropped, or parked domains for US local businesses
    by generating local business domain candidates or scanning directory outbound links.
    """

    US_CITIES = [
        "austin", "dallas", "houston", "miami", "orlando", "tampa",
        "chicago", "phoenix", "denver", "seattle", "atlanta", "charlotte"
    ]
    
    HIGH_INTENT_NICHES = [
        "roofing", "plumbing", "plumber", "hvac", "dental", "dentist",
        "electrician", "autorepair", "towing", "landscaping", "lawfirm", "salon"
    ]

    TLDS = [".com", ".net", ".org"]

    def __init__(self, timeout: float = 5.0):
        self.auditor = WebsiteAuditor(timeout=timeout)

    def generate_candidate_domains(self, city: str, niche: str) -> List[str]:
        """
        Generates domain pattern variations for a given US city and niche.
        e.g. austinroofing.com, roofingaustin.com, austinroofer.com, theaustinroofing.com
        """
        clean_city = city.lower().replace(" ", "").replace(",", "")
        clean_niche = niche.lower().replace(" ", "")

        patterns = [
            f"{clean_city}{clean_niche}",
            f"{clean_niche}{clean_city}",
            f"{clean_city}pro{clean_niche}",
            f"{clean_city}best{clean_niche}",
            f"the{clean_city}{clean_niche}",
            f"{clean_city}{clean_niche}pros",
            f"{clean_city}{clean_niche}group",
            f"{clean_city}{clean_niche}repair"
        ]

        domains = []
        for p in patterns:
            for tld in self.TLDS:
                domains.append(f"{p}{tld}")
        return domains

    def hunt_by_keyword(self, city: str, niche: str, max_check: int = 30) -> List[BusinessLead]:
        """
        Checks domain candidate patterns for NXDOMAIN (expired/unregistered) or parked landing pages.
        """
        candidates = self.generate_candidate_domains(city, niche)[:max_check]
        found_leads: List[BusinessLead] = []

        print(f"[*] Testing {len(candidates)} domain variations for {city} {niche}...")

        for domain in candidates:
            audit = self.auditor.audit(domain)
            # If domain is expired or parked, it represents a high-value lead / brand opportunity
            if audit["classification"] in ("EXPIRED_DOMAIN", "PARKED_PAGE"):
                biz_name = f"{city.title()} {niche.title()} ({domain})"
                lead = BusinessLead(
                    business_name=biz_name,
                    city=city.title(),
                    niche=niche.title(),
                    website=f"https://{domain}",
                    source="expired_domain_hunter",
                    has_website=True,
                    dns_resolves=audit["dns_resolves"],
                    ip=audit["ip"],
                    http_status=audit["http_status"],
                    is_reachable=audit["is_reachable"],
                    is_parked=audit["is_parked"],
                    parking_provider=audit["parking_provider"],
                    classification=audit["classification"],
                    outdated_signals=audit["outdated_signals"]
                )
                found_leads.append(lead)

        return found_leads
