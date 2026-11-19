# Páginas como consultas, no como copias

La regla que faltaba. Los datos ya están centralizados; lo que no lo estaba es
la **página**: se escribió a mano con los datos dentro. Eso es una vista que
puede contradecir su propia fuente.

## La regla

> Una página no contiene hechos. Los pide.

- **Prosa** = lo que solo existe como texto: el argumento, el matiz, la
  explicación. Se escribe a mano, no se genera.
- **Hecho** = nombre, precio, duración, fecha, identificador, URL. Vive en un
  dataset y la página lo lee.

Si un hecho aparece dos veces, una de las dos es una copia que envejecerá. La
prueba no es opinable: se cambia el valor en el dataset, se recompila, y se
busca el valor viejo en el HTML. Si aparece, había una copia.

## Equivalencia con una base de datos

| Base de datos | Aquí |
|:--|:--|
| Tabla | `things/<slug>/<dataset>.json` |
| Fila | un elemento de `itemListElement` |
| Clave primaria | `identifier` o `@id` |
| Clave foránea | `provider.@id`, `about.@id` |
| JOIN | el cliente cruza `services` con `people` por `@id` |
| Vista / consulta | un shortcode de Hugo sobre `site.Data.<dataset>` |
| Migración | un cambio en el JSON, versionado en git |

La diferencia con MySQL: no hay servidor que se caiga, la consulta es un `GET`
y el `EXPLAIN` es un `git diff`.

## Qué hay hoy (2026-11-19)

| Dataset | Plantillas que lo leen | Estado |
|:--|:--|:--|
| `services.json` (catálogo) | 1 | ✅ página de servicios reconstruida |
| `entity.json` | 0 | ⚠️ traído pero no usado |
| `people.json` | 0 | ⚠️ ídem (la sección de equipo usa `equipo.yml`) |
| `promotions.json` | 0 | ⚠️ ídem (`servicios.yml` tiene sus propias promos) |
| `sites.json` | 0 | ⚠️ ídem |
| `servicios.yml` (viejo) | 3 | ❌ duplica precios; no coincide |
| `carta.yml` | 1 | ⚠️ lista de precios propia |
| `products.yml` | 1 | ⚠️ productos de Stripe, legítimamente aparte |

Divergencia real entre `servicios.yml` y el catálogo, hoy:

```
solo en servicios.yml: 180, 600, 1500, 2900
solo en el catálogo  : 240
```

Un precio de 240 € que la tabla muestra y el YAML desconoce; y cuatro cifras en
el YAML que la página de servicios no muestra. Mientras existan las dos, no hay
una sola verdad.

## Rediseño, por orden

1. **`entity.json` y `people.json` a las páginas que ya existen.** Sustituir
   `data/equipo.yml` por `people.json` en `layouts/shortcodes/equipo.html`.
   Son los mismos datos con la misma forma; el catálogo además lleva ORCID.
2. **`promotions.json` a `layouts/partials/promo.html`.** Hoy lee
   `servicios.promociones`, que es otra copia. Tiene `validUntil`, que es
   justo lo que la promo necesita para caducar sola.
3. **Retirar `servicios.yml`.** Una vez 1 y 2 estén hechos, no le queda nada
   propio. Borrarlo cierra la última fuente de precios paralela.
4. **`carta.yml` → catálogo.** La carta à la carte es otro conjunto de precios
   del mismo negocio: debe ser un dataset del catálogo, no un YAML del sitio.
   Así `brisecom-catalogue` contiene *todos* los precios de BRISECOM.
5. **`products.yml` se queda.** Los productos de Stripe tienen `purchase_url` y
   límites de contrato: son una oferta distinta, no una vista de los servicios.
   Pero su precio tampoco debería repetirse: la página puede leer el importe
   del catálogo y dejar aquí solo la URL de compra.

## La abstracción que falta

Hoy cada tabla tiene su shortcode a medida (`catalogue-table`). El paso
siguiente no es un lenguaje de consultas, es un patrón repetible:

```go-html-template
{{< data-table from="services" filter="group=core" >}}
```

Con dos o tres variantes (tabla, lista, ficha) se cubren todas las páginas
reales. Un motor genérico sería más elegante y peor: el template deja de
leerse de un vistazo, que es la única razón por la que alguien lo edita.

## Cómo se comprueba

```bash
python3 - <<'PY'
import json, pathlib, subprocess
p = pathlib.Path("data/services.json"); orig = p.read_text()
d = json.loads(orig)
d["itemListElement"][1]["display"]["priceLabel"] = "999 €"
p.write_text(json.dumps(d, ensure_ascii=False, indent=2))
subprocess.run(["./.bin/hugo", "--quiet", "--destination", "/tmp/t"], check=False)
h = pathlib.Path("/tmp/t/services/index.html").read_text()
print("la página siguió al dato:", "999 €" in h)
print("no queda copia:", "240 €" not in h)
p.write_text(orig)
PY
```
