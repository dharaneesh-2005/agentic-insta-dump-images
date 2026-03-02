"""Configuration settings for AI Instagram Dump Generator."""
import os
from pathlib import Path

# ComfyUI Connection Settings
COMFYUI_HOST = os.getenv("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", "8000"))
COMFYUI_BASE_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

# Paths
BASE_DIR = Path(__file__).parent
WORKFLOW_PATH = BASE_DIR / "workflows" / "workflow_api.json"
OUTPUT_DIR = BASE_DIR / "generated"
TEMP_DIR = BASE_DIR / "temp"
PROMPTS_DIR = BASE_DIR / "prompts"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Generation Settings
DEFAULT_BATCH_SIZE = 15
MIN_BATCH_SIZE = 10
MAX_BATCH_SIZE = 20

# Supported themes with display names
THEMES = {
    "cinematic": "🎬 Cinematic",
    "vintage": "📷 Vintage",
    "beach": "🏖️ Beach",
    "streetwear": "👟 Streetwear",
    "minimalist": "⚪ Minimalist",
    "dark_aesthetic": "🌑 Dark Aesthetic",
    "nature": "🌿 Nature",
    "urban": "🏙️ Urban",
    "luxury": "💎 Luxury",
    "casual": "😎 Casual",
    "formal": "👔 Formal",
    "artistic": "🎨 Artistic",
}

# Gender options
GENDERS = {
    "male": "Male",
    "female": "Female",
}

# Image settings
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp"]
MAX_IMAGE_SIZE_MB = 10

# API Settings
REQUEST_TIMEOUT = 300  # 5 minutes for generation
POLL_INTERVAL = 2  # seconds between status checks
MAX_RETRIES = 3
