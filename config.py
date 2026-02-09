"""
Configuration module for Video Creator project.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ARK_API_KEY = os.environ.get("ARK_API_KEY")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# Model Endpoints
VIDEO_ENDPOINT = os.environ.get("VIDEO_ENDPOINT", "ep-20260206152338-7vwzw")  # Doubao-Seedance-2.0
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "ep-20260128152923-4g56t")  # Seed 2.0 for prompt enhancement

# Output directories
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
UPLOADS_DIR = os.path.join(OUTPUT_DIR, "uploads")

# Ensure output directories exist
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Video Generation Settings
DEFAULT_RATIO = "16:9"  # Options: 16:9, 9:16, 4:3, 3:4, 21:9, 1:1
DEFAULT_DURATION = 5  # Seconds (typically 5-12)
DEFAULT_WATERMARK = False

# Polling Settings
POLL_INTERVAL = 5  # Seconds between status checks
MAX_POLL_TIME = 600  # Maximum wait time (10 minutes)
