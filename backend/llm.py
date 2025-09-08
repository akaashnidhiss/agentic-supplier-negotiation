# llm.py
"""
LLM gateway using Google's GenAI SDK (free-tier capable, image-friendly).
- Requires: pip install google-genai
- Auth: set GEMINI_API_KEY or GOOGLE_API_KEY env var.
"""
import json, re
from typing import List, Optional, Any, Dict
from PIL import Image
from io import BytesIO
from . import config
from dotenv import load_dotenv

load_dotenv()  # load .env

# --- GenAI SDK imports / client ---
try:
    from google import genai
    from google.genai.types import Part
    _CLIENT = genai.Client()  # picks up GEMINI_API_KEY or GOOGLE_API_KEY
    _INIT_ERROR = None
except Exception as e:
    _CLIENT = None
    Part = None
    _INIT_ERROR = e

JSON_INSTRUCTIONS = "Always respond with **only** minified JSON. Do not include prose."

def _ensure_client():
    if _CLIENT is None:
        raise RuntimeError(f"LLM client not initialized: {_INIT_ERROR}")

def _image_to_part(path: str):
    """Return a google.genai.types.Part for an image (JPEG)."""
    img = Image.open(path).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    data = buf.getvalue()
    # From the new SDK: use keyword args for Part constructors
    return Part.from_bytes(data=data, mime_type="image/jpeg")

def extract_json(text: str) -> Dict[str, Any]:
    """Robustly coerce LLM output into JSON dict."""
    if not text:
        return {}
    # 1) direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) fenced ```json blocks
    fence = re.findall(r"```json\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence:
        try:
            return json.loads(fence[0])
        except Exception:
            pass
    # 3) first {...} span
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start:end+1]
        try:
            return json.loads(snippet)
        except Exception:
            # small repair: remove trailing commas
            snippet = re.sub(r",(\s*[}\]])", r"\1", snippet)
            try:
                return json.loads(snippet)
            except Exception:
                pass
    return {}

def generate_json(
    system_prompt: str,
    user_prompt: str,
    images: Optional[List[str]] = None,
    tools: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    """
    Calls Gemini with optional image parts, enforcing JSON-only output.
    Returns a parsed dict (empty dict if parsing fails).
    """
    _ensure_client()
    sys = f"{system_prompt}\n\n{JSON_INSTRUCTIONS}"

    # Build content parts: user text + optional images
    parts: List[Any] = []
    try:
        parts.append(Part.from_text(text=sys))
    except Exception:
        parts.append(sys)
    # IMPORTANT: Part.from_text requires keyword arg
    if Part is not None:
        parts.append(Part.from_text(text=user_prompt))
        if images:
            for p in images:
                try:
                    parts.append(_image_to_part(p))
                except Exception:
                    # ignore bad image; continue
                    pass
    else:
        # Fallback: let SDK accept raw string if Part import failed
        parts.append(user_prompt)

    # New SDK call signature:
    #   client.models.generate_content(model=..., contents=[Part|str,...], system_instruction=str, config={...})
    response = _CLIENT.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=parts,
        config={
            "temperature": config.LLM_TEMPERATURE,
            "max_output_tokens": config.MAX_OUTPUT_TOKENS,
        },
    )

    # Prefer response.text; fallback to first candidate part text
    out_text = getattr(response, "text", None) or ""
    if not out_text and getattr(response, "candidates", None):
        try:
            # candidates[0].content.parts[0].text is typical
            out_text = response.candidates[0].content.parts[0].text
        except Exception:
            out_text = ""

    data = extract_json(out_text)
    return data or {}
