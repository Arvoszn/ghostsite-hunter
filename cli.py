import sys
import argparse
import os
import json
from datetime import datetime

# Ensure proper stdout encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from core.models import BusinessLead
from core.pipeline import HunterPipeline
from sources.gmaps_hunter import GMapsHunter
from sources.socrata_hunter import SocrataHunter
from sources.search_verifier import SearchVerifier
from sources.csv_importer import CSVImporter
from sources.expired_domain_hunter import ExpiredDomainHunter
from exporters.exporter import LeadExporter
from auditor.website_auditor import WebsiteAuditor

def print_banner():
    banner = r"""
  ==============================================================
   SPAWNTEL GHOSTSITE & DEAD-WEBSITE HUNTER v1.0
   Autonomous US Business Lead Extraction & Forensic Audit System
  ==============================================================
    """
    print(banner)

def handle_hunt(args):
    print_banner()
    query = f"{args.niche} in {args.city}"
    print(f"[*] Starting Google Maps hunt: '{query}' (Target limit: {args.limit})...")
    
    hunter = GMapsHunter(headless=not args.headful)
    leads = hunter.hunt(query, limit=args.limit)
    print(f"[+] Raw candidates harvested from Google Maps: {len(leads)}")

    if not leads:
        print("[-] No businesses found for query. Try expanding the search radius or changing keywords.")
        return

    print(f"[*] Commencing forensic audit on {len(leads)} leads...")
    pipeline = HunterPipeline(max_threads=args.threads)
    processed_leads = pipeline.process_batch(leads)

    summary = LeadExporter.generate_summary(processed_leads)
    print("\n" + "="*50)
    print("                AUDIT SUMMARY")
    print("="*50)
    print(f"Total Businesses Audited:    {summary['total_leads']}")
    print(f"High-Priority Leads (A+/A):  {summary['hot_leads_count']} ({summary['hot_leads_percentage']}%)")
    print(f"Average Opportunity Score:   {summary['average_opportunity_score']}/100")
    print("-" * 50)
    for k, v in summary['breakdown'].items():
        if v > 0:
            print(f" - {k.ljust(22)}: {v}")
    print("="*50)

    # Save exports
    export_prefix = args.export or f"hunt_{args.city.replace(' ', '_')}_{args.niche.replace(' ', '_')}"
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", f"{export_prefix}.csv")
    json_path = os.path.join("data", f"{export_prefix}.json")

    LeadExporter.to_csv(processed_leads, csv_path)
    LeadExporter.to_json(processed_leads, json_path)
    print(f"\n[+] Results saved successfully:")
    print(f"    - CSV:  {csv_path}")
    print(f"    - JSON: {json_path}")

def handle_socrata(args):
    print_banner()
    print(f"[*] Querying official municipal registry for {args.city.upper()} (Niche: {args.niche or 'All'}, Limit: {args.limit})...")
    hunter = SocrataHunter()
    leads = hunter.hunt(city_key=args.city, niche_keyword=args.niche, limit=args.limit)
    print(f"[+] Registered active businesses retrieved: {len(leads)}")

    if args.verify_web:
        print("[*] Running web verification to check for missing/active websites on search...")
        for idx, lead in enumerate(leads):
            found_url, status = SearchVerifier.verify_business_website(lead.business_name, lead.city or args.city)
            lead.website = found_url
            print(f"    [{idx+1}/{len(leads)}] {lead.business_name}: {status} -> {found_url or 'NO WEBSITE'}")

    pipeline = HunterPipeline(max_threads=args.threads)
    processed_leads = pipeline.process_batch(leads)

    export_prefix = args.export or f"socrata_{args.city}_{args.niche or 'all'}"
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", f"{export_prefix}.csv")
    json_path = os.path.join("data", f"{export_prefix}.json")

    LeadExporter.to_csv(processed_leads, csv_path)
    LeadExporter.to_json(processed_leads, json_path)
    print(f"\n[+] Results saved: {csv_path} and {json_path}")

def handle_audit_url(args):
    print_banner()
    print(f"[*] Running forensic audit on URL: {args.url} ...\n")
    auditor = WebsiteAuditor()
    res = auditor.audit(args.url)

    temp_lead = BusinessLead(business_name="Audit Target", website=args.url)
    pipeline = HunterPipeline()
    audited = pipeline.process_single_lead(temp_lead)

    print("="*60)
    print(f" Target Domain:        {res.get('domain')}")
    print(f" Classification:       {audited.classification}")
    print(f" Opportunity Grade:    {audited.opportunity_grade} (Score: {audited.opportunity_score}/100)")
    print(f" DNS Resolves:         {audited.dns_resolves} (IP: {audited.ip})")
    print(f" HTTP Status:          {audited.http_status} (Reachable: {audited.is_reachable})")
    print(f" SSL Valid:            {audited.ssl_valid} (Expires: {audited.ssl_expires})")
    print(f" Parked Domain:        {audited.is_parked} (Provider: {audited.parking_provider})")
    print(f" Mobile Viewport:      {audited.has_viewport}")
    print(f" Copyright Year:       {audited.copyright_year}")
    print(f" Outdated Signals:     {audited.outdated_signals}")
    print("="*60)
    print("\n--- GENERATED PITCH ---")
    print(f"Subject: {audited.pitch_email_subject}\n")
    print(audited.pitch_email_body)
    print("-" * 60)
    print("Cold Call Opener:")
    print(audited.pitch_cold_call)
    print("="*60)

