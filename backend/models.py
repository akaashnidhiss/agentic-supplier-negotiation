# models.py
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

@dataclass
class SpecItem:
    sku_id: str
    title: str
    raw_text: str = ""
    images: List[str] = field(default_factory=list)  # file paths to images (optional)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QuoteComponent:
    ideal_value: Optional[float] = None
    floor_value: Optional[float] = None
    supplier_bids: List[Dict[str, Any]] = field(default_factory=list)  # [{supplier: str, value: float, source: str, raw: str}]

@dataclass
class QuoteSchema:
    sku_id: str
    category: Optional[str] = None
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    components: Dict[str, QuoteComponent] = field(default_factory=dict)  # e.g., {"specification": QuoteComponent(), ...}

@dataclass
class Supplier:
    id: str
    name: str
    category: str
    email: str

@dataclass
class Bid:
    sku_id: str
    supplier_id: str
    supplier_name: str
    components: Dict[str, float]  # normalized numeric values for scoring
    raw_reply: str = ""

@dataclass
class ScoringFormula:
    # weights must sum to 1.0; direction: "higher" or "lower"
    weights: Dict[str, float] = field(default_factory=dict)
    directions: Dict[str, str] = field(default_factory=dict)
    # optional normalizers: min/max or target values per component
    min_values: Dict[str, float] = field(default_factory=dict)
    max_values: Dict[str, float] = field(default_factory=dict)

@dataclass
class Score:
    sku_id: str
    supplier_id: str
    supplier_name: str
    total_score: float
    component_scores: Dict[str, float]

@dataclass
class Scorecard:
    session_id: str
    scores: List[Score]
    formula: ScoringFormula

def to_json(obj) -> Dict[str, Any]:
    if hasattr(obj, "__dict__") or isinstance(obj, (list, dict)):
        def convert(o):
            if hasattr(o, "__dict__"):
                return {k: convert(v) for k, v in o.__dict__.items()}
            if isinstance(o, list):
                return [convert(i) for i in o]
            if isinstance(o, dict):
                return {k: convert(v) for k, v in o.items()}
            return o
        return convert(obj)
    return asdict(obj)
