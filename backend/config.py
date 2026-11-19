import os
import dns.resolver
from dotenv import load_dotenv

load_dotenv()

# Use Google DNS for MongoDB Atlas SRV lookups
_atlas_dns = dns.resolver.Resolver(configure=False)
_atlas_dns.nameservers = ["8.8.8.8", "8.8.4.4"]
dns.resolver.default_resolver = _atlas_dns


class Config:
    """Central configuration for the Flask application."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # CORS - restrict this to your real frontend origin in production
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # MongoDB Atlas
    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority",
    )
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "microbial_evolution_sim")

    # If True, the app runs without a live MongoDB connection (in-memory only).
    # Useful for local development / demos without Atlas credentials configured.
    MONGO_OPTIONAL = os.getenv("MONGO_OPTIONAL", "1") == "1"
