#!/usr/bin/env python3
"""Genera un sitio estático de metadatos (GitHub Pages) desde los JSON.

Salida en docs/, lista para servirse como GitHub Pages:

  docs/index.json           el manifiesto (lo que existe y dónde)
  docs/data/<dataset>.json  cada dataset agregado, con JSON-LD de contexto
  docs/index.html           portada legible por humanos y por crawlers
  docs/robots.txt           permite todo, apunta al sitemap
  docs/sitemap.xml          todas las URLs de datos
  docs/llms.txt             resumen para agentes de IA
  docs/.well-known/…        descubrimiento

Regla: el sitio es una VISTA de los JSON. No se edita a mano; se regenera.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
BASE_URL = "https://javi-jimenez.github.io/brisecom-catalogue"

DATASETS = {
    "organization": "Legal identity, VAT, address and founder",
    "people": "People with their ORCID and public profiles",
    "services": "Service catalogue with prices",
    "promotions": "Time-bound offers with validUntil",
    "sites": "Sites BRISECOM operates",
}


def load(name: str) -> dict:
    return json.loads((ROOT / f"{name}.json").read_text(encoding="utf-8"))


def build() -> dict[Path, str]:
    files: dict[Path, str] = {}
    manifest = load("index")

    # El manifiesto se publica tal cual, con URLs absolutas de datos.
    published_manifest = dict(manifest)
    published_manifest["distribution"] = [
        {**d, "contentUrl": f"{BASE_URL}/data/{d['contentUrl'].replace('.json','')}.json"}
        for d in manifest.get("distribution", [])
    ]
    files[OUT / "index.json"] = json.dumps(published_manifest, ensure_ascii=False, indent=2) + "\n"

    for name in DATASETS:
        data = load(name)
        files[OUT / "data" / f"{name}.json"] = (
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        )

    # Un fichero por servicio: una URL por hecho, que es lo que hace cómoda
    # una consulta desde una app o un agente (no hay que recorrer el catálogo).
    services = load("services")
    for svc in services.get("itemListElement", []):
        ident = svc["identifier"]
        single = {
            "@context": "https://schema.org",
            **{k: v for k, v in svc.items() if k != "@context"},
        }
        files[OUT / "data" / "services" / f"{ident}.json"] = (
            json.dumps(single, ensure_ascii=False, indent=2) + "\n"
        )

    modified = max(
        (str(load(n).get("dateModified", "")) for n in DATASETS), default=""
    ) or date.today().isoformat()

    files[OUT / "index.html"] = INDEX_HTML.replace("{base}", BASE_URL).replace("{modified}", modified)
    files[OUT / "robots.txt"] = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "# Machine-readable: every dataset is plain JSON with schema.org types.\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n"
    )
    files[OUT / "sitemap.xml"] = SITEMAP.format(
        base=BASE_URL,
        modified=modified,
        urls="".join(
            [f"  <url><loc>{BASE_URL}/data/{n}.json</loc>"
             f"<lastmod>{modified}</lastmod></url>\n" for n in DATASETS]
            + [f"  <url><loc>{BASE_URL}/data/services/{s['identifier']}.json</loc>"
               f"<lastmod>{modified}</lastmod></url>\n"
               for s in load("services").get("itemListElement", [])]
        ),
    )
    files[OUT / "llms.txt"] = LLMS.format(base=BASE_URL, modified=modified)
    files[OUT / ".well-known" / "catalogue.json"] = (
        json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "DataCatalog",
                "name": "BRISECOM catalogue",
                "catalogue": "BRISECOM",
                "manifest": f"{BASE_URL}/index.json",
                "format": "application/json",
                "schema": "https://schema.org",
                "datasets": list(DATASETS),
                "version": manifest.get("version"),
                "license": manifest.get("license"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    files[OUT / ".nojekyll"] = ""
    return files


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BRISECOM catalogue — metadata as JSON</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Metadata of BRISECOM SL as plain JSON with schema.org types: services and prices, promotions, people, organisation and sites. A database without a server.">
<link rel="canonical" href="{base}/">
<script type="application/ld+json">
{jsonld}
</script>
<style>
  :root { color-scheme: light dark; }
  body { font: 16px/1.6 system-ui, sans-serif; max-width: 46rem; margin: 4rem auto; padding: 0 1.25rem; }
  h1 { font-size: 1.6rem; margin-bottom: .25rem; }
  .sub { margin-top: 0; opacity: .7; }
  table { border-collapse: collapse; width: 100%; margin: 2rem 0; }
  th, td { text-align: left; padding: .5rem; border-bottom: 1px solid rgba(128,128,128,.3); }
  code { background: rgba(128,128,128,.15); padding: .1rem .3rem; border-radius: 4px; }
  .muted { opacity: .6; font-size: .9rem; }
</style>
</head>
<body>
<h1>BRISECOM catalogue</h1>
<p class="sub">Metadata as plain JSON. No server, no API key: a URL is the query.</p>

<p>Every dataset is typed with <a href="https://schema.org">schema.org</a>, so a
consumer does not have to invent a mapping. Fetch, parse, use.</p>

<table>
<thead><tr><th>Dataset</th><th>What it holds</th><th>URL</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>

<h2>Discovery</h2>
<ul>
  <li><a href="index.json">index.json</a> — manifest of datasets</li>
  <li><a href="sitemap.xml">sitemap.xml</a> — every data URL</li>
  <li><a href="llms.txt">llms.txt</a> — summary for AI agents</li>
  <li><code>.well-known/catalogue.json</code> — machine entry point</li>
</ul>

<p class="muted">Last modified {modified}. Text and data licensed
CC BY-NC-SA 4.0. Generated from
<a href="https://github.com/javi-jimenez/brisecom-catalogue">the catalogue repo</a>.</p>
</body>
</html>
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{base}/</loc><lastmod>{modified}</lastmod></url>
  <url><loc>{base}/index.json</loc><lastmod>{modified}</lastmod></url>
{urls}</urlset>
"""

