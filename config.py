import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Automatically load .env file if it exists
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

# Path to the clubs JSON database
CLUBS_DATA_PATH = BASE_DIR / "data" / "clubs.json"

# Optional Gemini API Key
# If set in environment, the agent leverages Google Gemini for enriched answers.
# If not set, the agent operates in built-in offline intelligent mode.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

# Flask server configuration
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
