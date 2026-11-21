"""
Application Configuration and Settings
"""
import os
from typing import Optional

class Settings:
    PROJECT_NAME: str = "Mandate Radar"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration: defaults to local SQLite file for zero-config dev,
    # and seamlessly uses PostgreSQL in production when DATABASE_URL is set.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'mandate_radar.db'))}"
    )
    
    # JWT & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "mandate_radar_dev_secret_key_change_in_prod_9482104")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours
    
    # Neo4j Settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

settings = Settings()

