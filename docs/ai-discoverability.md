# Ser citado, no ser la respuesta

Objetivo: que un motor generativo (ChatGPT, Claude, Perplexity, Gemini, Copilot)
**detecte y cite** estas páginas como fuente, en lugar de absorber el contenido
y responder sin referenciarlas.

La distinción importa: no se trata de aparecer en el texto que el modelo genera,
sino de ser el enlace que el usuario puede abrir y comprobar. Eso se consigue
con datos verificables, URLs estables y fechas; no con trucos de posicionamiento.

## Qué hay ya

| Pieza | brisecom.org | laia.brisecom.org | catalogue |
|:--|:--|:--|:--|
| `robots.txt` (Allow: /) | ✅ | ✅ | ✅ |
| `sitemap.xml` | ✅ | ✅ | ✅ |
| `llms.txt` | ✅ | ✅ | ✅ |
| JSON-LD (`schema.org`) | ✅ `Product`/`Offer` | ✅ `ScholarlyArticle` | ✅ `DataCatalog` |
| Página indexable por artículo | — | ✅ 24 páginas | — |
| `citation_*` (Highwire) | — | ✅ | — |
| JSON plano consultable | ❌ (no copia) | ❌ | ✅ |
| Fecha visible | parcial | ✅ | ✅ |

Ninguno de los tres bloquee crawlers de IA: `User-agent: * / Allow: /` los
admite, incluidos `GPTBot`, `ClaudeBot`, `PerplexityBot` y `Google-Extended`.

## Hecho

1. **`llms.txt` en las tres webs.** Apunta al JSON canónico en vez de copiar
   datos. No es un estándar aprobado, pero Lighthouse lo audita y OpenAI,
   Anthropic y Google lo publican para su propia documentación.
2. **Una página indexable por whitepaper**, con el abstract completo visible en
   el cuerpo (nunca oculto), URL estable y fecha. Google Scholar exige una URL
   por artículo; la portada con 24 tarjetas no servía.
3. **`citation_*` (Highwire) y JSON-LD `ScholarlyArticle`** con `identifier` =
   DOI, `author` con ORCID y `datePublished`. Los 24 DOIs ya están asociados a
   una página que Scholar puede leer.
4. **Fechas visibles** en la página de cada paper y en la tabla del catálogo.

## Qué falta

1. **Verificar la indexación en Google Scholar.** No hay API de envío: se
   comprueba buscando el título. Tarda semanas. Requisitos que ya cumple: PDF
   con texto buscable, abstract completo accesible, una URL por artículo.
2. **Versión Markdown de las páginas** (`page.md` junto a `page.html`, como
   recomienda `llms.txt` v2). El `.md` ya existe en el repo; falta servirlo con
   el mismo nombre y una cabecera de licencia.
3. **Someter el catálogo a los agregadores** una vez publicado el primer lote
   de DOIs: OpenAIRE ya lo recogió por vía de Zenodo.

## Qué no hacer

- Texto oculto o `display:none` con datos para el modelo: es cloaking, Google
  lo penaliza y rompe justo la confianza que se busca.
- `llms.txt` con precios duplicados: si no coincide con el JSON canónico, el
  consumidor tiene dos verdades. Debe **apuntar**, no copiar.

## Criterio de éxito

No es "que la IA hable de nosotros". Es que una consulta del tipo *"cuánto
cuesta una auditoría de negocio en BRISECOM"* devuelva el enlace a
`brisecom.org/services` con el precio correcto y la fecha, para que el usuario
lo verifique. Medible: revisar a mano, una vez al mes, qué citan los motores
principales para las consultas del catálogo.
