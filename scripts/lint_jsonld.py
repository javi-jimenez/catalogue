#!/usr/bin/env python3
"""Comprueba que todo JSON publicado declara schema.org y un @type útil."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_SOURCES = ["index"]
THING_SOURCES = ["index", "entity", "people", "services", "promotions", "sites"]
errors: list[str] = []


def check(path: Path, *, require_type: bool = True) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: JSON inválido — {exc}")
        return
    if data.get("@context") != "https://schema.org":
        errors.append(f"{path}: @context ausente o distinto de https://schema.org")
    if require_type and not data.get("@type"):
        errors.append(f"{path}: sin @type")


for name in ROOT_SOURCES:
    path = ROOT / f"{name}.json"
    if not path.exists():
        errors.append(f"falta {name}.json")
        continue
    check(path)

for folder in sorted((ROOT / "things").iterdir()):
    if not folder.is_dir():
        continue
    # Se comprueba lo que la entidad declara, no una lista fija: una persona
    # no tiene servicios y no por ello está incompleta.
    manifest = json.loads((folder / "index.json").read_text(encoding="utf-8"))
    declared = [
        str(d.get("url", "")).removesuffix(".json")
        for d in manifest.get("dataset", [])
    ]
    for name in ["index"] + declared:
        path = folder / f"{name}.json"
        if not path.exists():
            errors.append(f"falta things/{folder.name}/{name}.json")
            continue
        check(path)

for path in sorted((ROOT / "docs").rglob("*.json")):
    check(path)

if errors:
    print(f"✗ {len(errors)} problema(s) de JSON-LD:")
    for err in errors:
        print(f"   - {err}")
    sys.exit(1)
print("✓ JSON-LD válido en fuentes y en el sitio publicado")
