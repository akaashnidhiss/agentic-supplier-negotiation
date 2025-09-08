# evaluator.py
from typing import List, Dict, Any
from .models import ScoringFormula, Score, Scorecard
from . import config, llm
import math, uuid, json

DEFAULT_FORMULA = {
    "weights": {"price": 0.5, "OTIF": 0.2, "payment_timeline": 0.2, "specification": 0.1},
    "directions": {"price": "lower", "OTIF": "higher", "payment_timeline": "higher", "specification": "higher"}
}

def derive_formula(quotes: List[Dict[str, Any]]) -> ScoringFormula:
    sys = config.get_prompt("WEIGHTED_SCORING_FORMULA_GEN_SYS")
    user = {"components_present": _collect_components(quotes), "request": "Return weights that sum to 1.0 and directions."}
    resp = llm.generate_json(system_prompt=sys, user_prompt=json.dumps(user))
    weights = resp.get("weights") or DEFAULT_FORMULA["weights"]
    directions = resp.get("directions") or DEFAULT_FORMULA["directions"]
    # Optional min/max
    mins = resp.get("min_values", {})
    maxs = resp.get("max_values", {})
    return ScoringFormula(weights=weights, directions=directions, min_values=mins, max_values=maxs)

def score_bids(quotes: List[Dict[str, Any]], formula: ScoringFormula) -> Scorecard:
    # Build per-sku per-supplier values
    rows = []
    for q in quotes:
        sku = q["sku_id"]
        comp_map = q.get("components", {})
        # collect all suppliers
        suppliers = set()
        for comp, obj in comp_map.items():
            for b in obj.get("supplier_bids", []):
                suppliers.add(b["supplier"])
        for supplier in suppliers:
            comp_vals: Dict[str, float] = {}
            for comp, obj in comp_map.items():
                # pick supplier's value if present
                val = None
                for b in obj.get("supplier_bids", []):
                    if b["supplier"] == supplier:
                        val = b.get("value")
                        break
                # simple normalization later
                if isinstance(val, (int, float)):
                    comp_vals[comp] = float(val)
            rows.append((sku, supplier, comp_vals))

    # Compute min/max per component to normalize [0,1]
    all_vals: Dict[str, List[float]] = {}
    for _, _, comps in rows:
        for k, v in comps.items():
            all_vals.setdefault(k, []).append(v)
    mins = {k: min(vs) for k, vs in all_vals.items()}
    maxs = {k: max(vs) for k, vs in all_vals.items()}

    scores: List[Score] = []
    for sku, supplier, comps in rows:
        comp_scores: Dict[str, float] = {}
        total = 0.0
        for comp, weight in formula.weights.items():
            if comp not in comps:
                continue
            raw = comps[comp]
            lo = formula.min_values.get(comp, mins.get(comp, raw))
            hi = formula.max_values.get(comp, maxs.get(comp, raw))
            if hi == lo:
                norm = 1.0
            else:
                # normalize to [0,1], then invert if "lower is better"
                t = (raw - lo) / (hi - lo)
                if formula.directions.get(comp, "higher") == "lower":
                    t = 1.0 - t
                norm = max(0.0, min(1.0, t))
            comp_scores[comp] = round(norm, 4)
            total += weight * norm
        scores.append(Score(sku_id=sku, supplier_id=supplier, supplier_name=supplier, total_score=round(total,4), component_scores=comp_scores))

    session_id = str(uuid.uuid4())
    return Scorecard(session_id=session_id, scores=scores, formula=formula)

def _collect_components(quotes: List[Dict[str, Any]]):
    comps = set()
    for q in quotes:
        for k in q.get("components", {}).keys():
            comps.add(k)
    return sorted(list(comps))
