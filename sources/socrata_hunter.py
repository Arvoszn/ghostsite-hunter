import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any, Optional
from core.models import BusinessLead

class SocrataHunter:
    """
    Hunts licensed active businesses from official US municipal open data portals.
    Supports Chicago, NYC, San Francisco, and Los Angeles.
    """

    ENDPOINTS = {
        "chicago": {
            "url": "https://data.cityofchicago.org/resource/r5kz-chrr.json",
            "name_field": "doing_business_as_name",
            "fallback_name": "legal_name",
            "addr_field": "address",
            "city_field": "city",
            "state_field": "state",
            "zip_field": "zip_code",
            "niche_field": "business_activity",
            "phone_field": None,
            "default_city": "Chicago",
            "default_state": "IL"
        },
        "nyc": {
            "url": "https://data.cityofnewyork.us/resource/w7w3-xahh.json",
            "name_field": "business_name",
            "fallback_name": "legal_business_name",
            "addr_field": "address_building",
            "city_field": "address_city",
            "state_field": "address_state",
            "zip_field": "address_zip",
            "niche_field": "industry",
            "phone_field": "contact_phone",
            "default_city": "New York",
            "default_state": "NY"
        },
        "sf": {
            "url": "https://data.sfgov.org/resource/g8m3-pdis.json",
            "name_field": "dba_name",
            "fallback_name": "ownership_name",
            "addr_field": "street_address",
            "city_field": "city",
            "state_field": "state",
            "zip_field": "source_zipcode",
            "niche_field": "naics_code_description",
            "phone_field": None,
            "default_city": "San Francisco",
            "default_state": "CA"
        }
    }

    def hunt(self, city_key: str = "chicago", niche_keyword: Optional[str] = None, limit: int = 25) -> List[BusinessLead]:
        city_key = city_key.lower().strip()
        config = self.ENDPOINTS.get(city_key, self.ENDPOINTS["chicago"])
        base_url = config["url"]

        params: Dict[str, str] = {
            "$limit": str(limit),
            "$order": ":id DESC"
        }
        
        # Add SoQL filtering if niche is requested
        if niche_keyword and config["niche_field"]:
            clean_niche = niche_keyword.replace("'", "''")
            params["$where"] = f"lower({config['niche_field']}) like '%{clean_niche.lower()}%'"

        query_str = urllib.parse.urlencode(params)
        full_url = f"{base_url}?{query_str}"

        req = urllib.request.Request(
            full_url,
            headers={
                "User-Agent": "SpawntelLeadHunter/1.0 (contact: ops@spawntel.com)",
                "Accept": "application/json"
            }
        )

        leads: List[BusinessLead] = []
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_data = json.loads(resp.read().decode("utf-8"))
                for row in raw_data:
                    name = row.get(config["name_field"]) or row.get(config["fallback_name"])
                    if not name:
                        continue
                    
                    addr = row.get(config["addr_field"], "")
                    city = row.get(config["city_field"]) or config["default_city"]
                    state = row.get(config["state_field"]) or config["default_state"]
                    zip_code = row.get(config["zip_field"], "")
                    full_addr = f"{addr}, {city}, {state} {zip_code}".strip(", ")
                    
                    niche = row.get(config["niche_field"], niche_keyword or "Local Business")
                    phone = row.get(config["phone_field"], "") if config["phone_field"] else ""

                    lead = BusinessLead(
                        business_name=name.title() if name.isupper() else name,
                        city=city,
                        state=state,
                        niche=niche,
                        address=full_addr,
                        phone=str(phone) if phone else "",
                        website=None,  # City registries typically do not have website URLs
                        source=f"socrata_{city_key}",
                        has_website=False
                    )
                    leads.append(lead)
        except Exception as e:
            pass

        return leads
