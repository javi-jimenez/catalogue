#!/usr/bin/env python3
"""Valida el catálogo: JSON válido, referencias cruzadas y campos obligatorios.

Uso:
    python3 validate.py

Sale con código 1 si algo no cuadra. Pensado para ejecutarse en CI y antes de
publicar: un precio mal escrito aquí llega a todas las webs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = ["@context", "@type"]
EXPECTED = {
    "organization.json", "people.json", "services.json", "promotions.json",
    "sites.json", "index.json",
}
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load(name: str) -> dict:
    path = ROOT / name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{name}: JSON inválido — {exc}")
        return {}
    for key in REQUIRED:
        if key not in data:
            fail(f"{name}: falta '{key}'")
    if data.get("@context") != "https://schema.org":
        fail(f"{name}: @context debe ser https://schema.org")
    return data


def main() -> int:
    on_disk = {p.name for p in ROOT.glob("*.json")}
    for missing in sorted(EXPECTED - on_disk):
        fail(f"falta {missing}")
    for extra in sorted(on_disk - EXPECTED):
        if extra != "index.json":
            fail(f"{extra} no está en el manifiesto ni en la lista esperada")

    data = {name: load(name) for name in sorted(EXPECTED & on_disk)}

    # Los datos de organización son la raíz de las referencias cruzadas.
    org = data.get("organization.json", {})
    if org.get("vatID") != "ESB23980998":
        fail("organization.json: VAT inesperado")
    org_id = org.get("@id")

    # El fundador y los empleados deben existir en people.json.
    people = data.get("people.json", {}).get("itemListElement", [])
    person_ids = {p.get("@id") for p in people}
    founder = (org.get("founder") or {}).get("@id")
    if founder and founder not in person_ids:
        fail(f"organization.json: founder {founder} no está en people.json")
    for emp in org.get("employee") or []:
        if emp.get("@id") not in person_ids:
            fail(f"organization.json: employee {emp.get('@id')} no está en people.json")

    # Cada persona debe llevar su ORCID, que es la razón de ser de este fichero.
    for person in people:
        ident = person.get("identifier") or {}
        if ident.get("propertyID") != "ORCID":
            fail(f"people.json: {person.get('name')} sin ORCID")
        elif not str(ident.get("value", "")).startswith("0009-"):
            fail(f"people.json: ORCID sospechoso en {person.get('name')}")

    # Servicios: identificadores únicos, precios numéricos y proveedor válido.
    services = data.get("services.json", {}).get("itemListElement", [])
    seen: set[str] = set()
    for svc in services:
        ident = svc.get("identifier")
        if not ident:
            fail("services.json: servicio sin identifier")
        elif ident in seen:
            fail(f"services.json: identifier duplicado '{ident}'")
        seen.add(ident)
        price = (svc.get("offers") or {}).get("price")
        if price is None or not str(price).replace(".", "", 1).isdigit():
            fail(f"services.json: precio no numérico en '{ident}': {price!r}")
        provider = (svc.get("provider") or {}).get("@id")
        if org_id and provider != org_id:
            fail(f"services.json: '{ident}' apunta a un provider desconocido")
        if not svc.get("display"):
            fail(f"services.json: '{ident}' sin bloque display")

    # Promociones: una oferta caducada es peor que ninguna.
    for promo in data.get("promotions.json", {}).get("itemListElement", []):
        if "validUntil" not in promo:
            fail(f"promotions.json: '{promo.get('identifier')}' sin validUntil (puede ser null)")
        if not promo.get("appliesTo"):
            fail(f"promotions.json: '{promo.get('identifier')}' sin appliesTo")

    # Manifiesto: cada distribución debe existir en disco.
    for dist in data.get("index.json", {}).get("distribution", []):
        name = dist.get("contentUrl")
        if name not in on_disk:
            fail(f"index.json: distribution '{name}' no existe")

    if errors:
        print(f"✗ {len(errors)} problema(s):")
        for err in errors:
            print(f"   - {err}")
        return 1
    print(f"✓ catálogo válido: {len(on_disk)} ficheros, {len(services)} servicios, "
          f"{len(people)} personas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
