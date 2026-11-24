import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from typing import Optional, Tuple, List
import re

class SearchVerifier:
    """
    Verifies if a business has an active website or only 3rd-party directory profiles
    using DuckDuckGo HTML search.
    """

    DIRECTORY_DOMAINS = [
        "facebook.com", "instagram.com", "twitter.com", "x.com", "linkedin.com",
        "yelp.com", "yellowpages.com", "mapquest.com", "bbb.org", "tripadvisor.com",
        "manta.com", "buzzfile.com", "dnb.com", "opencorporates.com", "chamberofcommerce.com",
        "angi.com", "homeadvisor.com", "thumbtack.com", "booksy.com", "vagaro.com",
        "foursquare.com", "nextdoor.com", "groupon.com", "zoominfo.com"
    ]

    @classmethod
    def verify_business_website(cls, business_name: str, location: str) -> Tuple[Optional[str], str]:
        """
        Returns (website_url or None, status_description)
        """
        query = f'"{business_name}" {location}'
        url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                
                results: List[str] = []
                for u in soup.select('.result__url'):
                    raw = u.get_text(strip=True)
                    if raw:
                        if not raw.startswith("http://") and not raw.startswith("https://"):
                            raw = "https://" + raw
                        results.append(raw)

                for r in results:
                    # Check if result is a directory
                    is_dir = any(d in r.lower() for d in cls.DIRECTORY_DOMAINS)
                    if not is_dir:
                        # Found a proprietary website candidate!
                        return r, "PROPRIETARY_WEBSITE_FOUND"

                if results:
                    return None, "DIRECTORIES_AND_SOCIAL_ONLY"
                else:
                    return None, "NO_SEARCH_PRESENCE"
        except Exception as e:
            return None, f"VERIFICATION_ERROR: {e}"
