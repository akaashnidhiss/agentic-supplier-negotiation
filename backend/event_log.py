# backend/event_log.py
from __future__ import annotations
import json, time, uuid, os
from pathlib import Path
from typing import Any, Optional
from . import config

# Change path via env if you want separate files per run.
LOG_PATH = Path(os.getenv("AGENT_LOG_PATH", config.RESULTS_DIR / "agent_events.jsonl"))
RUN_ID: Optional[str] = None

def new_run(run_id: Optional[str] = None) -> str:
    """Generate or set a run_id and log the run start."""
    global RUN_ID
    RUN_ID = run_id or str(uuid.uuid4())
    log_event("_run", "start", run_id=RUN_ID)
    return RUN_ID

def log_event(step: str, message: str = "", level: str = "INFO", **payload: Any) -> None:
    """Append a structured event to JSONL and (optionally) echo to stdout."""
    global RUN_ID
    if RUN_ID is None:
        RUN_ID = str(uuid.uuid4())
    rec = {
        "ts": time.time(),
        "run_id": RUN_ID,
        "level": level,
        "step": step,
        "message": message,
        "payload": payload,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if os.getenv("AGENT_LOG_STDOUT", "1").lower() in ("1", "true", "yes"):
        print(f"[{time.strftime('%H:%M:%S')}] {step}: {message}")

class span:
    """Context manager to automatically log start/end + duration."""
    def __init__(self, step: str, **start_payload: Any):
        self.step = step
        self.start_payload = start_payload
        self.t0 = None

    def __enter__(self):
        self.t0 = time.time()
        log_event(self.step, "start", **self.start_payload)
        return self

    def update(self, message: str, **payload: Any):
        log_event(self.step, message, **payload)

    def __exit__(self, exc_type, exc, tb):
        dur_ms = int((time.time() - self.t0) * 1000) if self.t0 else None
        if exc:
            log_event(self.step, "error", level="ERROR", error=str(exc), duration_ms=dur_ms)
            return False
        log_event(self.step, "end", duration_ms=dur_ms)
        return False
