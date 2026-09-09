"""Canonical data and bounded JSON intake; hashes do not establish external truth."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from typing import Any

class Invalid(ValueError):
    pass

class BudgetExceeded(RuntimeError):
    pass

class Stopped(RuntimeError):
    pass

def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def finite(x: Any, lo: float, hi: float, name: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) or not lo <= x <= hi:
        raise Invalid(f"{name} must be finite and in [{lo}, {hi}]")
    return float(x)

def integer(x: Any, lo: int, hi: int, name: str) -> int:
    finite(x, lo, hi, name)
    if type(x) is not int:
        raise Invalid(f"{name} must be an integer")
    return x

def exact_keys(obj: Any, required: set[str], optional: set[str] | None = None) -> None:
    if not isinstance(obj, dict) or required - obj.keys() or obj.keys() - required - (optional or set()):
        raise Invalid(f"Expected keys {sorted(required)}; optional {sorted(optional or set())}")

def _pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise Invalid(f"Duplicate JSON key: {k}")
        result[k] = v
    return result

def load_json(path: str | Path, max_bytes: int = 2_000_000):
    raw = Path(path).read_bytes()
    if len(raw) > max_bytes:
        raise Invalid("Input is larger than permitted")
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda x: (_ for _ in ()).throw(Invalid(x)))

def save_json(path: str | Path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
