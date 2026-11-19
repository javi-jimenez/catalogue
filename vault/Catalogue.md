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
FROM "Brisecom/Services"
WHERE type = "service"
SORT order ASC
```
