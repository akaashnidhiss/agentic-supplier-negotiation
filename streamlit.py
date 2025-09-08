import streamlit as st
import pandas as pd
import json, io, zipfile, time
from pathlib import Path

# Backend imports
from backend import (
    config,
    agent_functions as F,
    agent,
    evaluator,
    supabase_client,
    email_client,
    event_log,
)

# ---------- Helpers ----------
def _save_upload(file) -> Path:
    up_dir = Path(config.RESULTS_DIR) / "uploads"
    up_dir.mkdir(parents=True, exist_ok=True)
    p = up_dir / f"upload_{int(time.time())}.zip"
    p.write_bytes(file.read())
    return p

def _zip_preview(zip_path: Path, max_chars=800):
    items = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for name in sorted(z.namelist()):
            try:
                if name.lower().endswith((".txt", ".md", ".csv")):
                    txt = z.read(name).decode("utf-8", errors="ignore")
                    if len(txt) > max_chars:
                        txt = txt[:max_chars] + "\n...[truncated]"
                    items.append({"name": name, "text": txt})
                else:
                    items.append({"name": name, "text": "(binary/unsupported preview)"})
            except Exception as e:
                items.append({"name": name, "text": f"(error reading: {e})"})
    return items

def _carousel(idx_label, items, render_fn):
    if not items:
        st.info("Nothing to show yet.")
        return
    n = len(items)
    i = st.slider(idx_label, 1, n, 1, key=idx_label)
    render_fn(items[i-1], i, n)

def _schema_card(q, i, n):
    st.markdown(f"**SKU {q.get('sku_id','?')}**  _(item {i}/{n})_")
    st.json(q)

def _supplier_table_for_sku(q, grouped):
    cat = q.get("category") or "Uncategorized"
    bundle = grouped.get(cat, {"suppliers": []})
    df = pd.DataFrame(bundle["suppliers"])
    if df.empty:
        st.info("No suppliers found for this category.")
    else:
        st.caption(f"Category: **{cat}**  •  Suppliers: {len(df)}")
        st.dataframe(df[["name", "email", "category"]], use_container_width=True)

def _email_card(e, i, n):
    st.markdown(f"**Email {i}/{n} → {e['to_name']}**  `<{e['to_email']}>`")
    st.write(f"**Subject:** {e['subject']}")
    st.code(e["body"])

def _email_chain_card(supplier_name, emails_for_supplier, replies_for_supplier):
    st.markdown(f"### 📬 {supplier_name}")
    for em in emails_for_supplier:
        with st.expander("Agent → Supplier (initial RFQ)", expanded=True):
            st.write(f"**To:** {em['to_name']} `<{em['to_email']}>`")
            st.write(f"**Subject:** {em['subject']}")
            st.code(em["body"])
    if replies_for_supplier:
        for sku_id, payload in replies_for_supplier.items():
            with st.expander(f"Supplier → Agent (reply for {sku_id})", expanded=True):
                st.code(payload.get("raw_reply", "(no text)"))
                st.json(payload.get("components", {}))
    else:
        st.info("No reply available (demo shows from simulated_replies.json).")

def _score_card(scorecard):
    # Show formula
    st.subheader("Weighted scoring formula")
    st.json({
        "weights": scorecard.formula.weights,
        "directions": scorecard.formula.directions,
        "min_values": scorecard.formula.min_values,
        "max_values": scorecard.formula.max_values,
    })

    # Per‑SKU carousel of rankings
    by_sku = {}
    for s in scorecard.scores:
        by_sku.setdefault(s.sku_id, []).append(s)
    skus = sorted(by_sku.keys())
    if not skus:
        st.info("No scores computed.")
        return
    idx = st.slider("Ranking — pick SKU", 1, len(skus), 1)
    sku = skus[idx-1]
    rows = sorted(by_sku[sku], key=lambda x: x.total_score, reverse=True)
    df = pd.DataFrame([{
        "supplier": r.supplier_name,
        "total_score": r.total_score,
        **{f"{k}_score": v for k, v in r.component_scores.items()}
    } for r in rows])
    st.markdown(f"**SKU {sku} — ranking**")
    st.dataframe(df, use_container_width=True)

