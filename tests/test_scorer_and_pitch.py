import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import BusinessLead
from engine.scorer import LeadScorer
from engine.pitch_generator import PitchGenerator

class TestScorerAndPitch(unittest.TestCase):
    def test_no_website_scoring_and_pitch(self):
        lead = BusinessLead(
            business_name="Austin Prime Roofing",
            city="Austin",
            state="TX",
            niche="roofing",
            phone="512-555-0199",
            rating=4.9,
            reviews_count=24,
            classification="NO_WEBSITE"
        )
        score, grade = LeadScorer.score_lead(lead)
        lead.opportunity_score = score
        lead.opportunity_grade = grade
        self.assertEqual(grade, "A+")
        self.assertGreaterEqual(score, 90)

        PitchGenerator.generate(lead)
        self.assertIn("Austin Prime Roofing", lead.pitch_email_subject)
        self.assertIn("no website linked on your Google listing", lead.pitch_email_body)
        self.assertIn("Austin", lead.pitch_email_body)
        self.assertTrue(len(lead.pitch_cold_call) > 20)

    def test_expired_domain_pitch(self):
        lead = BusinessLead(
            business_name="Apex Dental Care",
            city="Dallas",
            state="TX",
            niche="dental",
            website="https://apexdentalcare-expired.com",
            classification="EXPIRED_DOMAIN",
            is_parked=True,
            parking_provider="GoDaddy"
        )
        score, grade = LeadScorer.score_lead(lead)
        lead.opportunity_score = score
        lead.opportunity_grade = grade
        self.assertEqual(grade, "A+")

        PitchGenerator.generate(lead)
        self.assertIn("GoDaddy", lead.pitch_email_body)
        self.assertIn("expired or redirecting", lead.pitch_email_body)

    def test_broken_website_pitch(self):
        lead = BusinessLead(
            business_name="Lone Star Auto Repair",
            city="Houston",
            state="TX",
            website="https://lonestarrepair-down.com",
            classification="BROKEN_WEBSITE",
            outdated_signals=["HTTP Server Error 500"]
        )
        score, grade = LeadScorer.score_lead(lead)
        lead.opportunity_score = score
        lead.opportunity_grade = grade
        self.assertEqual(grade, "A")

        PitchGenerator.generate(lead)
        self.assertIn("HTTP Server Error 500", lead.pitch_email_body)

    def test_healthy_website_low_score(self):
        lead = BusinessLead(
            business_name="Modern Tech Clinic",
            city="Seattle",
            classification="HEALTHY_WEBSITE"
        )
        score, grade = LeadScorer.score_lead(lead)
        self.assertEqual(grade, "C")
        self.assertLessEqual(score, 35)

if __name__ == "__main__":
    unittest.main()