LLMS = """# BRISECOM catalogue

> Metadata of BRISECOM SL as plain JSON, typed with schema.org.

Everything below is authoritative and machine-readable. Fetch the JSON, do not
scrape the HTML.

- Manifest: {base}/index.json
- Datasets: organization, people, services, promotions, sites
- Format: JSON, `@context: https://schema.org`
- License: CC BY-NC-SA 4.0
- Last modified: {modified}

## Services and prices
{base}/data/services.json — `OfferCatalog` of `Service` with `offers[].price`.

## People
{base}/data/people.json — `Person`, each with an ORCID identifier.

## Organisation
{base}/data/organization.json — `Organization`, VAT ESB23980998.

## Promotions
{base}/data/promotions.json — time-bound offers; honour `validUntil`.

## Sites
{base}/data/sites.json — `WebSite` entries BRISECOM operates.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Genera el sitio de metadatos en docs/.")
    ap.add_argument("--check", action="store_true", help="no escribe; exit 1 si difiere")
    args = ap.parse_args()

    files = build()

    # JSON-LD de la portada: describe el catálogo entero.
    manifest = load("index")
    modified = max(
        (str(load(n).get("dateModified", "")) for n in DATASETS), default=""
    ) or date.today().isoformat()
    jsonld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "DataCatalog",
            "name": manifest["name"],
            "description": manifest["description"],
            "url": f"{BASE_URL}/",
            "license": manifest.get("license"),
            "dataset": [
                {
                    "@type": "Dataset",
                    "name": name,
                    "description": desc,
                    "url": f"{BASE_URL}/data/{name}.json",
                    "encodingFormat": "application/json",
                }
                for name, desc in DATASETS.items()
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
    rows = "\n".join(
        f'<tr><td><code>{n}</code></td><td>{escape(d)}</td>'
        f'<td><a href="data/{n}.json">data/{n}.json</a></td></tr>'
        for n, d in DATASETS.items()
    )
    html_path = next(k for k in files if k.name == "index.html")
    files[html_path] = (
        files[html_path]
        .replace("{jsonld}", jsonld)
        .replace("{rows}", rows)
        .replace("{base}", BASE_URL)
        .replace("{modified}", modified)
    )

    stale = []
    for path, content in files.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            continue
        stale.append(str(path.relative_to(ROOT)))
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if args.check:
        if stale:
            print(f"✗ sitio desactualizado ({len(stale)} ficheros). Ejecuta: make site")
            return 1
        print(f"✓ sitio al día ({len(files)} ficheros)")
        return 0
    print(f"✓ sitio generado: {len(files)} ficheros" + (f" ({len(stale)} escritos)" if stale else " (sin cambios)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
