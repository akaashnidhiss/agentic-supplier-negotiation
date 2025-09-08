# backend/agent.py
from typing import List, Dict, Any
from . import config, llm
from .models import SpecItem
from . import event_log as log
import json as _json

def _clip(obj, max_chars: int = 1800):
    """Return preview for large payloads to keep logs readable."""
    try:
        s = _json.dumps(obj, ensure_ascii=False)
    except Exception:
        return obj
    if len(s) > max_chars:
        return {"_truncated": True, "preview": s[:max_chars]}
    return obj

def create_quote_schemas(specs: List[SpecItem]) -> List[Dict[str, Any]]:
    sys = config.get_prompt("INITIAL_QUOTE_SYS")
    results: List[Dict[str, Any]] = []
    with log.span("create_quote_schemas", items=len(specs)) as sp:
        for item in specs:
            user = {
                "instruction": "Generate initial quote schema for this SKU/service.",
                "sku_id": item.sku_id,
                "title": item.title,
                "raw_text_excerpt": item.raw_text[:2000],
                "expected_components": ["specification", "OTIF", "payment_timeline", "price"],
                "notes": "If any component is missing in spec, infer reasonable defaults; leave supplier_bids empty."
            }
            images = item.images if item.images else None
            sp.update("llm_request", sku_id=item.sku_id, input=_clip(user), images=len(images or []))
            data = llm.generate_json(system_prompt=sys, user_prompt=_json.dumps(user, ensure_ascii=False), images=images)
            # Normalize required structure
            data.setdefault("sku_id", item.sku_id)
            data.setdefault("title", item.title)
            data.setdefault("components", {})
            for comp in ["specification", "OTIF", "payment_timeline", "price"]:
                data["components"].setdefault(comp, {"ideal_value": None, "floor_value": None, "supplier_bids": []})
            sp.update("llm_response", sku_id=item.sku_id, output=_clip(data), components=list(data["components"].keys()))
            results.append(data)
    return results

def categorize_items(quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sys = config.get_prompt("CATEGORIZE_SKU_SERVICE_SYS")
    out = []
    with log.span("categorize_items", count=len(quotes)) as sp:
        for q in quotes:
            user = {"sku_id": q.get("sku_id"), "title": q.get("title"), "components": q.get("components", {})}
            sp.update("categorize_request", sku_id=q.get("sku_id"), input=_clip(user))
            resp = llm.generate_json(system_prompt=sys, user_prompt=_json.dumps(user, ensure_ascii=False))
            q["category"] = resp.get("category", "Uncategorized")
            q["confidence"] = resp.get("confidence", 0.5)
            q["rationale"] = resp.get("rationale", "")
            sp.update("categorize_result", sku_id=q["sku_id"], category=q["category"], confidence=q["confidence"], rationale=q["rationale"])
            out.append(q)
    return out

def prepare_initial_emails(grouped: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    sys = config.get_prompt("INITIAL_EMAIL_SYS")
    emails = []
    with log.span("prepare_initial_emails", categories=len(grouped)) as sp:
        for category, bundle in grouped.items():
            skus = [{"sku_id": q["sku_id"], "title": q.get("title", q["sku_id"])} for q in bundle.get("quotes", [])]
            suppliers = bundle.get("suppliers", [])
            sp.update("compose_batch", category=category, skus=[s["sku_id"] for s in skus], suppliers=len(suppliers))
            for supplier in suppliers:
                user = {
                    "supplier_name": supplier["name"],
                    "to_email": supplier["email"],
                    "category": category,
                    "skus": skus
                }
                resp = llm.generate_json(system_prompt=sys, user_prompt=_json.dumps(user, ensure_ascii=False))
                email = {
                    "to_email": supplier["email"],
                    "to_name": supplier["name"],
                    "subject": resp.get("subject") or f"RFQ for {category} items",
                    "body": resp.get("body") or f"Hello {supplier['name']},\nPlease quote for attached items.\nThanks.",
                    "meta": {"category": category, "supplier_id": supplier.get("id")}
                }
                sp.update("email_composed", to=supplier["email"], subject=email["subject"][:100])
                emails.append(email)
    return emails

def enrich_with_supplier_bids(quotes: List[Dict[str, Any]], bids: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_sku = {q["sku_id"]: q for q in quotes}
    with log.span("enrich_with_supplier_bids", skus=len(by_sku), bids=len(bids)) as sp:
        for bid in bids:
            sku = bid["sku_id"]
            supplier_name = bid.get("supplier_name", bid.get("supplier_id", "unknown"))
            if sku not in by_sku:
                sp.update("skipped_bid_unknown_sku", sku_id=sku, supplier=supplier_name)
                continue
            comps = bid.get("components", {})
            for comp, val in comps.items():
                entry = by_sku[sku].setdefault("components", {}).setdefault(
                    comp, {"ideal_value": None, "floor_value": None, "supplier_bids": []}
                )
                normalized_val = _avg(val) if isinstance(val, (list, tuple)) else val
                entry["supplier_bids"].append({
                    "supplier": supplier_name,
                    "value": normalized_val,
                    "source": "range_avg" if isinstance(val, (list, tuple)) else "quoted",
                    "raw": bid.get("raw_reply", "")
                })
                sp.update("bid_added", sku_id=sku, supplier=supplier_name, component=comp, value=normalized_val)
    return list(by_sku.values())

def _avg(x):
    try:
        return sum(x) / len(x)
    except Exception:
        return x
