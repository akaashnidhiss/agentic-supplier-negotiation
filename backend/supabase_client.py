# supabase_client.py
from typing import List, Dict, Any
from . import config
try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None

_client = None

def _ensure_client():
    global _client
    if _client is None and config.SUPABASE_URL and config.SUPABASE_ANON_KEY and create_client:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
    return _client

def get_suppliers_by_category(categories: List[str]) -> List[Dict[str, Any]]:
    """
    Returns rows with keys: id, name, category, email.
    In DEMO_MODE or missing client, reads demo/suppliers_seed.csv
    """
    if config.DEMO_MODE or not _ensure_client():
        return _read_suppliers_seed(categories)
    data = []
    for cat in categories:
        res = _client.table("suppliers").select("id,name,category,email").eq("category", cat).execute()
        rows = res.data or []
        data.extend(rows)
    return data

def _read_suppliers_seed(categories: List[str]) -> List[Dict[str, Any]]:
    import csv, os
    path = config.DEMO_DIR / "suppliers_seed.csv"
    out = []
    if not path.exists():
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not categories or row.get("Category") in categories:
                out.append({"id": row.get("Supplier Name"), "name": row.get("Supplier Name"), "category": row.get("Category"), "email": row.get("email")})
    return out
