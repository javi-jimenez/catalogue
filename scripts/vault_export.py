#!/usr/bin/env python3
"""Exporta el catálogo como un vault de Obsidian consultable.

Por qué existe
--------------
Ni Dataview ni Bases pueden leer JSON: ambas consultan propiedades de notas
Markdown. Así que el JSON sigue siendo la fuente de verdad y este script
genera un ESPEJO: una nota por entidad con su frontmatter, más un `.base`.

    JSON (fuente)  ──►  scripts/vault_export.py  ──►  vault/*.md (vista)

Reglas
------
- El vault es de solo lectura: si editas una nota, se pierde al regenerar.
  Se edita el JSON y se vuelve a exportar.
- Cada nota lleva `id`, que es el identificador estable del catálogo, para
  poder enlazar entre notas con [[wikilinks]] sin depender del nombre.

Uso:
    python3 scripts/vault_export.py            # escribe vault/
    python3 scripts/vault_export.py --check    # exit 1 si el vault está desfasado
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOGUE = ROOT.parent
VAULT = CATALOGUE / "vault"


def load(name: str) -> dict:
    return json.loads((CATALOGUE / name).read_text(encoding="utf-8"))


def q(value: object) -> str:
    """Escapa un escalar para YAML entre comillas dobles."""
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def note(front: dict, title: str, body: str = "") -> str:
    lines = ["---"]
    for key, value in front.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {q(v)}" for v in value)
        else:
            lines.append(f"{key}: {q(value)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    if body:
        lines.append("")
        lines.append(body.rstrip())
    return "\n".join(lines) + "\n"


def build() -> dict[Path, str]:
    files: dict[Path, str] = {}
    org = load("organization.json")
    people = load("people.json")["itemListElement"]
    services = load("services.json")["itemListElement"]
    promos = load("promotions.json")["itemListElement"]
    sites = load("sites.json")["itemListElement"]
    org_id = org["@id"]

    # --- organización ---
    address = org.get("address", {})
    files[VAULT / "Organization" / "BRISECOM.md"] = note(
        {
            "id": org["@id"],
            "type": "organization",
            "name": org["name"],
            "legal_name": org.get("legalName"),
            "vat": org.get("vatID"),
            "email": org.get("email"),
            "url": org.get("url"),
            "city": address.get("addressLocality"),
            "country": address.get("addressCountry"),
            "address": address.get("streetAddress"),
            "postal_code": address.get("postalCode"),
        },
        org["name"],
        "Datos de la organización. Editar en `organization.json`.",
    )

    # --- personas ---
    for person in people:
        ident = person.get("identifier") or {}
        files[VAULT / "People" / f"{person['name']}.md"] = note(
            {
                "id": person["@id"],
                "type": "person",
                "name": person["name"],
                "job_title": person.get("jobTitle"),
                "organization": org_id,
                "orcid": ident.get("value"),
                "orcid_url": ident.get("url"),
                "links": person.get("sameAs", []),
            },
            person["name"],
            person.get("description", ""),
        )

    # --- servicios ---
    for svc in services:
        offer = svc.get("offers") or {}
        display = svc.get("display") or {}
        files[VAULT / "Services" / f"{svc['identifier']}.md"] = note(
            {
                "id": svc["identifier"],
                "type": "service",
                "name": svc["name"],
                "category": svc.get("category"),
                "group": svc.get("group"),
                "order": svc.get("order"),
                "price": float(offer.get("price", 0)),
                "currency": offer.get("priceCurrency", "EUR"),
                "price_unit": display.get("priceLabel"),
                "duration_hours": int((svc.get("estimatedDuration") or "PT0H")[2:-1]),
                "duration_label": display.get("durationLabel"),
                "provider": svc.get("provider", {}).get("@id"),
                "deliverables": svc.get("deliverables", []) or None,
            },
            svc["name"],
            svc.get("description", ""),
        )

    # --- promociones ---
    for promo in promos:
        offer = promo.get("offers") or {}
        files[VAULT / "Promotions" / f"{promo['identifier']}.md"] = note(
            {
                "id": promo["identifier"],
                "type": "promotion",
                "name": promo["name"],
                "category": promo.get("category"),
                "price": float(offer["price"]) if offer.get("price") is not None else None,
                "currency": offer.get("priceCurrency"),
                "valid_until": promo.get("validUntil"),
                "applies_to": promo.get("appliesTo"),
            },
            promo["name"],
            promo.get("description", ""),
        )

    # --- sitios ---
    for site in sites:
        files[VAULT / "Sites" / f"{site['name']}.md"] = note(
            {
                "id": site["url"],
                "type": "site",
                "name": site["name"],
                "url": site["url"],
                "purpose": site.get("purpose"),
                "tech": site.get("tech"),
                "repository": site.get("codeRepository"),
                "public": site.get("public", True),
            },
            site["name"],
            site.get("purpose", ""),
        )

    files[VAULT / "Services.base"] = BASE_FILE
    files[VAULT / "Catalogue.md"] = INDEX_NOTE
    return files


BASE_FILE = """\
# Bases: vista de servicios. Abrir en Obsidian 1.9+ (plugin core "Bases").
filters:
  and:
    - 'type == "service"'
properties:
  note.name:
    displayName: Service
  note.price:
    displayName: Price
  note.currency:
    displayName: Currency
views:
  - type: table
    name: "Catalogue by price"
    order:
      - note.order
      - note.name
      - note.group
      - note.price
      - note.duration_hours
    sort:
      - property: note.order
        direction: ASC
"""

INDEX_NOTE = """\
---
type: index
---
# BRISECOM catalogue

Vault **generado** desde el repo de metadatos. No editar aquí: se edita el JSON
y se regenera con `python3 scripts/vault_export.py`.

- Con **Bases** (core, Obsidian 1.9+): abre `Services.base`.
- Con **Dataview** (plugin) o DataviewJS, las notas de `Services/` exponen
  `price`, `group`, `duration_hours` como campos consultables.

```dataview
TABLE price, currency, duration_hours
FROM "Services"
WHERE type = "service"
SORT order ASC
```
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Exporta el catálogo como vault de Obsidian.")
    ap.add_argument("--check", action="store_true", help="no escribe; exit 1 si difiere")
    args = ap.parse_args()

    files = build()
    stale: list[str] = []
    for path, content in files.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        stale.append(str(path.relative_to(CATALOGUE)))
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if args.check:
        if stale:
            print(f"✗ vault desactualizado ({len(stale)} ficheros). Ejecuta: make vault")
            return 1
        print(f"✓ vault al día ({len(files)} ficheros)")
        return 0

    if stale:
        print(f"✓ vault generado: {len(files)} ficheros ({len(stale)} escritos)")
    else:
        print(f"✓ vault ya al día ({len(files)} ficheros)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
