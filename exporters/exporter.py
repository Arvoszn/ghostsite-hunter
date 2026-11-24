import csv
import json
from typing import List, Dict, Any
from core.models import BusinessLead

class LeadExporter:
    """
    Exports leads to CSV, JSON, and summary metrics formats.
    """

    @staticmethod
    def to_csv(leads: List[BusinessLead], file_path: str):
        if not leads:
            return

        fields = [
            "id", "business_name", "niche", "city", "state", "phone", "address",
            "rating", "reviews_count", "website", "classification", "opportunity_grade",
            "opportunity_score", "dns_resolves", "is_reachable", "has_ssl", "ssl_valid",
            "is_parked", "parking_provider", "has_viewport", "copyright_year",
            "outdated_signals", "pitch_email_subject", "pitch_email_body", "pitch_cold_call", "pitch_sms"
        ]

        with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for lead in leads:
                d = lead.to_dict()
                d["outdated_signals"] = " | ".join(d.get("outdated_signals", []))
                writer.writerow({k: d.get(k, "") for k in fields})

    @staticmethod
    def to_json(leads: List[BusinessLead], file_path: str, indent: int = 2):
        with open(file_path, mode="w", encoding="utf-8") as f:
            json.dump([l.to_dict() for l in leads], f, indent=indent)

    @staticmethod
    def generate_summary(leads: List[BusinessLead]) -> Dict[str, Any]:
        total = len(leads)
        if total == 0:
            return {"total": 0}

        counts = {
            "NO_WEBSITE": 0,
            "EXPIRED_DOMAIN": 0,
            "PARKED_PAGE": 0,
            "BROKEN_WEBSITE": 0,
            "OUTDATED_WEBSITE": 0,
            "HEALTHY_WEBSITE": 0,
            "OTHER": 0
        }

        total_score = 0
        hot_leads_count = 0  # Grade A or A+

        for lead in leads:
            cat = lead.classification
            if cat in counts:
                counts[cat] += 1
            else:
                counts["OTHER"] += 1
            
            total_score += lead.opportunity_score
            if lead.opportunity_grade in ("A+", "A"):
                hot_leads_count += 1

        avg_score = round(total_score / total, 1)

        return {
            "total_leads": total,
            "hot_leads_count": hot_leads_count,
            "hot_leads_percentage": round((hot_leads_count / total) * 100, 1),
            "breakdown": counts,
            "average_opportunity_score": avg_score
        }
