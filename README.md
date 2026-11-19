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

## Structure

A catalogue of **things** — a `Thing` in schema.org is the root type, so a
company, a person and a project all fit without inventing a taxonomy.

```
index.json                        DataCatalog → dataset[] (references only)
things/<slug>/index.json          DataCatalog → about: the thing, dataset[]: its files
things/<slug>/entity.json         Organization | Person | Project  (who it is)
things/<slug>/people.json         ItemList of Person
things/<slug>/services.json       OfferCatalog of Service with offers
things/<slug>/promotions.json     ItemList of PromotionalOffer
things/<slug>/sites.json          ItemList of WebSite
```

The root is **only schema**: it names the catalogue and points at each thing.
It carries no company name, no VAT, no prices. Everything a thing is lives in
its own directory, so the same catalogue can hold a company, a person and a
project without the root knowing anything about them.

Adding a company, a project or a person is adding a directory and one line in
`index.json`. Nothing else changes.

Each thing declares which datasets it has. A person has no services and no
promotions, and is not incomplete because of it:

```json
"dataset": [
  { "@type": "Dataset", "name": "entity", "url": "entity.json" },
  { "@type": "Dataset", "name": "sites",  "url": "sites.json" }
]
```

Each entry declares its schema.org classification, and the validator enforces
that `kind` and `about.@type` agree:

```json
{
  "@type": "DataCatalog",
  "name": "BRISECOM SL",
  "kind": "Organization",
  "about": { "@type": "Organization", "@id": "https://brisecom.org/#organization" }
}
```

The root entry for the same thing is three fields and nothing else:

```json
{ "@type": "DataCatalog", "identifier": "brisecom", "url": "things/brisecom/index.json" }
```

## Datasets per thing

| File | What it holds | schema.org |
|:--|:--|:--|
| `entity.json` | Who it is: legal identity and VAT, or ORCID and profiles | `Organization`, `Person` or `Project` |
| `people.json` | People with their ORCID and public profiles | `ItemList` → `Person` |
| `services.json` | The service catalogue with prices | `OfferCatalog` → `Service` → `Offer` |
| `promotions.json` | Time-bound offers, each with `validUntil` | `ItemList` → `PromotionalOffer` |
| `sites.json` | Registry of the sites the thing operates | `ItemList` → `WebSite` |

## How it is consumed

Everything comes from this repository. No site hosts a copy: the catalogue is
published once, from here, and every consumer reads it from the same place.

```
  this repo (source)  ──►  GitHub Pages (published)  ──►  consumers
```

The published endpoint is <https://javi-jimenez.github.io/catalogue/>. A site
that needs the data fetches it there; nothing is duplicated and nothing is
vendored from a second location.

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

## AI and search crawlers

The published site is built to be **cited, not paraphrased**: every fact is
plain JSON, typed with schema.org, at a stable URL, with a date.

- `robots.txt` allows every crawler, AI ones included.
- `sitemap.xml` lists every data URL.
- `llms.txt` explains how to query it, and points at the JSON instead of
  copying it.
- `/.well-known/catalogue.json` is a machine entry point.

What each site is still missing — and what not to do — is written down in
[`docs/ai-discoverability.md`](docs/ai-discoverability.md).

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

## Consumers

There is one catalogue and it lives here. Sites do not keep their own copy:
they fetch these JSONs at build time, from GitHub.

`brisecom.org` runs a sync before every Hugo build, so `make build` cannot
compile a page from stale data:

```make
build: catalogue
```

If the network is down the sync falls back to its last copy and warns; the
build never breaks over it.

## Public metadata endpoint

The repo also publishes itself as a static site (GitHub Pages), so anything —
a web app, a script, an AI agent — can query the facts over plain HTTP:

| URL | What |
|:--|:--|
| `/index.json` | `DataCatalog`: the things and their URLs |
| `/things/<slug>/index.json` | `DataCatalog` of one thing |
| `/things/<slug>/services.json` | `OfferCatalog` with prices |
| `/things/<slug>/services/<id>.json` | One `Service`, one URL — no need to walk the list |
| `/things/<slug>/people.json` | `Person` with ORCID |
| `/things/<slug>/entity.json` | The thing itself (`Organization`, `Person`…) |
| `/things/<slug>/promotions.json` | Offers, each with `validUntil` |
| `/things/<slug>/sites.json` | Sites operated |
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
| `https://javi-jimenez.github.io/catalogue/` | Live, generated from `docs/` |

The base URL is the only thing that changes if the catalogue ever moves:

```bash
python3 scripts/build_site.py --base-url https://example.org/catalogue
```
