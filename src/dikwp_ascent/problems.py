"""Public synthetic generators. Audits are withheld from search, not secret from owners."""
from __future__ import annotations
import math
import random
from .canonical import Invalid, finite, integer

TASKS = ("quadratic", "periodic", "sensor_shift", "scheduling")
WORLDS = ("in_distribution", "shifted_inputs", "proxy_failure")

def rows(task, seed, n=72, world="in_distribution"):
    if task not in TASKS or task == "scheduling" or world not in WORLDS:
        raise Invalid("Unknown regression family/world")
    rng = random.Random(seed)
    result = []
    for _ in range(n):
        bound = 4 if world == "shifted_inputs" else 2
        x = rng.uniform(-bound, bound)
        if task == "quadratic":
            y = 1 + 1.5*x + 0.8*x*x
        elif task == "periodic":
            y = 0.4 + 0.7*x + 2*math.sin(x)
        else:
            y = 2 + 1.2*x - 0.6*x*x
        y += rng.uniform(-0.08, 0.08)
        proxy = y + rng.uniform(-0.01, 0.01)
        if world == "proxy_failure":
            proxy = rng.uniform(-8, 8)
        result.append({"x": x, "proxy": proxy, "y": y})
    return result

def schedules(seed, n=60, world="in_distribution"):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        jobs = []
        for j in range(rng.randint(8, 14)):
            c = rng.randint(2, 15)
            v = rng.randint(4, 28)
            if world == "shifted_inputs":
                v += c * 2
            if world == "proxy_failure":
                v = rng.randint(2, 50)
            jobs.append({"cost": c, "value": v})
        out.append({"jobs": jobs, "capacity": rng.randint(18, 40)})
    return out

def make_split(task, seed, split):
    if task not in TASKS or split not in {"train", "development", "audit"}:
        raise Invalid("Unknown task or split")
    integer(seed, 0, 2**31-1, "seed")
    offset = {"train": 0, "development": 10000, "audit": 20000}[split]
    n = {"train": 72, "development": 48, "audit": 128}[split]
    worlds = ("in_distribution",) if split == "train" else WORLDS
    f = schedules if task == "scheduling" else lambda s,n,w: rows(task,s,n,w)
    return {w: f(seed+offset+j*1000,n,w) for j,w in enumerate(worlds)}

def validate_custom(data):
    """Custom regression only, strict three-way disjoint record content and named worlds."""
    from .canonical import exact_keys, digest
    exact_keys(data, {"train", "development", "audit"})
    if not isinstance(data["train"], list) or not 8 <= len(data["train"]) <= 4096:
        raise Invalid("Custom train size outside [8,4096]")
    groups = [data["train"]]
    for name in ("development", "audit"):
        if not isinstance(data[name], dict) or not 2 <= len(data[name]) <= 6:
            raise Invalid("At least two custom worlds required per evaluation split")
        for world, rs in data[name].items():
            if not isinstance(world, str) or not world.isidentifier() or len(world)>48:
                raise Invalid("Invalid world identifier")
            if not isinstance(rs, list) or not 8 <= len(rs) <= 4096:
                raise Invalid("Custom evaluation size outside [8,4096]")
            groups.append(rs)
    if set(data["development"]) != set(data["audit"]):
        raise Invalid("Development/audit world names must match")
    hashes = []
    for group in groups:
        current = set()
        for r in group:
            exact_keys(r, {"x", "y"}, {"proxy"})
            finite(r["x"], -10, 10, "x")
            finite(r["y"], -10000, 10000, "y")
            finite(r.get("proxy",0), -1000,1000,"proxy")
            current.add(digest({"x":float(r["x"]),"y":float(r["y"]),"proxy":float(r.get("proxy",0))}))
        hashes.append(current)
    for i,s in enumerate(hashes):
        for t in hashes[i+1:]:
            if s & t:
                raise Invalid("Identical records overlap across splits/worlds")
    return data
