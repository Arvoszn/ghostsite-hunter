import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auditor.website_auditor import WebsiteAuditor

class TestWebsiteAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = WebsiteAuditor(timeout=5.0)

    def test_no_website(self):
        res = self.auditor.audit(None)
        self.assertEqual(res["classification"], "NO_WEBSITE")
        self.assertFalse(res["has_website"])

    def test_clean_url(self):
        self.assertEqual(self.auditor.clean_url("example.com"), "https://example.com")
        self.assertEqual(self.auditor.clean_url("http://test.org"), "http://test.org")

    def test_extract_domain(self):
        self.assertEqual(self.auditor.extract_domain("https://www.example.com/about?q=1"), "example.com")
        self.assertEqual(self.auditor.extract_domain("sub.test.com:8080"), "sub.test.com")

    def test_expired_domain_nxdomain(self):
        fake_domain = "this-is-a-completely-bogus-domain-99998877.xyz"
        res = self.auditor.audit(fake_domain)
        self.assertEqual(res["classification"], "EXPIRED_DOMAIN")
        self.assertFalse(res["dns_resolves"])

    def test_parking_signature_matching(self):
        # Verify parking signatures exist for key registrars
        self.assertIn("GoDaddy", self.auditor.PARKING_SIGNATURES)
        self.assertIn("Namecheap", self.auditor.PARKING_SIGNATURES)
        self.assertIn("Sedo", self.auditor.PARKING_SIGNATURES)
        self.assertIn("HugeDomains", self.auditor.PARKING_SIGNATURES)

if __name__ == "__main__":
    unittest.main()
