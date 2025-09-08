# main.py
"""
Orchestrates the end-to-end demo flow.
"""
import json, sys
from pathlib import Path
from backend import config, agent_functions as F, agent, evaluator, supabase_client, email_client
from backend import event_log

def run_demo(specs_zip: str = None):
    run_id = event_log.new_run()
    print(f"Agent run_id: {run_id} | Log: {event_log.LOG_PATH}")    
    # 1) Load specs
    if not specs_zip:
        specs_zip = str(config.DEMO_DIR / "sample_specs.zip")
    specs = F.parse_specs_zip(specs_zip)

    # 2) Generate quote schemas
    quote_schemas = agent.create_quote_schemas(specs)

    # 3) Categorize
    quote_schemas = agent.categorize_items(quote_schemas)

    # 4) Fetch suppliers & prepare emails
    categories = sorted({q.get("category","Uncategorized") for q in quote_schemas})
    supplier_rows = supabase_client.get_suppliers_by_category(categories)
    grouped = F.group_by_category(quote_schemas, supplier_rows)
    emails = agent.prepare_initial_emails(grouped)

    # 5) Send emails
    send_results = email_client.send_batch(emails)

    # 6) Collect replies (demo) -> build bids
    raw_replies = email_client.collect_replies()
    bids = F.build_bid_payloads(raw_replies)

    # 7) Enrich schemas with supplier bids
    enriched = agent.enrich_with_supplier_bids(quote_schemas, [b.__dict__ for b in bids])

    # 8) Derive formula & score
    formula = evaluator.derive_formula(enriched)
    scorecard = evaluator.score_bids(enriched, formula)

    # 9) Save & print summary
    out_path = config.RESULTS_DIR / "scorecard.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "form": {
                "weights": formula.weights,
                "directions": formula.directions,
                "min_values": formula.min_values,
                "max_values": formula.max_values,
            },
            "scores": [s.__dict__ for s in scorecard.scores],
            "session_id": scorecard.session_id
        }, f, ensure_ascii=False, indent=2)

    print("\n=== DEMO SUMMARY ===")
    print(f"Emails: {len(emails)} (see results/outbox/ in DEMO_MODE)")
    print(f"Scores stored at: {out_path}")
    # show top pick per SKU
    from collections import defaultdict
    by_sku = defaultdict(list)
    for s in scorecard.scores:
        by_sku[s.sku_id].append(s)
    for sku, arr in by_sku.items():
        arr.sort(key=lambda x: x.total_score, reverse=True)
        top = arr[0]
        print(f"SKU {sku}: winner -> {top.supplier_name} (score={top.total_score})")

if __name__ == "__main__":
    specs_zip = sys.argv[1] if len(sys.argv) > 1 else None
    run_demo(specs_zip)
