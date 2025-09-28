"""
Configuration for College Recommendation System
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# System Configuration
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() == "true"

# Data Configuration
COLLEGE_DATA_PATH = "./data/colleges_sample.json"
VECTOR_DB_PATH = "./data/chroma_db"

# Demo Configuration
DEMO_API_KEY = "sk-or-v1-demo-key-replace-with-real-key"
DEMO_MODE = False  # Set to False to use real API calls