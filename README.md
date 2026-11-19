# catalogue

Metadata as JSON. **A database without a server:** git is the storage, a URL is
the query, and every site renders it its own way.

Who the catalogue describes is data, not the name of the repo: `index.json`
carries a `subject` pointing at the entity it publishes. Today that is BRISECOM
SL; change the field and the same catalogue describes another entity.

Nothing here is a page or a design. It is data.

## Why

Each site used to keep its own copy of prices, names and contact details, and
they drifted. Now the facts live once, here. A site that hardcodes a price is
wrong by construction.

It is also already typed: every file carries `@context`/`@type` from
[schema.org](https://schema.org), so a site can use it as structured data
without inventing a mapping.

## Datasets

| File | What it holds | schema.org |
|:--|:--|:--|
| [`organization.json`](organization.json) | Legal identity, VAT, address, contact, founder | `Organization` |
| [`people.json`](people.json) | People with their ORCID and public profiles | `Person` |
| [`services.json`](services.json) | The service catalogue with prices | `OfferCatalog` → `Service` → `Offer` |
| [`promotions.json`](promotions.json) | Time-bound offers, each with `validUntil` | `PromotionalOffer` |
| [`sites.json`](sites.json) | Registry of the sites BRISECOM operates | `WebSite` |
| [`index.json`](index.json) | Manifest: what exists and where | `Dataset` |

## How it is consumed

```
  this repo  ──►  brisecom.org/data/*.json  ──►  consumers
  (source)        (synced on build)             (fetched at build, vendored)
```

Published under <https://brisecom.org/data/>, so any site — or a local dev
server — can fetch it over plain HTTP. Consumers keep a vendored copy so a
build never depends on the network being up.

## Rules

- **Identifiers are stable.** Consumers key on `identifier` / `@id`, never on a
  display name. Renaming a service must not break a consumer.
- **Prices live here only.** `offers[].price` is a string; the currency is in
  `priceCurrency`.
- **`version` and `dateModified`** change with any content change, so a
  consumer can detect staleness.
- **Promotions expire.** Every entry declares `validUntil` (`null` means
  evergreen). An expired offer is worse than no offer.
- **Unverified data is left out** rather than guessed. A missing field is a
  question; an invented one is a bug.
- **Breaking changes** (removing a field a consumer reads) bump the major
  version.

## Validate

```bash
python3 validate.py
```

Checks JSON validity, that every cross-reference resolves (the founder exists in
`people.json`, every service points at the same organisation), that prices are
numeric, that identifiers are unique, and that the manifest matches the files on
disk. A price typo here would reach every site, so this runs in CI.

## Obsidian

`vault/` is a **generated mirror**: one Markdown note per entity, with the JSON
fields as YAML frontmatter, plus a `.base` file.

Why a mirror and not the JSON directly: neither Dataview nor Bases can read a
JSON file. Dataview indexes frontmatter and inline fields; Bases queries
properties of notes. YAML frontmatter on Markdown is the de facto standard both
of them, Hugo and this repo already speak. So the JSON stays the source and the
notes are a view of it.

```bash
make vault          # regenerate vault/
make check          # validate + fail if the vault is stale
```

The vault is **read-only**: edit the JSON and regenerate. Each note carries
`id`, the stable catalogue identifier, so links survive a rename.

| In Obsidian | Needs | What it gives you |
|:--|:--|:--|
| `vault/Services.base` | Obsidian 1.9+, core "Bases" | Sortable table of the catalogue, no plugin |
| `vault/Catalogue.md` | Dataview plugin | The same via `TABLE price, duration_hours` |
| Everything | nothing | Plain notes with frontmatter, greppable and linkable |

To use it, open this repository as a vault in Obsidian (`Open folder as vault` →
`vault/`), or symlink `vault/` into an existing vault.

## Public metadata endpoint

The repo also publishes itself as a static site (GitHub Pages), so anything —
a web app, a script, an AI agent — can query the facts over plain HTTP:

| URL | What |
|:--|:--|
| `/index.json` | Manifest: datasets and their URLs |
| `/data/services.json` | ``OfferCatalog`` with prices |
| `/data/services/<id>.json` | One `Service`, one URL — no need to walk the list |
| `/data/people.json` | `Person` with ORCID |
| `/data/organization.json` | `Organization` with VAT |
| `/data/promotions.json` | Offers, each with `validUntil` |
| `/data/sites.json` | Sites operated |
| `/llms.txt` | Plain summary for AI agents |
| `/sitemap.xml`, `/robots.txt` | Crawler entry points |
| `/.well-known/catalogue.json` | Machine discovery |

```bash
make site      # regenerate docs/ from the JSON
make lint      # verify every published JSON declares schema.org and a @type
```

`docs/` is generated; edit the JSON and regenerate. `make check` runs the
validator, the JSON-LD linter and verifies the vault and the site are current,
so CI fails on drift rather than publishing stale metadata.

### Where it is served

Two endpoints, same content:

| Endpoint | Status |
|:--|:--|
| `https://brisecom.org/data/` | Live, deployed with the BRISECOM site |
| GitHub Pages (`docs/`) | Built and validated; see the note below |

Change the host with `--base-url` or `CATALOGUE_BASE_URL`:

```bash
python3 scripts/build_site.py --base-url https://brisecom.org
```
