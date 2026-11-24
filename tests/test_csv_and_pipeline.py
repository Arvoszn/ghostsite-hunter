import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import BusinessLead
from core.pipeline import HunterPipeline
from sources.csv_importer import CSVImporter
from exporters.exporter import LeadExporter

class TestPipelineAndExporters(unittest.TestCase):
    def test_pipeline_processing(self):
        pipeline = HunterPipeline(max_threads=2, audit_timeout=3.0)
        lead_no_web = BusinessLead(business_name="Test No Web Co", city="Miami", phone="305-555-1234")
        lead_dead_domain = BusinessLead(business_name="Dead Domain LLC", city="Orlando", website="this-is-dead-domain-xyz-1234.com")

        results = pipeline.process_batch([lead_no_web, lead_dead_domain], show_progress=False)
        self.assertEqual(len(results), 2)
        
        # Check that no-web lead is classified properly
        no_web_res = next(r for r in results if r.business_name == "Test No Web Co")
        self.assertEqual(no_web_res.classification, "NO_WEBSITE")
        self.assertEqual(no_web_res.opportunity_grade, "A+")

        # Check dead domain lead
        dead_res = next(r for r in results if r.business_name == "Dead Domain LLC")
        self.assertEqual(dead_res.classification, "EXPIRED_DOMAIN")
        self.assertEqual(dead_res.opportunity_grade, "A+")

    def test_csv_import_and_export(self):
        sample_csv_content = """Company,Phone,Website,City,State
Alpha Roofing,5125550101,,Austin,TX
Beta HVAC,5125550202,https://nonexistent-domain-test-123987.org,Round Rock,TX
"""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(sample_csv_content)
            temp_in = f.name

        try:
            leads = CSVImporter.import_file(temp_in, default_niche="Contractor")
            self.assertEqual(len(leads), 2)
            self.assertEqual(leads[0].business_name, "Alpha Roofing")
            self.assertIsNone(leads[0].website)
            self.assertEqual(leads[1].business_name, "Beta HVAC")
            self.assertEqual(leads[1].website, "https://nonexistent-domain-test-123987.org")

            # Test export
            temp_out = temp_in.replace(".csv", "_out.csv")
            LeadExporter.to_csv(leads, temp_out)
            self.assertTrue(os.path.exists(temp_out))
            os.remove(temp_out)
        finally:
            if os.path.exists(temp_in):
                os.remove(temp_in)

if __name__ == "__main__":
    unittest.main()