def _load_log_df():
    p = event_log.LOG_PATH
    if not p.exists():
        return pd.DataFrame(), pd.DataFrame()
    rows = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    if not rows:
        return pd.DataFrame(), pd.DataFrame()

    # Raw keeps a 'payload' column for display/search
    raw = pd.DataFrame(rows)
    raw["time"] = pd.to_datetime(raw["ts"], unit="s")

    # Flat expands payload.* into columns for filtering
    flat = pd.json_normalize(rows, sep=".")
    flat["time"] = pd.to_datetime(flat["ts"], unit="s")

    # Sort both chronologically
    raw = raw.sort_values("time")
    flat = flat.sort_values("time")
    return raw, flat

# ---------- UI ----------
st.set_page_config("Vendor Negotiation Agent", layout="wide")
st.title("Vendor Negotiation Agent — Streamlit Demo")

# Session state scaffolding
ss = st.session_state
for k in [
    "run_id","zip_path","demo","specs","quotes_initial","quotes_categorized",
    "categories","supplier_rows","grouped","emails","send_results","raw_replies",
    "bids","enriched","formula","scorecard"
]:
    ss.setdefault(k, None)

# Start run
if ss["run_id"] is None:
    ss["run_id"] = event_log.new_run()
st.caption(f"Run ID: `{ss['run_id']}`  •  Log: `{event_log.LOG_PATH}`")

# ---------- Step 1: Upload or Demo ----------
st.header("1) Upload Zip folder of SKU/Service details")
col1, col2 = st.columns([2,1])
with col1:
    ss["demo"] = st.toggle("Use Demo Zip", value=True, help="If on, loads demo/sample_specs.zip")
with col2:
    uploaded = st.file_uploader("Or upload your own .zip", type=["zip"], label_visibility="collapsed")

if ss["demo"]:
    demo_zip = config.DEMO_DIR / "sample_specs.zip"
    st.success("Using demo zip")
    with st.expander("Preview demo specs (carousel)", expanded=False):
        items = _zip_preview(demo_zip)
        _carousel("demo_preview", items, lambda it, i,n: (st.markdown(f"**{it['name']}** ({i}/{n})"), st.code(it["text"])))
    ss["zip_path"] = demo_zip
else:
    if uploaded:
        ss["zip_path"] = _save_upload(uploaded)
        with st.expander("Preview uploaded archive"):
            with zipfile.ZipFile(ss["zip_path"], "r") as z:
                names = sorted(z.namelist())
            st.write(f"Found **{len(names)}** files")
            st.write(names[:20] + (["…"] if len(names)>20 else []))
    else:
        st.info("Upload a .zip or toggle Demo Zip to continue.")

st.divider()

# ---------- Step 2: Ingest ----------
st.header("2) Ingest SKU/Service details")
if st.button("Ingest & Generate Quote Schemas", use_container_width=True, type="primary", disabled=not ss["zip_path"]):
    event_log.log_event("ui", "ingest_clicked", zip=str(ss["zip_path"]))
    ss["specs"] = F.parse_specs_zip(str(ss["zip_path"]))
    ss["quotes_initial"] = agent.create_quote_schemas(ss["specs"])
    st.success(f"Ingested {len(ss['specs'])} items and generated quote schemas.")

if ss["quotes_initial"]:
    st.subheader("Generated quote schema — carousel per SKU")
    _carousel("schema_carousel", ss["quotes_initial"], _schema_card)

st.divider()

# ---------- Step 3: Categorize + Suppliers ----------
st.header("3) Find applicable suppliers from database")
if st.button("Categorize SKUs & Lookup Suppliers", use_container_width=True, disabled=not ss.get("quotes_initial")):
    event_log.log_event("ui", "categorize_clicked")
    ss["quotes_categorized"] = agent.categorize_items(ss["quotes_initial"])
    ss["categories"] = sorted({q.get("category","Uncategorized") for q in ss["quotes_categorized"]})
    ss["supplier_rows"] = supabase_client.get_suppliers_by_category(ss["categories"])
    ss["grouped"] = F.group_by_category(ss["quotes_categorized"], ss["supplier_rows"])
    st.success(f"Categorized {len(ss['quotes_categorized'])} SKUs across {len(ss['categories'])} categories.")

