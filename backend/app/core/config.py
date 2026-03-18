"""Central configuration for backend services."""

import os
from pathlib import Path
from dotenv import load_dotenv


# Resolve paths relative to the backend root so data and env files stay discoverable
BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "dummyData"
MOCK_DATA_DIR = BACKEND_DIR / "mockData"

# Data file mapping per agent
DATA_FILES = {
    "iqvia": "iqvia_data.json",
    "exim": "exim_data.json",
    "patent": "patent_data.json",
    "clinical": "clinical_data.json",
    "internal_knowledge": "internal_knowledge_data.json",
    "report_generator": "report_data.json",
}

# Human readable names per agent
AGENT_NAMES = {
    "iqvia": "IQVIA Insights Agent",
    "exim": "EXIM Trends Agent",
    "patent": "Patent Landscape Agent",
    "clinical": "Clinical Trials Agent",
    "internal_knowledge": "Internal Knowledge Agent",
    "report_generator": "Report Generator Agent",
}

# Mapping used for mockData lookups
AGENT_KEY_MAPPING = {
    "iqvia": "IQVIA Insights Agent",
    "exim": "EXIM Trade Agent",
    "patent": "Patent Landscape Agent",
    "clinical": "Clinical Trials Agent",
    "internal_knowledge": "Internal Knowledge Agent",
    "report_generator": "Report Generator Agent",
}

# CORS configuration
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]

# Clerk authentication
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")

# Mongo configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pharmassist_db")
MONGO_CHAT_COLLECTION = os.getenv("MONGO_CHAT_COLLECTION", "chat_sessions")

API_METADATA = {
    "title": "PharmAssist Intelligence API",
    "description": "Multi-agent pharmaceutical intelligence system for drug repurposing analysis",
    "version": "1.0.0",
}
