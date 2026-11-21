"""
Curated Bundle Inclusions Reference Knowledge Base
Strictly verified bundle relationships: (:Plan/:Service)-[:INCLUDES]->(:Service)
Every relationship carries confidence, verification date, source URL, and notes.
"""

CURATED_BUNDLES = [
    {
        "parent_id": "youtube_premium",
        "parent_name": "YouTube Premium",
        "child_id": "youtube_music",
        "child_name": "YouTube Music",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link", # e.g. https://www.youtube.com/premium
        "notes": "YouTube Premium membership includes full ad-free YouTube Music Premium at no extra cost."
    },
    {
        "parent_id": "amazon_prime",
        "parent_name": "Amazon Prime",
        "child_id": "prime_video",
        "child_name": "Prime Video",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link", # e.g. https://www.amazon.in/prime
        "notes": "Amazon Prime annual and monthly memberships include Prime Video streaming."
    },
    {
        "parent_id": "apple_one",
        "parent_name": "Apple One",
        "child_id": "apple_music",
        "child_name": "Apple Music",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link",
        "notes": "Apple One bundle includes Apple Music."
    },
    {
        "parent_id": "apple_one",
        "parent_name": "Apple One",
        "child_id": "apple_icloud",
        "child_name": "iCloud+ Storage",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link",
        "notes": "Apple One bundle includes iCloud+ storage (50GB Individual, 200GB Family, 2TB Premier)."
    },
    {
        "parent_id": "apple_one",
        "parent_name": "Apple One",
        "child_id": "apple_tv_plus",
        "child_name": "Apple TV+",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link",
        "notes": "Apple One bundle includes Apple TV+ original programming."
    },
    {
        "parent_id": "apple_one",
        "parent_name": "Apple One",
        "child_id": "apple_arcade",
        "child_name": "Apple Arcade",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link",
        "notes": "Apple One bundle includes Apple Arcade gaming."
    },
    {
        "parent_id": "microsoft_365",
        "parent_name": "Microsoft 365",
        "child_id": "onedrive",
        "child_name": "OneDrive Storage",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link",
        "notes": "Microsoft 365 Personal/Family includes 1TB OneDrive cloud storage."
    },
    {
        "parent_id": "google_one",
        "parent_name": "Google One",
        "child_id": "google_drive_extra",
        "child_name": "Google Drive Storage",
        "confidence": "confirmed_public",
        "verified_on": "2026-01-01",
        "source_url": "TODO: fill link",
        "notes": "Google One plans include expanded cloud storage shared across Drive, Gmail, and Photos."
    }
]
