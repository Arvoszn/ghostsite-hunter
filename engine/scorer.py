from typing import Tuple
from core.models import BusinessLead

class LeadScorer:
    """
    Computes Opportunity Score (0-100) and Grade (A+, A, B+, C)
    based on website health, rating, and business presence.
    """

    @staticmethod
    def score_lead(lead: BusinessLead) -> Tuple[int, str]:
        score = 0
        grade = "C"

        classification = lead.classification

        if classification == "NO_WEBSITE":
            score = 90
            grade = "A+"
        elif classification in ("EXPIRED_DOMAIN", "PARKED_PAGE"):
            score = 90
            grade = "A+"
        elif classification == "BROKEN_WEBSITE":
            score = 82
            grade = "A"
        elif classification == "OUTDATED_WEBSITE":
            score = 70
            grade = "B+"
        elif classification == "HEALTHY_WEBSITE":
            score = 25
            grade = "C"
        else:
            score = 40
            grade = "B"

        # Boost for active businesses (ratings / reviews)
        if lead.rating and lead.rating >= 4.0:
            score += 5
        if lead.reviews_count and lead.reviews_count >= 10:
            score += 5
        
        # Boost if phone number is present (ready for outreach)
        if lead.phone and len(lead.phone) >= 7:
            score += 5

        # Penalize if healthy
        if classification == "HEALTHY_WEBSITE":
            score = min(score, 35)

        # Cap score at 100
        score = min(100, max(0, score))

        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 65:
            grade = "B+"
        else:
            grade = "C"

        return score, grade
