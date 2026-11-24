from typing import List, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.models import BusinessLead
from auditor.website_auditor import WebsiteAuditor
from engine.scorer import LeadScorer
from engine.pitch_generator import PitchGenerator

class HunterPipeline:
    """
    Coordinates ingestion, diagnostic auditing, scoring, and pitch generation.
    """

    def __init__(self, max_threads: int = 5, audit_timeout: float = 7.0):
        self.max_threads = max_threads
        self.auditor = WebsiteAuditor(timeout=audit_timeout)

    def process_single_lead(self, lead: BusinessLead) -> BusinessLead:
        """
        Audits a single lead, applies classification, calculates score and generates pitch.
        """
        if not lead.website or lead.website.lower() in ("no_website", "none", "n/a", ""):
            lead.has_website = False
            lead.classification = "NO_WEBSITE"
            lead.outdated_signals = ["No website linked on profile"]
        else:
            lead.has_website = True
            audit_res = self.auditor.audit(lead.website)
            lead.dns_resolves = audit_res["dns_resolves"]
            lead.ip = audit_res["ip"]
            lead.http_status = audit_res["http_status"]
            lead.is_reachable = audit_res["is_reachable"]
            lead.has_ssl = audit_res["has_ssl"]
            lead.ssl_valid = audit_res["ssl_valid"]
            lead.ssl_expires = audit_res["ssl_expires"]
            lead.is_parked = audit_res["is_parked"]
            lead.parking_provider = audit_res["parking_provider"]
            lead.has_viewport = audit_res["has_viewport"]
            lead.copyright_year = audit_res["copyright_year"]
            lead.outdated_signals = audit_res["outdated_signals"]
            lead.classification = audit_res["classification"]

        # Calculate score and grade
        score, grade = LeadScorer.score_lead(lead)
        lead.opportunity_score = score
        lead.opportunity_grade = grade

        # Generate personalized pitches
        PitchGenerator.generate(lead)

        return lead

    def process_batch(self, leads: List[BusinessLead], show_progress: bool = True) -> List[BusinessLead]:
        """
        Processes a batch of leads concurrently.
        """
        processed: List[BusinessLead] = []
        total = len(leads)

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            future_to_lead = {executor.submit(self.process_single_lead, lead): lead for lead in leads}
            
            completed = 0
            for future in as_completed(future_to_lead):
                completed += 1
                try:
                    res_lead = future.result()
                    processed.append(res_lead)
                    if show_progress:
                        print(f"[{completed}/{total}] Audited: {res_lead.business_name} -> {res_lead.classification} (Grade {res_lead.opportunity_grade}, Score {res_lead.opportunity_score})")
                except Exception as e:
                    orig_lead = future_to_lead[future]
                    orig_lead.classification = "AUDIT_ERROR"
                    orig_lead.outdated_signals.append(str(e))
                    processed.append(orig_lead)

        # Sort by opportunity score descending (best opportunities first)
        processed.sort(key=lambda x: x.opportunity_score, reverse=True)
        return processed
