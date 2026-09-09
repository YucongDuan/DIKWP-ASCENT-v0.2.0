"""Explicit data and proposal handoff. Files are data, not commands or tools."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from .canonical import Invalid, digest, finite
from .dsl import FEATURES, validate_program
from .problems import TASKS, make_split, validate_custom


def csv_dataset(path: str | Path) -> dict:
    raw = Path(path).read_bytes()
    if len(raw) > 2_000_000:
        raise Invalid("CSV exceeds 2 MB limit")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if reader.fieldnames != ["split", "world", "x", "y", "proxy"]:
        raise Invalid("CSV header must be split,world,x,y,proxy")
    data = {"train": [], "development": {}, "audit": {}}
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise Invalid("Malformed CSV row")
        split, world = row["split"], row["world"]
        if split not in data:
            raise Invalid("Split must be train, development or audit")
        if split == "train" and world != "in_distribution":
            raise Invalid("Training world must be in_distribution")
        try:
            item = {"x": float(row["x"]), "y": float(row["y"]), "proxy": float(row["proxy"] or 0)}
        except ValueError as exc:
            raise Invalid("Non-numeric CSV observation") from exc
        if split == "train":
            data[split].append(item)
        else:
            data[split].setdefault(world, []).append(item)
    return validate_custom(data)


def proposer_packet(task: str = "periodic", seed: int = 17, custom: dict | None = None) -> dict:
    """Export train/development observations only. No hidden reasoning or audit labels."""
    if custom is not None:
        if task != "custom_regression":
            raise Invalid("Custom data requires custom_regression")
        checked = validate_custom(custom)
        train, dev = checked["train"], checked["development"]
    else:
        if task not in TASKS:
            raise Invalid("Unknown task")
        train = make_split(task, seed, "train")["in_distribution"]
        dev = make_split(task, seed, "development")
    packet = {"schema": "ascent.proposer-request/1", "task": task,
              "purpose": "Suggest up to 32 data-only candidates for the declared bounded task",
              "allowed_features": list(FEATURES), "train": train, "development": dev,
              "response": "JSON array of allowed basis or scheduler programs; no scores, paths, code or tools",
              "network_authorized": False, "tools_authorized": False,
              "limitations": "This file may contain private training data. Review before manually sharing. Synthetic generator is public; withholding audit rows is not secrecy from source readers."}
    packet["digest"] = digest(packet)
    return packet


def validate_proposals(items: list, kind: str | None = None) -> list:
    if not isinstance(items, list) or not 1 <= len(items) <= 32:
        raise Invalid("Expected 1 to 32 candidate program objects")
    programs = [validate_program(item) for item in items]
    if kind is not None and any(p["kind"] != kind for p in programs):
        raise Invalid("Proposal family does not match task")
    return programs
