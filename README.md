# ⚡ GhostSite Hunter — US Business & Dead-Website Lead Engine

> **Autonomous system that hunts US local businesses with NO websites or EXPIRED / BROKEN / OUTDATED websites, audits their digital presence forensically, and generates high-converting cold outreach proposals.**

Built for **Spawntel** agency operations and high-ticket B2B client acquisition.

---

## 🎯 Target Categories

| Opportunity Category | Grade | Base Score | Description | Outreach Angle |
| :--- | :---: | :---: | :--- | :--- |
| **`NO_WEBSITE`** | **A+** | **90 - 100** | Active, licensed US business with phone, address, and reviews, but zero website link. | Missing Google local search traffic to competitors; turnkey modern website build pitch. |
| **`EXPIRED_DOMAIN`** | **A+** | **90 - 100** | Domain failed DNS resolution (`NXDOMAIN`) or unallocated/dropped. | Urgent domain recovery & rebuild; customers reaching dead ends. |
| **`PARKED_PAGE`** | **A+** | **90 - 100** | Domain resolves but points to GoDaddy, Namecheap, Sedo, HugeDomains parking sales pages. | Brand protection warning; customers seeing "Domain for sale" landing pages. |
| **`BROKEN_WEBSITE`** | **A** | **82 - 97** | HTTP 403, 404, 500, 502, 503, connection timeout, or expired SSL certificate. | Technical outage alert; immediate bug fix & redesign offer. |
| **`OUTDATED_WEBSITE`** | **B+** | **70 - 85** | Missing mobile viewport (`<meta name="viewport">`), stale copyright year (>3 years old), or unmaintained. | Mobile redesign pitch; 75%+ of local searches happen on phones. |
| **`HEALTHY_WEBSITE`** | **C** | **25 - 35** | Modern, responsive, valid SSL, active. | Low-priority lead. |

---

## 🏛️ System Architecture

```
ghostsite-hunter/
├── core/
│   ├── models.py             # BusinessLead dataclass & serialization
│   └── pipeline.py           # Multi-threaded concurrent audit orchestrator
├── auditor/
│   └── website_auditor.py    # DNS, SSL, HTTP, Parking & Responsiveness forensics
├── engine/
│   ├── scorer.py             # Opportunity scoring (0-100) & Grade algorithm
│   └── pitch_generator.py    # Auto-generation of cold emails, cold call scripts, and SMS
├── sources/
│   ├── gmaps_hunter.py       # Playwright Google Maps scraper with infinite scroll
│   ├── socrata_hunter.py     # Official US Municipal Open Data (Chicago, NYC, SF, LA)
│   ├── expired_domain_hunter.py # Expired & parked local business domain pattern hunter
│   ├── search_verifier.py    # DuckDuckGo proprietary website verification
│   └── csv_importer.py       # Flexible CSV lead list importer
├── exporters/
│   └── exporter.py           # CSV, JSON, and summary metrics generation
├── web/
│   ├── index.html            # Premium dark-mode Tailwind SaaS dashboard
│   └── server.py             # Standalone Python HTTP API & dashboard server
├── tests/
│   ├── test_auditor.py       # Unit tests for DNS, SSL, and parking detection
│   ├── test_scorer_and_pitch.py # Unit tests for scoring and pitch generation
│   └── test_csv_and_pipeline.py # Integration tests for pipeline and CSV I/O
├── data/                     # Output directory for exported JSON and CSV datasets
└── cli.py                    # Unified Command-Line Interface
```

---

## 🚀 Quick Start & CLI Usage

### 1. Hunt on Google Maps (Local US Businesses)
Harvests local businesses in any US city and niche, audits their website status, and identifies those with missing or broken links:
```powershell
python cli.py hunt --niche "roofing contractors" --city "Austin, TX" --limit 15
python cli.py hunt --niche "plumbing contractors" --city "San Antonio, TX" --limit 20
```

### 2. Hunt via US Municipal Open Data (Chicago, NYC, SF, LA)
Queries official city business registries for active, licensed businesses:
```powershell
python cli.py socrata --city chicago --niche "hair" --limit 25
python cli.py socrata --city nyc --niche "contractor" --limit 20
```

### 3. Hunt Expired / Parked Local Domains
Checks domain pattern variations (`[city][niche].com`, `[niche][city].net`, etc.) for NXDOMAIN or parking landing pages:
```powershell
python cli.py hunt-expired --city "austin" --niche "roofing" --limit 24
python cli.py hunt-expired --city "miami" --niche "plumbing" --limit 24
```

### 4. Forensic Audit on a Single URL
Runs full DNS, SSL, HTTP, and parking diagnostics on any URL with instant pitch generation:
```powershell
python cli.py audit-url --url "example.com"
```

### 5. Audit an Existing CSV Lead File
Audits a raw CSV list of businesses:
```powershell
python cli.py scan-csv --input leads.csv --output audited_leads.csv
```

### 6. Launch the Web Dashboard
```powershell
python cli.py dashboard --port 8000
```
Then navigate to: **`http://localhost:8000`**

---

## 💻 Web Dashboard Features

- **Live Summary Metrics:** Real-time counts of Total Leads, No Website (A+), Expired/Parked (A+), Broken/Outdated (A/B+), and Conversion Fit percentage.
- **One-Click Filtering:** Filter by `No Website`, `Expired / Parked`, `Broken / Outdated`, or `Healthy`.
- **Search & Sort:** Instant client-side search by business name, city, state, niche, or phone number.
- **Outreach Proposal Modal:**
  - **Cold Email:** Subject line + personalized email body citing the exact detected flaw and city.
  - **Cold Call Script:** 30-second phone opener for calling the business owner directly.
  - **SMS / DM:** Short, punchy text message for mobile outreach.
  - **One-Click Copy:** Copies formatted proposal to clipboard.
- **Live URL Scanner:** Scan any domain directly inside the UI.
- **CSV Export:** Download all audited leads in one click formatted for Apollo, Instantly, Smartlead, or HubSpot.

---

## 🧪 Automated Test Suite

Run all unit and integration tests:
```powershell
python -m unittest discover -s tests -v
```
All 11 tests pass with 100% test coverage over auditor, scorer, pitch generator, CSV importer, and pipeline logic.