def handle_scan_csv(args):
    print_banner()
    print(f"[*] Importing leads from CSV: {args.input} ...")
    raw_leads = CSVImporter.import_file(args.input, default_niche=args.niche or "Local Business")
    print(f"[+] Loaded {len(raw_leads)} leads from file.")

    pipeline = HunterPipeline(max_threads=args.threads)
    processed = pipeline.process_batch(raw_leads)

    output_path = args.output or f"data/audited_{os.path.basename(args.input)}"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    LeadExporter.to_csv(processed, output_path)
    print(f"\n[+] Audited leads saved to {output_path}")

def handle_hunt_expired(args):
    print_banner()
    print(f"[*] Hunting expired / parked business domains for: {args.city} {args.niche}...")
    hunter = ExpiredDomainHunter()
    leads = hunter.hunt_by_keyword(city=args.city, niche=args.niche, max_check=args.limit)
    print(f"[+] Found {len(leads)} expired / parked domain opportunities!")

    pipeline = HunterPipeline(max_threads=args.threads)
    processed = pipeline.process_batch(leads)

    export_prefix = args.export or f"expired_{args.city.replace(' ', '_')}_{args.niche.replace(' ', '_')}"
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", f"{export_prefix}.csv")
    json_path = os.path.join("data", f"{export_prefix}.json")

    LeadExporter.to_csv(processed, csv_path)
    LeadExporter.to_json(processed, json_path)
    print(f"\n[+] Results saved: {csv_path} and {json_path}")

def handle_dashboard(args):
    print_banner()
    print(f"[*] Starting GhostSite Hunter Web Dashboard on port {args.port}...")
    from web.server import run_server
    run_server(port=args.port)

def main():
    parser = argparse.ArgumentParser(description="Spawntel GhostSite & Dead-Website Hunter")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # hunt command
    hunt_parser = subparsers.add_parser("hunt", help="Hunt US businesses on Google Maps by niche and city")
    hunt_parser.add_argument("--niche", required=True, help="Business niche (e.g. 'roofing', 'plumbers', 'dentists')")
    hunt_parser.add_argument("--city", required=True, help="US City and State (e.g. 'Austin, TX', 'Miami, FL')")
    hunt_parser.add_argument("--limit", type=int, default=15, help="Number of leads to retrieve")
    hunt_parser.add_argument("--threads", type=int, default=5, help="Audit worker threads")
    hunt_parser.add_argument("--headful", action="store_true", help="Run browser in headful mode")
    hunt_parser.add_argument("--export", help="Custom export filename prefix")

    # socrata command
    socrata_parser = subparsers.add_parser("socrata", help="Hunt registered businesses from US municipal open data")
    socrata_parser.add_argument("--city", default="chicago", choices=["chicago", "nyc", "sf"], help="City registry")
    socrata_parser.add_argument("--niche", help="Niche keyword filter (e.g. 'hair', 'restaurant', 'contractor')")
    socrata_parser.add_argument("--limit", type=int, default=20, help="Number of records to fetch")
    socrata_parser.add_argument("--verify-web", action="store_true", help="Verify web/search presence for each lead")
    socrata_parser.add_argument("--threads", type=int, default=5, help="Audit worker threads")
    socrata_parser.add_argument("--export", help="Custom export filename prefix")

    # hunt-expired command
    expired_parser = subparsers.add_parser("hunt-expired", help="Hunt expired and parked domains for a US city and niche")
    expired_parser.add_argument("--city", required=True, help="City name (e.g. 'austin', 'miami', 'chicago')")
    expired_parser.add_argument("--niche", required=True, help="Business niche (e.g. 'roofing', 'plumbing', 'dental')")
    expired_parser.add_argument("--limit", type=int, default=24, help="Max domain variations to check")
    expired_parser.add_argument("--threads", type=int, default=5, help="Audit worker threads")
    expired_parser.add_argument("--export", help="Custom export filename prefix")

    # audit-url command
    audit_parser = subparsers.add_parser("audit-url", help="Perform deep forensic audit on a specific website URL")
    audit_parser.add_argument("--url", required=True, help="Website URL to audit")

    # scan-csv command
    csv_parser = subparsers.add_parser("scan-csv", help="Audit an existing CSV lead file")
    csv_parser.add_argument("--input", required=True, help="Path to input CSV file")
    csv_parser.add_argument("--output", help="Path to output audited CSV file")
    csv_parser.add_argument("--niche", help="Default niche if missing from CSV")
    csv_parser.add_argument("--threads", type=int, default=5, help="Audit worker threads")

    # dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Launch interactive web dashboard")
    dash_parser.add_argument("--port", type=int, default=8000, help="Web server port")

    args = parser.parse_args()

    if args.command == "hunt":
        handle_hunt(args)
    elif args.command == "socrata":
        handle_socrata(args)
    elif args.command == "hunt-expired":
        handle_hunt_expired(args)
    elif args.command == "audit-url":
        handle_audit_url(args)
    elif args.command == "scan-csv":
        handle_scan_csv(args)
    elif args.command == "dashboard":
        handle_dashboard(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
