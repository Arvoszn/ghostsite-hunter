from core.models import BusinessLead

class PitchGenerator:
    """
    Generates tailored, high-converting outreach copy for each lead
    based on the exact diagnostic flaw detected.
    """

    @classmethod
    def generate(cls, lead: BusinessLead) -> BusinessLead:
        biz_name = lead.business_name or "your business"
        city = lead.city or "your area"
        niche = lead.niche or "local businesses"
        domain = lead.website or "your website"

        if lead.classification == "NO_WEBSITE":
            lead.pitch_email_subject = f"Website question for {biz_name}"
            lead.pitch_email_body = (
                f"Hi {biz_name} team,\n\n"
                f"I came across {biz_name} while looking at top-rated {niche} in {city}.\n\n"
                f"I noticed you have strong customer reviews, but no website linked on your Google listing. "
                f"Most customers who search for {niche} in {city} end up clicking on competitors simply because "
                f"they can't view a menu/service list or book directly online.\n\n"
                f"We help local businesses launch modern, high-converting websites in under 5 days without high agency fees.\n\n"
                f"Would you be open to seeing a quick 60-second mockup we put together for {biz_name}?\n\n"
                f"Best regards,\nSpawntel Digital"
            )
            lead.pitch_cold_call = (
                f"Hi, is the owner or manager available? My name is [Your Name]. I was checking out {biz_name} online "
                f"and saw your great reviews, but noticed your Google listing doesn't have a website attached. "
                f"Are you guys currently taking on new customers in {city}? We build simple, high-converting websites "
                f"for {niche} that bring in direct bookings. Can I email you a quick preview?"
            )
            lead.pitch_sms = (
                f"Hey {biz_name}! Noticed you have great reviews in {city} but no website link on Google. "
                f"Are you open to seeing a quick design mockup we built for your shop? No cost or pitch, just thought you'd like it."
            )

        elif lead.classification in ("EXPIRED_DOMAIN", "PARKED_PAGE"):
            provider = lead.parking_provider or "a domain parking service"
            lead.pitch_email_subject = f"Urgent heads up regarding {domain} ({biz_name})"
            lead.pitch_email_body = (
                f"Hi {biz_name} team,\n\n"
                f"I'm reaching out with a quick heads up. When searching for {biz_name}, the link to {domain} "
                f"appears to be expired or redirecting to {provider} ('This domain is parked / for sale').\n\n"
                f"This usually happens if auto-renew failed or DNS records shifted, and it means local customers trying "
                f"to visit your site are seeing a placeholder page instead of your services.\n\n"
                f"Did you intend to retire this domain, or would you like help getting your website back online and protected?\n\n"
                f"Happy to help you get this sorted out quickly.\n\n"
                f"Best,\nSpawntel Digital"
            )
            lead.pitch_cold_call = (
                f"Hi, quick call for the owner: I was trying to check out {biz_name}'s website ({domain}), "
                f"and it looks like the domain is expired and showing a parking page to visitors right now. "
                f"Just wanted to let you know before potential customers bounce. Do you need help getting that restored?"
            )
            lead.pitch_sms = (
                f"Heads up {biz_name}: your website ({domain}) currently shows an expired domain / parking page to visitors. "
                f"Let me know if you need help restoring or pointing it back up!"
            )

        elif lead.classification == "BROKEN_WEBSITE":
            error_msg = lead.outdated_signals[0] if lead.outdated_signals else "Server error"
            lead.pitch_email_subject = f"Technical issue on {domain} ({biz_name})"
            lead.pitch_email_body = (
                f"Hi {biz_name} team,\n\n"
                f"I wanted to let you know that your website ({domain}) currently shows an error to visitors: {error_msg}.\n\n"
                f"When potential customers click your link from Google, they are unable to load your page or contact you. "
                f"We specialize in rapid web diagnostics and maintenance for local businesses in {city}.\n\n"
                f"Would you like us to run a free diagnostic report to show what needs to be fixed to get you back up?\n\n"
                f"Best regards,\nSpawntel Digital"
            )
            lead.pitch_cold_call = (
                f"Hi, quick call for the manager: Your website ({domain}) seems to be down with a {error_msg}. "
                f"Are you aware customers can't open your page right now? We fix site outages and redesigns locally."
            )
            lead.pitch_sms = (
                f"Hi {biz_name}, quick alert: your website at {domain} is currently down ({error_msg}). "
                f"Reaching out in case you need a hand fixing it!"
            )

        elif lead.classification == "OUTDATED_WEBSITE":
            signals_str = ", ".join(lead.outdated_signals[:2])
            lead.pitch_email_subject = f"Mobile experience update for {biz_name}"
            lead.pitch_email_body = (
                f"Hi {biz_name} team,\n\n"
                f"I was looking at {domain} on my phone and noticed {signals_str}.\n\n"
                f"Over 75% of local searches in {city} now happen on mobile devices, and Google actively demotes "
                f"sites that aren't optimized for smartphone viewports.\n\n"
                f"We help established businesses modernize their site into a fast, mobile-first design that increases "
                f"inbound calls and form submissions.\n\n"
                f"Can I send you a 2-minute video showing 3 quick tweaks that would boost your mobile conversions?\n\n"
                f"Best regards,\nSpawntel Digital"
            )
            lead.pitch_cold_call = (
                f"Hi! Calling because I checked out {biz_name}'s website on a phone and noticed it's hard to read on mobile. "
                f"We do fast mobile redesigns for {niche} in {city}. Can I send the owner a quick preview?"
            )
            lead.pitch_sms = (
                f"Hey {biz_name}! Took a look at {domain} and noticed it's not formatted for mobile phones. "
                f"Open to seeing a quick mobile mockup we put together for you guys?"
            )

        else:
            lead.pitch_email_subject = f"Quick question regarding {biz_name}"
            lead.pitch_email_body = f"Hi {biz_name} team, reaching out regarding your online presence in {city}..."
            lead.pitch_cold_call = f"Hi, reaching out to {biz_name} about web strategy."
            lead.pitch_sms = f"Hi {biz_name}, quick question about your online services."

        return lead
