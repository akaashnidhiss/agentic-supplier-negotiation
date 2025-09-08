# email_client.py
"""
SendGrid-backed email client with DEMO outbox fallback.
"""
from typing import List, Dict, Any
from . import config
import os, json, time

def send_batch(emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not emails:
        return []
    if config.DEMO_MODE or not config.SENDGRID_API_KEY:
        return _write_outbox(emails)
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, From, To
    except Exception as e:
        # fall back
        return _write_outbox(emails)

    client = SendGridAPIClient(config.SENDGRID_API_KEY)
    results = []
    for e in emails:
        to_email = e["to_email"]
        subject = e["subject"]
        body = e["body"]
        message = Mail(
            from_email=(config.SENDGRID_FROM_EMAIL, config.SENDGRID_FROM_NAME),
            to_emails=[to_email],
            subject=subject,
            plain_text_content=body
        )
        try:
            resp = client.send(message)
            results.append({"to": to_email, "status": resp.status_code})
        except Exception as ex:
            results.append({"to": to_email, "status": "failed", "error": str(ex)})
    return results

def _write_outbox(emails: List[Dict[str, Any]]):
    out_dir = config.RESULTS_DIR / "outbox"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    path = out_dir / f"emails_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)
    # Also print minimal console summary
    summary = [{"to": e["to_email"], "subject": e["subject"][:60]} for e in emails]
    return [{"mode": "demo_outbox", "file": str(path), "summary": summary}]

def collect_replies() -> Dict[str, Any]:
    """
    DEMO: read replies from demo/simulated_replies.json
    """
    sim = config.DEMO_DIR / "simulated_replies.json"
    if sim.exists():
        import json
        with open(sim, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
