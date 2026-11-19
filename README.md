# brisecom-catalogue

Metadata of BRISECOM SL as JSON. **A database without a server:** git is the
storage, a URL is the query, and every site renders it its own way —
`brisecom.org` as a sales page, `laia.brisecom.org` as a short reference.

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
