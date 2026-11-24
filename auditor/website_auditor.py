import socket
import ssl
import re
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
import httpx
try:
    import dns.resolver
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False

class WebsiteAuditor:
    """
    Audits website health, DNS validity, SSL certificate status,
    parking signatures, and obsolescence signals.
    """

    PARKING_SIGNATURES = {
        "GoDaddy": [
            "domain is parked",
            "parked free, courtesy of godaddy",
            "buy this domain at godaddy",
            "this domain is registered with godaddy",
            "parked-domain.godaddy.com"
        ],
        "Namecheap": [
            "parkingpage.namecheap.com",
            "registered at namecheap.com",
            "domain is parked with namecheap",
            "website is parked by namecheap"
        ],
        "Sedo": [
            "sedoparking.com",
            "buy this domain",
            "sedo domain parking",
            "domain has been registered with sedo"
        ],
        "HugeDomains": [
            "hugedomains.com",
            "this domain is for sale - hugedomains",
            "buy this domain today"
        ],
        "Dan.com / Afternic": [
            "dan.com",
            "afternic.com/domain",
            "buy or lease this domain",
            "this domain may be for sale"
        ],
        "Squarespace Expired": [
            "this account has expired",
            "website expired",
            "squarespace.com/expired"
        ],
        "Hostinger / cPanel Default": [
            "default page hosted by hostinger",
            "cgi-sys/defaultwebpage.cgi",
            "default web site page",
            "if you are the owner of this website"
        ],
        "Wix Parked": [
            "domain is currently parked with wix",
            "parked with wix"
        ],
        "Generic Expired": [
            "domain name has expired",
            "domain is expired and pending renewal",
            "domain has expired",
            "renew your domain",
            "domain expired on",
            "this domain expired"
        ]
    }

    def __init__(self, timeout: float = 7.0):
        self.timeout = timeout

    @staticmethod
    def clean_url(url: str) -> str:
        if not url:
            return ""
        url = url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        return url

    def extract_domain(self, url: str) -> str:
        cleaned = self.clean_url(url)
        parsed = urlparse(cleaned)
        netloc = parsed.netloc.split(":")[0].lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc

    def check_dns(self, domain: str) -> Dict[str, Any]:
        """Resolves DNS and detects NXDOMAIN."""
        result = {
            "resolves": False,
            "ip": None,
            "is_nxdomain": False,
            "has_mx": False,
            "nameservers": []
        }
        
        # Test basic socket resolution
        try:
            ip = socket.gethostbyname(domain)
            result["resolves"] = True
            result["ip"] = ip
        except socket.gaierror as e:
            result["resolves"] = False
            result["is_nxdomain"] = True
            return result
        except Exception:
            result["resolves"] = False
            return result

        if HAS_DNSPYTHON:
            try:
                ns_answers = dns.resolver.resolve(domain, 'NS', lifetime=2.0)
                result["nameservers"] = [str(r.target).rstrip('.') for r in ns_answers]
            except Exception:
                pass
            try:
                mx_answers = dns.resolver.resolve(domain, 'MX', lifetime=2.0)
                result["has_mx"] = len(mx_answers) > 0
            except Exception:
                pass

        return result

    def check_ssl(self, domain: str) -> Dict[str, Any]:
        """Checks SSL certificate validity and expiration date."""
        result = {
            "has_ssl": False,
            "valid": False,
            "expires_at": None,
            "error": None
        }
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    result["has_ssl"] = True
                    result["valid"] = True
                    exp_date_str = cert.get("notAfter")
                    if exp_date_str:
                        exp_date = datetime.strptime(exp_date_str, "%b %d %H:%M:%S %Y %Z")
                        result["expires_at"] = exp_date.strftime("%Y-%m-%d")
                        if exp_date < datetime.now():
                            result["valid"] = False
                            result["error"] = f"SSL expired on {result['expires_at']}"
        except ssl.SSLCertVerificationError as e:
            result["has_ssl"] = True
            result["valid"] = False
            result["error"] = f"SSL verification failed: {e.verify_message}"
        except Exception as e:
            result["has_ssl"] = False
            result["valid"] = False
            result["error"] = "No HTTPS / SSL setup"

        return result

    def audit(self, raw_url: Optional[str]) -> Dict[str, Any]:
        """
        Executes full forensic audit on website.
        Returns diagnostic dictionary.
        """
        if not raw_url or raw_url.lower() in ("no_website", "none", "n/a", ""):
            return {
                "has_website": False,
                "dns_resolves": False,
                "ip": None,
                "http_status": None,
                "is_reachable": False,
                "has_ssl": False,
                "ssl_valid": False,
                "ssl_expires": None,
                "is_parked": False,
                "parking_provider": None,
                "has_viewport": False,
                "copyright_year": None,
                "outdated_signals": ["No website found on record"],
                "classification": "NO_WEBSITE",
                "error_message": "Business has no registered website"
            }

        target_url = self.clean_url(raw_url)
        domain = self.extract_domain(target_url)

        audit_res = {
            "has_website": True,
            "target_url": target_url,
            "domain": domain,
            "dns_resolves": False,
            "ip": None,
            "http_status": None,
            "is_reachable": False,
            "has_ssl": False,
            "ssl_valid": False,
            "ssl_expires": None,
            "is_parked": False,
            "parking_provider": None,
            "has_viewport": False,
            "copyright_year": None,
            "outdated_signals": [],
            "classification": "UNKNOWN",
            "error_message": None
        }

        # 1. DNS Check
        dns_res = self.check_dns(domain)
        audit_res["dns_resolves"] = dns_res["resolves"]
        audit_res["ip"] = dns_res["ip"]

        if not dns_res["resolves"]:
            audit_res["classification"] = "EXPIRED_DOMAIN"
            audit_res["outdated_signals"].append("Domain does not resolve (NXDOMAIN - Expired or Deleted)")
            audit_res["error_message"] = "DNS NXDOMAIN: Domain expired or removed"
            return audit_res

        # 2. SSL Check
        ssl_res = self.check_ssl(domain)
        audit_res["has_ssl"] = ssl_res["has_ssl"]
        audit_res["ssl_valid"] = ssl_res["valid"]
        audit_res["ssl_expires"] = ssl_res["expires_at"]
        if ssl_res["error"]:
            audit_res["outdated_signals"].append(ssl_res["error"])

        # 3. HTTP Inspection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        try:
            with httpx.Client(follow_redirects=True, timeout=self.timeout, verify=False, headers=headers) as client:
                resp = client.get(target_url)
                audit_res["http_status"] = resp.status_code
                audit_res["is_reachable"] = resp.status_code < 400

                if resp.status_code >= 400:
                    audit_res["classification"] = "BROKEN_WEBSITE"
                    audit_res["outdated_signals"].append(f"HTTP Server Error {resp.status_code}")
                    audit_res["error_message"] = f"HTTP {resp.status_code} error response"
                    return audit_res

                body_text = resp.text.lower()

                # Parking Check
                for provider, sigs in self.PARKING_SIGNATURES.items():
                    if any(sig in body_text for sig in sigs):
                        audit_res["is_parked"] = True
                        audit_res["parking_provider"] = provider
                        audit_res["classification"] = "PARKED_PAGE"
                        audit_res["outdated_signals"].append(f"Parked domain page ({provider})")
                        audit_res["error_message"] = f"Domain is parked/for sale on {provider}"
                        return audit_res

                # Viewport / Mobile Responsiveness Check
                if 'name="viewport"' in body_text or "name='viewport'" in body_text:
                    audit_res["has_viewport"] = True
                else:
                    audit_res["has_viewport"] = False
                    audit_res["outdated_signals"].append("Missing mobile viewport (Unusable on mobile phones)")

                # Copyright Year Check
                current_year = datetime.now().year
                cp_matches = re.findall(r'(?:copyright|©|&copy;)\s*(?:20\d\d\s*[-–]\s*)?(20\d\d)', body_text)
                if cp_matches:
                    years = [int(y) for y in cp_matches if 1999 <= int(y) <= current_year + 1]
                    if years:
                        latest_year = max(years)
                        audit_res["copyright_year"] = latest_year
                        if latest_year < current_year - 2:
                            audit_res["outdated_signals"].append(f"Outdated copyright year: © {latest_year} (stale for {current_year - latest_year} years)")

                # Flash / Ancient Technology Check
                if ".swf" in body_text or "shockwave-flash" in body_text:
                    audit_res["outdated_signals"].append("Uses deprecated Adobe Flash technology")

                # Under Construction check
                if any(x in body_text for x in ["under construction", "coming soon", "site is currently undergoing maintenance"]):
                    audit_res["outdated_signals"].append("Website displays placeholder/maintenance banner")

                # Classification determination
                if not audit_res["ssl_valid"] and not audit_res["has_ssl"]:
                    audit_res["classification"] = "BROKEN_WEBSITE"
                elif len(audit_res["outdated_signals"]) > 0:
                    audit_res["classification"] = "OUTDATED_WEBSITE"
                else:
                    audit_res["classification"] = "HEALTHY_WEBSITE"

        except httpx.ConnectTimeout:
            audit_res["is_reachable"] = False
            audit_res["classification"] = "BROKEN_WEBSITE"
            audit_res["outdated_signals"].append("Server connection timed out (>7s)")
            audit_res["error_message"] = "Connection timed out"
        except httpx.ConnectError as e:
            audit_res["is_reachable"] = False
            audit_res["classification"] = "BROKEN_WEBSITE"
            audit_res["outdated_signals"].append(f"Connection refused / Server down")
            audit_res["error_message"] = f"Connection error: {e}"
        except Exception as e:
            audit_res["is_reachable"] = False
            audit_res["classification"] = "BROKEN_WEBSITE"
            audit_res["outdated_signals"].append(f"Fetch failed: {str(e)[:60]}")
            audit_res["error_message"] = str(e)

        return audit_res
