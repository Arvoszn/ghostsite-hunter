import csv
from typing import List, Dict, Any, Optional
from core.models import BusinessLead

class CSVImporter:
    """
    Imports business lead lists from CSV files.
    Flexibly maps columns such as Name, Phone, Address, City, State, Website.
    """

    @staticmethod
    def import_file(file_path: str, default_niche: str = "Local Business") -> List[BusinessLead]:
        leads: List[BusinessLead] = []

        with open(file_path, mode="r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            fieldnames = [k.lower().strip() for k in (reader.fieldnames or [])]
            
            # Map column names
            name_col = next((k for k in reader.fieldnames if k.lower().strip() in ["name", "business_name", "business", "company", "title"]), None)
            phone_col = next((k for k in reader.fieldnames if k.lower().strip() in ["phone", "telephone", "mobile", "contact_phone"]), None)
            web_col = next((k for k in reader.fieldnames if k.lower().strip() in ["website", "url", "domain", "web", "site"]), None)
            addr_col = next((k for k in reader.fieldnames if k.lower().strip() in ["address", "street", "full_address"]), None)
            city_col = next((k for k in reader.fieldnames if k.lower().strip() in ["city", "town"]), None)
            state_col = next((k for k in reader.fieldnames if k.lower().strip() in ["state", "province", "region"]), None)
            niche_col = next((k for k in reader.fieldnames if k.lower().strip() in ["niche", "category", "industry", "type"]), None)
            rating_col = next((k for k in reader.fieldnames if k.lower().strip() in ["rating", "stars", "score"]), None)

            for row in reader:
                name = row.get(name_col, "").strip() if name_col else ""
                if not name:
                    continue

                phone = row.get(phone_col, "").strip() if phone_col else ""
                website = row.get(web_col, "").strip() if web_col else None
                if not website or website.lower() in ["none", "n/a", "no website", "null", ""]:
                    website = None

                addr = row.get(addr_col, "").strip() if addr_col else ""
                city = row.get(city_col, "").strip() if city_col else ""
                state = row.get(state_col, "").strip() if state_col else ""
                niche = row.get(niche_col, "").strip() if niche_col else default_niche
                
                rating = None
                if rating_col and row.get(rating_col):
                    try:
                        rating = float(row.get(rating_col).strip())
                    except ValueError:
                        pass

                lead = BusinessLead(
                    business_name=name,
                    phone=phone,
                    website=website,
                    address=addr,
                    city=city,
                    state=state,
                    niche=niche,
                    rating=rating,
                    source="csv_import",
                    has_website=bool(website)
                )
                leads.append(lead)

        return leads
