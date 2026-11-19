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
DATASETS = ["entity", "people", "services", "promotions", "sites"]
KINDS = {"Organization", "Person", "Project", "Corporation", "NGO", "LocalBusiness"}

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
    manifest = load(folder / "index.json") if (folder / "index.json").exists() else {}
    listed = [
        str(d.get("url", "")).rsplit("/", 1)[-1]
        for d in manifest.get("dataset", [])
    ]

    # Cada entidad declara sus propios datasets: una persona no tiene
    # servicios ni promociones, y no por ello está incompleta.
    for name in listed:
        if not (folder / name).exists():
            fail(f"{slug}: index.json declara {name} pero no existe")
    if "entity.json" not in listed:
        fail(f"{slug}/index.json: no declara entity.json en dataset[]")

    kind = manifest.get("kind")
    if kind not in KINDS:
        fail(f"{slug}/index.json: kind '{kind}' no es un Thing de schema.org")
    about = manifest.get("about") or {}
    if about.get("@type") != kind:
        fail(f"{slug}/index.json: discrepa entre kind y about.@type")
    if not about.get("@id"):
        fail(f"{slug}/index.json: sin about.@id")

    org = load(folder / "entity.json") if (folder / "entity.json").exists() else {}
    org_id = org.get("@id")
    kind = org.get("@type")
    if kind not in KINDS:
        fail(f"{slug}: entity.json tiene @type '{kind}', no es un Thing conocido")
    if  kind == "Organization" and not org.get("vatID"):
        fail(f"{slug}: entity.json es Organization y no declara vatID")

    people = (
        load(folder / "people.json").get("itemListElement", [])
        if "people.json" in listed
        else []
    )
    person_ids = {p.get("@id") for p in people}
    founder = (org.get("founder") or {}).get("@id")
    if founder and founder not in person_ids:
        fail(f"{slug}: founder {founder} no está en people.json")
    for emp in org.get("employee") or []:
        if people and emp.get("@id") not in person_ids:
            fail(f"{slug}: employee {emp.get('@id')} no está en people.json")

    for person in people:
        ident = person.get("identifier") or {}
        if ident.get("propertyID") == "ORCID" and len(str(ident.get("value", ""))) != 19:
            fail(f"{slug}: ORCID raro en {person.get('name')}")

    services = (
        load(folder / "services.json").get("itemListElement", [])
        if "services.json" in listed
        else []
    )
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

    promotions = (
        load(folder / "promotions.json").get("itemListElement", [])
        if "promotions.json" in listed
        else []
    )
    for promo in promotions:
        if "validUntil" not in promo:
            fail(f"{slug}/promotions.json: '{promo.get('identifier')}' sin validUntil")
        if not promo.get("appliesTo"):
            fail(f"{slug}/promotions.json: '{promo.get('identifier')}' sin appliesTo")

    return {"slug": slug, "org": org, "services": len(services), "people": len(people),
            "datasets": len(listed)}


def main() -> int:
    index = load(ROOT / "index.json")
    declared = {t.get("identifier") for t in index.get("dataset", [])}
    on_disk = {p.name for p in THINGS.iterdir() if p.is_dir()} if THINGS.exists() else set()

    for missing in sorted(on_disk - declared):
        fail(f"index.json: falta la entidad '{missing}'")
    for ghost in sorted(declared - on_disk):
        fail(f"index.json: declara '{ghost}' pero no existe el directorio")

    # La identidad del catálogo no puede ser la de la entidad que describe.
    catalogue_id = str(index.get("@id", ""))
    for entry in index.get("dataset", []):
        org_path = THINGS / entry.get("identifier", "") / "organization.json"
        if not org_path.exists():
            continue
        org = json.loads(org_path.read_text(encoding="utf-8"))
        org_id = str(org.get("@id", ""))
        host = org_id.split("/")[2] if "//" in org_id else ""
        if host and host in catalogue_id:
            fail(
                f"index.json: @id '{catalogue_id}' cuelga del dominio de "
                f"'{entry.get('identifier')}' ({host}); el catálogo es un "
                f"contenedor, no parte de la entidad"
            )

    # La raíz es solo un índice: ninguna entrada debe repetir datos de la
    # entidad (eso vive en things/<slug>/). Solo referencia.
    ALLOWED_ROOT_KEYS = {"@type", "identifier", "url"}
    for entry in index.get("dataset", []):
        extra = set(entry) - ALLOWED_ROOT_KEYS
        if extra:
            fail(
                f"index.json: '{entry.get('identifier')}' lleva {sorted(extra)}; "
                f"la raíz solo referencia, los datos van en things/<slug>/"
            )
        if not str(entry.get("url", "")).endswith("/index.json"):
            fail(f"index.json: '{entry.get('identifier')}' debe apuntar a su index.json")

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
