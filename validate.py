#!/usr/bin/env python3
"""Valida el catálogo: JSON válido, referencias cruzadas y campos obligatorios.

Estructura:
    index.json                     ← lista de empresas
    things/<slug>/index.json       ← manifiesto de esa entidad
    things/<slug>/*.json           ← organization, people, services, promotions, sites

Uso:
    python3 validate.py            # exit 1 si algo no cuadra
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
THINGS = ROOT / "things"
DATASETS = ["organization", "people", "services", "promotions", "sites"]

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)}: JSON inválido — {exc}")
        return {}
    if data.get("@context") != "https://schema.org":
        fail(f"{path.relative_to(ROOT)}: @context debe ser https://schema.org")
    if not data.get("@type"):
        fail(f"{path.relative_to(ROOT)}: sin @type")
    return data


def check_thing(slug: str, folder: Path) -> dict:
    org = {}
    for name in DATASETS:
        path = folder / f"{name}.json"
        if not path.exists():
            fail(f"{slug}: falta {name}.json")
            continue
        data = load(path)
        if name == "organization":
            org = data

    manifest = load(folder / "index.json") if (folder / "index.json").exists() else {}
    listed = {
        str(d.get("url", "")).rsplit("/", 1)[-1]
        for d in manifest.get("dataset", [])
    }
    for name in DATASETS:
        if f"{name}.json" not in listed:
            fail(f"{slug}/index.json: no declara {name}.json en dataset[]")

    org_id = org.get("@id")
    if not org.get("vatID"):
        fail(f"{slug}: organization.json sin vatID")

    people = load(folder / "people.json").get("itemListElement", []) if (folder / "people.json").exists() else []
    person_ids = {p.get("@id") for p in people}
    founder = (org.get("founder") or {}).get("@id")
    if founder and founder not in person_ids:
        fail(f"{slug}: founder {founder} no está en people.json")
    for emp in org.get("employee") or []:
        if emp.get("@id") not in person_ids:
            fail(f"{slug}: employee {emp.get('@id')} no está en people.json")

    for person in people:
        ident = person.get("identifier") or {}
        if ident.get("propertyID") == "ORCID" and len(str(ident.get("value", ""))) != 19:
            fail(f"{slug}: ORCID raro en {person.get('name')}")

    services = load(folder / "services.json").get("itemListElement", []) if (folder / "services.json").exists() else []
    seen: set[str] = set()
    for svc in services:
        ident = svc.get("identifier")
        if not ident:
            fail(f"{slug}/services.json: servicio sin identifier")
        elif ident in seen:
            fail(f"{slug}/services.json: identifier duplicado '{ident}'")
        seen.add(ident)
        price = (svc.get("offers") or {}).get("price")
        if price is None or not str(price).replace(".", "", 1).isdigit():
            fail(f"{slug}/services.json: precio no numérico en '{ident}': {price!r}")
        if org_id and (svc.get("provider") or {}).get("@id") != org_id:
            fail(f"{slug}/services.json: '{ident}' apunta a otro provider")
        if not svc.get("display"):
            fail(f"{slug}/services.json: '{ident}' sin bloque display")

    for promo in load(folder / "promotions.json").get("itemListElement", []) if (folder / "promotions.json").exists() else []:
        if "validUntil" not in promo:
            fail(f"{slug}/promotions.json: '{promo.get('identifier')}' sin validUntil")
        if not promo.get("appliesTo"):
            fail(f"{slug}/promotions.json: '{promo.get('identifier')}' sin appliesTo")

    return {"slug": slug, "org": org, "services": len(services), "people": len(people)}


def main() -> int:
    index = load(ROOT / "index.json")
    declared = {t.get("identifier") for t in index.get("dataset", [])}
    on_disk = {p.name for p in THINGS.iterdir() if p.is_dir()} if THINGS.exists() else set()

    for missing in sorted(on_disk - declared):
        fail(f"index.json: falta la entidad '{missing}'")
    for ghost in sorted(declared - on_disk):
        fail(f"index.json: declara '{ghost}' pero no existe el directorio")

    # Clasificación schema.org: cada entidad declara su tipo.
    KINDS = {"Organization", "Person", "Project", "Corporation", "NGO", "LocalBusiness"}
    for entry in index.get("dataset", []):
        kind = entry.get("kind")
        if kind not in KINDS:
            fail(f"index.json: '{entry.get('identifier')}' tiene kind '{kind}' "
                 f"que no es un subtipo de schema.org/Thing conocido")
        about = entry.get("about") or {}
        if about.get("@type") != kind:
            fail(f"index.json: '{entry.get('identifier')}' discrepa entre kind y about.@type")
        if not about.get("@id"):
            fail(f"index.json: '{entry.get('identifier')}' sin about.@id")

    summary = [check_thing(slug, THINGS / slug) for slug in sorted(on_disk & declared)]

    if errors:
        print(f"✗ {len(errors)} problema(s):")
        for err in errors:
            print(f"   - {err}")
        return 1
    total = sum(s["services"] for s in summary)
    print(f"✓ catálogo válido: {len(summary)} entidad(es), {total} servicios")
    for s in summary:
        print(f"    {s['slug']:12} {s['org'].get('name','?'):20} {s['services']} servicios, {s['people']} personas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
