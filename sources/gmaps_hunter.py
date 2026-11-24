import time
from typing import List, Optional
from core.models import BusinessLead
from playwright.sync_api import sync_playwright

class GMapsHunter:
    """
    Hunts US local businesses using Google Maps with Playwright.
    Finds businesses, phone numbers, ratings, reviews, and website URLs,
    identifying businesses with missing or existing website links.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    def hunt(self, query: str, limit: int = 20) -> List[BusinessLead]:
        leads: List[BusinessLead] = []
        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900}
            )
            page = context.new_page()

            try:
                page.goto(search_url, timeout=35000)
                page.wait_for_timeout(3000)

                # Handle cookie/consent prompt if present
                for btn_text in ["Reject all", "Accept all", "Dismiss"]:
                    btn = page.query_selector(f'button:has-text("{btn_text}")')
                    if btn:
                        try:
                            btn.click()
                            page.wait_for_timeout(1500)
                            break
                        except Exception:
                            pass

                # Scroll the feed to load more cards
                feed_selector = 'div[role="feed"]'
                page.wait_for_selector(feed_selector, timeout=10000)
                
                # Progressive scroll
                scroll_rounds = max(2, limit // 5)
                for _ in range(scroll_rounds):
                    page.evaluate(f'''
                        const feed = document.querySelector('{feed_selector}');
                        if (feed) {{
                            feed.scrollTop = feed.scrollHeight;
                        }}
                    ''')
                    page.wait_for_timeout(1500)

                cards = page.query_selector_all('a.hfpxzc')
                total_found = len(cards)
                target_count = min(limit, total_found)

                # Extract location/niche hints from query
                query_parts = query.split(" in ")
                niche_hint = query_parts[0].strip() if len(query_parts) > 1 else query
                location_hint = query_parts[1].strip() if len(query_parts) > 1 else "USA"

                for idx in range(target_count):
                    try:
                        # Re-query cards to avoid stale DOM references
                        current_cards = page.query_selector_all('a.hfpxzc')
                        if idx >= len(current_cards):
                            break
                        card = current_cards[idx]
                        name = card.get_attribute("aria-label") or "Unknown Business"
                        
                        # Click into card to inspect detail pane
                        card.click()
                        page.wait_for_timeout(2000)

                        # Website button
                        web_elem = page.query_selector('a[data-item-id="authority"]')
                        website = web_elem.get_attribute("href") if web_elem else None

                        # Clean redirect URL if wrapped in google.com/url?q=
                        if website and "google.com/url" in website:
                            import urllib.parse
                            parsed_web = urllib.parse.urlparse(website)
                            qs = urllib.parse.parse_qs(parsed_web.query)
                            if "q" in qs:
                                website = qs["q"][0]

                        # Phone button
                        phone_elem = page.query_selector('button[data-item-id^="phone:tel:"]')
                        phone = phone_elem.get_attribute("data-item-id").replace("phone:tel:", "") if phone_elem else ""

                        # Address button
                        addr_elem = page.query_selector('button[data-item-id="address"]')
                        addr = addr_elem.inner_text().strip() if addr_elem else ""
                        # Remove map pin icon if present
                        if addr.startswith("\ue0c8") or addr.startswith(""):
                            addr = addr[1:].strip()

                        # Rating and Reviews
                        rating_elem = page.query_selector('div.F7nice > span > span[aria-hidden="true"]')
                        rating = float(rating_elem.inner_text().strip()) if rating_elem and rating_elem.inner_text().strip() else None

                        reviews_elem = page.query_selector('div.F7nice > span:nth-child(2) > span > span')
                        reviews_count = None
                        if reviews_elem:
                            raw_reviews = reviews_elem.inner_text().replace("(", "").replace(")", "").replace(",", "").strip()
                            try:
                                reviews_count = int(raw_reviews)
                            except ValueError:
                                pass

                        # City & State extraction from address or query
                        city = ""
                        state = ""
                        if addr:
                            parts = [p.strip() for p in addr.split(",")]
                            if len(parts) >= 3:
                                city = parts[-3] if len(parts) >= 3 else ""
                                state_zip = parts[-2].strip().split()
                                state = state_zip[0] if state_zip else ""
                        if not city:
                            city = location_hint

                        lead = BusinessLead(
                            business_name=name,
                            city=city,
                            state=state,
                            niche=niche_hint,
                            address=addr,
                            phone=phone,
                            rating=rating,
                            reviews_count=reviews_count,
                            website=website,
                            source="google_maps",
                            has_website=bool(website)
                        )
                        leads.append(lead)
                    except Exception as e:
                        continue

            except Exception as e:
                pass
            finally:
                browser.close()

        return leads
