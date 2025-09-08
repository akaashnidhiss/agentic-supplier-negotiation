# backend/agent_functions.py
import os, zipfile, json
from typing import List, Dict, Any
from pathlib import Path
from .models import SpecItem, Bid
from . import config
from . import event_log as log

def parse_specs_zip(zip_path: str) -> List[SpecItem]:
    """Extracts the zip and returns a list of SpecItem."""
    items: List[SpecItem] = []
    extract_dir = Path(config.RESULTS_DIR) / "tmp_specs"
    with log.span("parse_specs_zip", zip_path=str(zip_path)) as sp:
        if extract_dir.exists():
            for p in extract_dir.rglob("*"):
                if p.is_file(): p.unlink()
            for p in sorted(extract_dir.glob("*"), reverse=True):
                if p.is_dir(): p.rmdir()
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
        sp.update("extracted", files=len(list(extract_dir.rglob("*"))))

        counter = 1
        for path in sorted(extract_dir.rglob("*")):
            if path.is_dir():
                continue
            suffix = path.suffix.lower()
            sku_id = f"SKU-{counter:03d}"
            counter += 1

            if suffix == ".pdf":
                images = []
                if config.ENABLE_PDF_TO_IMAGE:
                    try:
                        from pdf2image import convert_from_path
                        pages = convert_from_path(str(path), poppler_path=config.POPPLER_PATH)
                        for i, pg in enumerate(pages[:2]):
                            out = path.with_suffix(f".page{i+1}.jpg")
                            pg.save(out, "JPEG")
                            images.append(str(out))
                    except Exception as e:
                        sp.update("pdf_to_image_failed", file=str(path), error=str(e))
                raw_text = _extract_pdf_text(path)
                items.append(SpecItem(sku_id=sku_id, title=path.stem, raw_text=raw_text, images=images, metadata={"path": str(path)}))
                sp.update("item_built_pdf", sku_id=sku_id, file=str(path), images=len(images), text_len=len(raw_text or ""))
            elif suffix in (".txt", ".md", ".csv"):
                raw_text = path.read_text(encoding="utf-8", errors="ignore")
                items.append(SpecItem(sku_id=sku_id, title=path.stem, raw_text=raw_text, images=[], metadata={"path": str(path)}))
                sp.update("item_built_text", sku_id=sku_id, file=str(path), text_len=len(raw_text))
            elif suffix in (".png", ".jpg", ".jpeg"):
                items.append(SpecItem(sku_id=sku_id, title=path.stem, raw_text="", images=[str(path)], metadata={"path": str(path)}))
                sp.update("item_built_image", sku_id=sku_id, file=str(path))
            else:
                items.append(SpecItem(sku_id=sku_id, title=path.stem, raw_text="", images=[], metadata={"path": str(path), "note": "Unsupported file type"}))
                sp.update("item_built_other", sku_id=sku_id, file=str(path), note="unsupported")
        sp.update("items_ready", count=len(items))
    return items

def _extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        texts = []
        for page in reader.pages[:5]:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
    except Exception:
        return ""

def group_by_category(quotes: List[Dict[str, Any]], supplier_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Returns dict: {category: {quotes: [...], suppliers: [...]}} for batching emails."""
    with log.span("group_by_category", quotes=len(quotes), suppliers=len(supplier_rows)) as sp:
        grouped: Dict[str, Dict[str, Any]] = {}
        by_cat: Dict[str, List[Dict[str, Any]]] = {}
        for s in supplier_rows:
            by_cat.setdefault(s["category"], []).append(s)
        for q in quotes:
            cat = q.get("category") or "Uncategorized"
            grouped.setdefault(cat, {"quotes": [], "suppliers": by_cat.get(cat, [])})
            grouped[cat]["quotes"].append(q)
        sp.update("grouped_summary", categories=len(grouped), counts={k: {"quotes": len(v["quotes"]), "suppliers": len(v["suppliers"])} for k, v in grouped.items()})
        return grouped

def parse_supplier_replies(source: str) -> Dict[str, Any]:
    """For demo: reads JSON file mapping suppliers to replies."""
    with log.span("parse_supplier_replies", source=str(source)) as sp:
        try:
            with open(source, "r", encoding="utf-8") as f:
                data = json.load(f)
            supplier_cnt = len(data)
            sku_cnt = sum(len(v) for v in data.values()) if isinstance(data, dict) else 0
            sp.update("parsed", suppliers=supplier_cnt, skus=sku_cnt)
            return data
        except Exception as e:
            sp.update("parse_failed", error=str(e))
            return {}

def build_bid_payloads(replies: Dict[str, Any]) -> List[Bid]:
    bids: List[Bid] = []
    with log.span("build_bid_payloads") as sp:
        for supplier_key, skus in (replies or {}).items():
            for sku_id, payload in (skus or {}).items():
                components = payload.get("components", {})
                bids.append(Bid(
                    sku_id=sku_id,
                    supplier_id=str(supplier_key),
                    supplier_name=str(supplier_key),
                    components=components,
                    raw_reply=payload.get("raw_reply", "")
                ))
        sp.update("bids_built", suppliers=len(replies or {}), bids=len(bids))
    return bids
