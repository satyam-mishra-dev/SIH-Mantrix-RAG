"""
Configuration settings for College Recommendation System
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Database Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(DATA_DIR / "chroma_db"))

# Model Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Verification Settings
ENABLE_VERIFICATION = os.getenv("ENABLE_VERIFICATION", "true").lower() == "true"
VERIFICATION_CACHE_HOURS = int(os.getenv("VERIFICATION_CACHE_HOURS", "24"))

# Evaluation Settings
EVALUATION_TEST_CASES = int(os.getenv("EVALUATION_TEST_CASES", "20"))
MENTOR_FEEDBACK_REQUIRED = os.getenv("MENTOR_FEEDBACK_REQUIRED", "true").lower() == "true"

# Data Sources
COLLEGE_DATA_PATH = DATA_DIR / "colleges_sample.json"
TEST_CASES_PATH = DATA_DIR / "test_cases.json"
EVALUATION_RESULTS_PATH = DATA_DIR / "evaluation_results.json"
MENTOR_UI_PATH = DATA_DIR / "mentor_annotation_ui.html"

# Government Sources for Verification
GOVERNMENT_SOURCES = {
    "nirf": "https://www.nirf.ac.in",
    "ugc": "https://www.ugc.ac.in",
    "aicte": "https://www.aicte-india.org",
    "digilocker": "https://www.digilocker.gov.in",
    "ncs": "https://www.ncs.gov.in"
}

# Default Recommendation Weights
DEFAULT_WEIGHTS = {
    "official_quality": 0.3,
    "mentor_trust": 0.2,
    "relevance": 0.3,
    "proximity": 0.2
}

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "College Recommendation System",
    "page_icon": "🎓",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
