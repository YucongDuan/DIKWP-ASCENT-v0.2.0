"""Non-executable program descriptions. No eval, exec, imports or paths in candidates."""
from __future__ import annotations
import math
from .canonical import exact_keys, finite, integer, Invalid, digest

FEATURES = ("x", "x2", "x3", "sin", "cos", "proxy")
RIDGES = (0.000001, 0.001, 0.1)

def validate_program(p):
    if not isinstance(p, dict):
        raise Invalid("Program must be an object")
    if p.get("kind") == "basis":
        exact_keys(p, {"kind", "features", "ridge"})
        fs = p["features"]
        if not isinstance(fs, list) or len(fs) > 6 or any(not isinstance(f,str) or f not in FEATURES for f in fs) or len(set(fs)) != len(fs):
            raise Invalid("Features must be unique names from the fixed vocabulary")
        finite(p["ridge"], 0.000001, 1, "ridge")
        return {"kind": "basis", "features": sorted(fs), "ridge": float(p["ridge"])}
    if p.get("kind") == "scheduler":
        exact_keys(p, {"kind", "cost_power", "swap_passes"})
        finite(p["cost_power"], 0, 2, "cost_power")
        integer(p["swap_passes"], 0, 3, "swap_passes")
        return dict(p)
    raise Invalid("Unknown program kind; source code, tools and authority fields are forbidden")

def feature_vector(features, row):
    x = finite(row["x"], -10, 10, "x")
    proxy = finite(row.get("proxy", 0), -1000, 1000, "proxy")
    mapping = {"x": x, "x2": x*x, "x3": x*x*x, "sin": math.sin(x), "cos": math.cos(x), "proxy": proxy}
    return [1.0] + [mapping[k] for k in features]

def solve_linear(a, b):
    """Small pivoted normal-equation solve. Not intended for ill-conditioned large data."""
    n = len(b)
    m = [list(row) + [b[i]] for i, row in enumerate(a)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda j: abs(m[j][i]))
        if abs(m[pivot][i]) < 1e-14:
            raise Invalid("Singular feature system")
        m[i], m[pivot] = m[pivot], m[i]
        d = m[i][i]
        for k in range(i, n+1):
            m[i][k] /= d
        for j in range(n):
            if j == i:
                continue
            d = m[j][i]
            for k in range(i, n+1):
                m[j][k] -= d*m[i][k]
    return [m[i][-1] for i in range(n)]

def fit(program, rows):
    p = validate_program(program)
    if p["kind"] != "basis":
        return {"program": p}
    if not 8 <= len(rows) <= 4096:
        raise Invalid("Regression training rows outside [8,4096]")
    X = [feature_vector(p["features"], r) for r in rows]
    y = [finite(r["y"], -10000, 10000, "y") for r in rows]
    n = len(X[0])
    a = [[sum(row[i]*row[j] for row in X) + (p["ridge"] if i == j and i else 0.0) for j in range(n)] for i in range(n)]
    b = [sum(row[i]*v for row, v in zip(X, y)) for i in range(n)]
    return {"program": p, "coefficients": solve_linear(a, b)}

def predict(model, row):
    fs = feature_vector(model["program"]["features"], row)
    if len(fs) != len(model["coefficients"]):
        raise Invalid("Coefficient width mismatch")
    v = sum(a*b for a, b in zip(fs, model["coefficients"]))
    finite(v, -1e9, 1e9, "prediction")
    return v

def schedule(program, case):
    """Greedy policy plus bounded one-for-one local repair; never emits infeasible sets."""
    p = validate_program(program)
    jobs, capacity = case["jobs"], case["capacity"]
    order = sorted(range(len(jobs)), key=lambda i: (-(jobs[i]["value"]/(jobs[i]["cost"]**p["cost_power"])), i))
    chosen = []
    used = 0
    for i in order:
        if used + jobs[i]["cost"] <= capacity:
            chosen.append(i)
            used += jobs[i]["cost"]
    for _ in range(p["swap_passes"]):
        best = None
        for old in sorted(chosen):
            for new in order:
                if new in chosen:
                    continue
                gain = jobs[new]["value"] - jobs[old]["value"]
                cost = used - jobs[old]["cost"] + jobs[new]["cost"]
                if gain > 0 and cost <= capacity and (best is None or gain > best[0]):
                    best = (gain, old, new, cost)
        if best is None:
            break
        _, old, new, used = best
        chosen.remove(old)
        chosen.append(new)
        for i in order:
            if i not in chosen and used + jobs[i]["cost"] <= capacity:
                chosen.append(i)
                used += jobs[i]["cost"]
    return sorted(chosen)


def validate_model(model):
    """Validate an already fitted data-only policy without refitting its parameters."""
    if not isinstance(model, dict) or not isinstance(model.get("program"), dict):
        raise Invalid("Fitted model object required")
    program = validate_program(model["program"])
    if program != model["program"]:
        raise Invalid("Frozen model feature ordering must be canonical")
    if program["kind"] == "scheduler":
        exact_keys(model, {"program"})
        return {"program": program}
    exact_keys(model, {"program", "coefficients"})
    values = model["coefficients"]
    if not isinstance(values, list) or len(values) != len(program["features"]) + 1:
        raise Invalid("Fitted model coefficient width mismatch")
    coefficients = [finite(v, -1e9, 1e9, "coefficient") for v in values]
    return {"program": program, "coefficients": coefficients}
