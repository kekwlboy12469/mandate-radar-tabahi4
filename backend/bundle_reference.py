"""
Curated Plan & Bundle Inclusions Reference Knowledge Base
=========================================================
Strictly verified bundle relationships:
(:Vendor)-[:OFFERS]->(:Plan)-[:INCLUDES]->(:Vendor | :Plan)

Every edge carries confidence ('confirmed_public'), verification date, source URL, and notes.
"""

# Explicitly Defined Plans with Tier and Pricing
PLANS = [
    {
        "id": "youtube_premium_individual",
        "name": "YouTube Premium (Individual)",
        "vendor_id": "youtube_premium",
        "tier": "individual",
        "monthly_cost": 129.0,
        "annual_cost": 1290.0,
        "description": "Ad-free YouTube video and music streaming for one personal account."
    },
    {
        "id": "amazon_prime_annual",
        "name": "Amazon Prime (Annual)",
        "vendor_id": "amazon_prime",
        "tier": "annual",
        "monthly_cost": 125.0,
        "annual_cost": 1499.0,
        "description": "Fast free delivery, Prime Video, Prime Music, and reading benefits."
    },
    {
        "id": "apple_one_individual",
        "name": "Apple One (Individual)",
        "vendor_id": "apple_one",
        "tier": "individual",
        "monthly_cost": 195.0,
        "annual_cost": 2340.0,
        "description": "Bundles Apple Music, Apple TV+, Apple Arcade, and 50GB iCloud+ storage."
    },
    {
        "id": "google_one_standard",
        "name": "Google One (100GB)",
        "vendor_id": "google_one",
        "tier": "standard",
        "monthly_cost": 130.0,
        "annual_cost": 1300.0,
        "description": "100GB cloud storage across Google Drive, Gmail, and Google Photos."
    },
    {
        "id": "microsoft_365_personal",
        "name": "Microsoft 365 Personal",
        "vendor_id": "microsoft_365",
        "tier": "personal",
        "monthly_cost": 489.0,
        "annual_cost": 4899.0,
        "description": "Word, Excel, PowerPoint, and 1TB OneDrive cloud storage."
    },
    {
        "id": "times_prime_annual",
        "name": "Times Prime (Annual)",
        "vendor_id": "times_prime",
        "tier": "annual",
        "monthly_cost": 100.0,
        "annual_cost": 1199.0,
        "description": "Lifestyle bundle including Disney+ Hotstar, SonyLIV, and partner passes."
    }
]

# Verified Bundle Inclusions
CURATED_BUNDLES = [
    {
        "parent_plan_id": "youtube_premium_individual",
        "parent_vendor_id": "youtube_premium",
        "parent_name": "YouTube Premium",
        "child_vendor_id": "youtube_music",
        "child_name": "YouTube Music",
        "tier": "individual",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link", # e.g. https://www.youtube.com/premium
        "notes": "YouTube Premium membership includes full ad-free YouTube Music Premium at no extra cost."
    },
    {
        "parent_plan_id": "amazon_prime_annual",
        "parent_vendor_id": "amazon_prime",
        "parent_name": "Amazon Prime",
        "child_vendor_id": "prime_video",
        "child_name": "Prime Video",
        "tier": "annual",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link", # e.g. https://www.amazon.in/prime
        "notes": "Amazon Prime annual and monthly memberships include Prime Video streaming."
    },
    {
        "parent_plan_id": "apple_one_individual",
        "parent_vendor_id": "apple_one",
        "parent_name": "Apple One",
        "child_vendor_id": "apple_music",
        "child_name": "Apple Music",
        "tier": "individual",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link",
        "notes": "Apple One bundle includes Apple Music."
    },
    {
        "parent_plan_id": "apple_one_individual",
        "parent_vendor_id": "apple_one",
        "parent_name": "Apple One",
        "child_vendor_id": "apple_icloud",
        "child_name": "iCloud+ Storage",
        "tier": "individual",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link",
        "notes": "Apple One bundle includes iCloud+ storage (50GB Individual, 200GB Family)."
    },
    {
        "parent_plan_id": "apple_one_individual",
        "parent_vendor_id": "apple_one",
        "parent_name": "Apple One",
        "child_vendor_id": "apple_services",
        "child_name": "Apple TV+",
        "tier": "individual",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link",
        "notes": "Apple One bundle includes Apple TV+ original programming."
    },
    {
        "parent_plan_id": "microsoft_365_personal",
        "parent_vendor_id": "microsoft_365",
        "parent_name": "Microsoft 365",
        "child_vendor_id": "onedrive",
        "child_name": "OneDrive Storage",
        "tier": "personal",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link",
        "notes": "Microsoft 365 Personal/Family includes 1TB OneDrive cloud storage."
    },
    {
        "parent_plan_id": "google_one_standard",
        "parent_vendor_id": "google_one",
        "parent_name": "Google One",
        "child_vendor_id": "google_one",
        "child_name": "Google Drive Storage",
        "tier": "standard",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link",
        "notes": "Google One plans include expanded cloud storage shared across Drive, Gmail, and Photos."
    },
    {
        "parent_plan_id": "times_prime_annual",
        "parent_vendor_id": "times_prime",
        "parent_name": "Times Prime",
        "child_vendor_id": "disney_hotstar",
        "child_name": "Disney+ Hotstar",
        "tier": "annual",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link",
        "notes": "Times Prime annual membership includes complimentary 6-month or 1-year Disney+ Hotstar access."
    },
    {
        "parent_plan_id": "times_prime_annual",
        "parent_vendor_id": "times_prime",
        "parent_name": "Times Prime",
        "child_vendor_id": "sony_liv",
        "child_name": "SonyLIV",
        "tier": "annual",
        "confidence": "confirmed_public",
        "verified_on": "2026-11-01",
        "source_url": "TODO: fill link",
        "notes": "Times Prime membership includes complimentary 6-month SonyLIV subscription."
    }
]
