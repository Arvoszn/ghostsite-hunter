import http.server
import socketserver
import json
import os
import sys
import glob
from urllib.parse import urlparse, parse_qs
from core.models import BusinessLead
from core.pipeline import HunterPipeline
from auditor.website_auditor import WebsiteAuditor
from exporters.exporter import LeadExporter

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.web_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(os.path.dirname(self.web_dir), "data")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            index_path = os.path.join(self.web_dir, "index.html")
            with open(index_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        elif path == "/api/leads":
            leads = self._load_all_leads()
            data = json.dumps([l.to_dict() for l in leads]).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        elif path == "/api/summary":
            leads = self._load_all_leads()
            summary = LeadExporter.generate_summary(leads)
            data = json.dumps(summary).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        elif path == "/api/export":
            leads = self._load_all_leads()
            temp_csv = os.path.join(self.data_dir, "_export_temp.csv")
            os.makedirs(self.data_dir, exist_ok=True)
            LeadExporter.to_csv(leads, temp_csv)
            with open(temp_csv, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", 'attachment; filename="ghostsite_leads.csv"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/audit":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            req_data = json.loads(body)
            target_url = req_data.get("url", "")

            temp_lead = BusinessLead(business_name="Target Domain", website=target_url)
            pipeline = HunterPipeline()
            audited = pipeline.process_single_lead(temp_lead)

            res_bytes = json.dumps(audited.to_dict()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(res_bytes)))
            self.end_headers()
            self.wfile.write(res_bytes)
            return

        self.send_error(404, "Not Found")

    def _load_all_leads(self):
        all_leads = []
        json_files = glob.glob(os.path.join(self.data_dir, "*.json"))
        seen_ids = set()

        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            lead = BusinessLead.from_dict(item)
                            key = f"{lead.business_name}_{lead.city}".lower()
                            if key not in seen_ids:
                                seen_ids.add(key)
                                all_leads.append(lead)
            except Exception:
                continue

        all_leads.sort(key=lambda x: x.opportunity_score, reverse=True)
        return all_leads

def run_server(port: int = 8000):
    handler = DashboardHandler
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"[*] GhostSite Hunter Dashboard running at: http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Server stopped.")

if __name__ == "__main__":
    run_server(8000)
