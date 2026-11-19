# brisecom-catalogue

Metadata for the BRISECOM services, kept in one place. Every site renders it
its own way: `brisecom.org` as a sales page, `laia.brisecom.org` as a short
reference.

## What this is

`services.json` is the **single source of truth** for the service catalogue:
names, prices, durations and the schema.org types that describe them.

It is not a page and not a design. It is data.

- Machine-readable: one JSON document, versioned, no build step.
- Typed: it already carries `@context`/`@type` (schema.org `OfferCatalog`,
  `Service`, `Offer`, `PriceSpecification`), so a site can drop it into
  structured data without inventing a mapping.
- Language-neutral: strings are English, as on the site. Translations belong in
  the consumer, not here.

## How it is consumed

Published by `brisecom.org` at <https://brisecom.org/data/services.json>, so any
site (or a local dev server) can fetch it over plain HTTP. Consumers keep a
vendored copy so a build never depends on the network:

```
  services.json  ──►  brisecom.org /data/services.json  ──►  consumers
   (this repo)          (synced on deploy)                   (fetched at build)
```

## Rules

- Prices live here and only here. A consumer that hardcodes a price is wrong.
- `version` and `dateModified` change with any content change, so a consumer can
  detect staleness.
- Breaking changes (removing a field a consumer reads) bump the major version.

## Fields

| Field | Meaning |
|:--|:--|
| `entryPoint` | The free hour that opens every route |
| `itemListElement[].identifier` | Stable id; consumers key on it, never on the name |
| `itemListElement[].group` | `core` (the map) or `modules` (contracted separately) |
| `itemListElement[].offers[].price` | Amount as a string, currency in `priceCurrency` |
| `itemListElement[].deliverables` | The pieces a grouped service is sold in |