if ss.get("quotes_categorized") and ss.get("grouped"):
    st.write("Then: it categorizes each SKU, searches company DB for matching suppliers, and shows results.")
    st.subheader("Suppliers per SKU — carousel")
    _carousel(
        "suppliers_carousel",
        ss["quotes_categorized"],
        lambda q,i,n: _supplier_table_for_sku(q, ss["grouped"])
    )

st.divider()

# ---------- Step 4: Draft emails ----------
st.header("4) Draft initial RFP email to applicable suppliers")
if st.button("Draft Emails", use_container_width=True, disabled=not ss.get("grouped")):
    event_log.log_event("ui", "draft_emails_clicked")
    ss["emails"] = agent.prepare_initial_emails(ss["grouped"])
    st.success(f"Drafted {len(ss['emails'])} emails.")

if ss.get("emails"):
    st.subheader("Email drafts — carousel")
    _carousel("emails_carousel", ss["emails"], _email_card)

st.divider()

# ---------- Step 5: Send emails & show chain ----------
st.header("5) Send Initial RFP Email")
if st.button("Send Emails", use_container_width=True, disabled=not ss.get("emails")):
    event_log.log_event("ui", "send_emails_clicked")
    ss["send_results"] = email_client.send_batch(ss["emails"])
    ss["raw_replies"] = email_client.collect_replies()
    st.success("Emails dispatched (demo: saved to results/outbox). Loaded simulated replies.")

if ss.get("emails") and ss.get("raw_replies") is not None:
    st.subheader("Supplier email chain (per supplier)")
    # group outbox emails by supplier name (to_name) for display
    emails_by_supp = {}
    for e in ss["emails"]:
        emails_by_supp.setdefault(e["to_name"], []).append(e)
    for supplier_name in sorted(emails_by_supp.keys()):
        replies_for_supplier = ss["raw_replies"].get(supplier_name, {})
        _email_chain_card(supplier_name, emails_by_supp[supplier_name], replies_for_supplier)

st.divider()

# ---------- Step 6: Score & Ranking ----------
st.header("6) Generate weighted scoring formula & final ranking")
if st.button("Score Bids & Rank Vendors", use_container_width=True, disabled=not ss.get("quotes_categorized")):
    event_log.log_event("ui", "score_clicked")
    # Enrich schemas with supplier replies (demo)
    bids = F.build_bid_payloads(ss.get("raw_replies") or {})
    ss["enriched"] = agent.enrich_with_supplier_bids(ss["quotes_categorized"], [b.__dict__ for b in bids])
    ss["formula"] = evaluator.derive_formula(ss["enriched"])
    ss["scorecard"] = evaluator.score_bids(ss["enriched"], ss["formula"])
    st.success("Computed scores and rankings.")

if ss.get("scorecard"):
    _score_card(ss["scorecard"])

st.divider()

# ---------- Log viewer ----------
with st.expander("View Agent Log (JSONL)", expanded=False):
    raw_df, flat_df = _load_log_df()
    if raw_df.empty:
        st.info("No log entries yet.")
    else:
        st.caption("Tip: toggle between a simple view (with raw payload) and a flattened view (payload.* columns).")
        view_mode = st.radio("View", ["Simple", "Flattened"], horizontal=True)

        base_df = raw_df if view_mode == "Simple" else flat_df
        steps = sorted(base_df["step"].dropna().unique().tolist())
        sel_steps = st.multiselect("Filter steps", steps, default=[])

        view = base_df if not sel_steps else base_df[base_df["step"].isin(sel_steps)]

        if view_mode == "Simple":
            # Show raw payload as a compact JSON string column
            v = view.copy()
            v["payload_str"] = v.get("payload", {}).apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else str(x))
            cols = [c for c in ["time", "run_id", "level", "step", "message", "payload_str"] if c in v.columns]
            st.dataframe(v[cols], width="stretch", height=380)
        else:
            # Flattened columns already include payload.* fields
            # Pick some common columns if present
            pref = ["time","run_id","level","step","message"]
            cols = [c for c in pref if c in view.columns]
            # Add a few popular payload fields if present
            extras = [c for c in view.columns if c.startswith("payload.")][:8]
            cols = cols + extras
            st.dataframe(view[cols], width="stretch", height=380)
