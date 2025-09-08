# config.py
# Central configuration & helpers (tiny, functional).
import os
from pathlib import Path

# Modes & paths
DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("1", "true", "yes")
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "backend" / "prompts"
RESULTS_DIR = BASE_DIR / "results"
DEMO_DIR = BASE_DIR / "demo"

# LLM
# Recommend Gemini "Flash" for free-tier + image support
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))

# Email (SendGrid)
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "procurement@example.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Procurement Bot")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")  # empty => demo mode outbox

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# PDF/Image processing
ENABLE_PDF_TO_IMAGE = os.getenv("ENABLE_PDF_TO_IMAGE", "false").lower() in ("1","true","yes")
POPPLER_PATH = os.getenv("POPPLER_PATH", None)  # required on Windows for pdf2image

def get_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")

def ensure_dirs():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "outbox").mkdir(parents=True, exist_ok=True)

ensure_dirs()
