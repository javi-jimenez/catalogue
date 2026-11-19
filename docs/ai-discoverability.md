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
| `llms.txt` | ❌ | ❌ | ✅ |
| JSON-LD (`schema.org`) | ✅ `Product`/`Offer` | ❌ | ✅ `DataCatalog` |
| JSON plano consultable | ❌ (se retiró la copia) | ❌ | ✅ |
| Fecha visible + actualización | parcial | ✅ | ✅ |

Ninguno de los tres bloquee crawlers de IA: `User-agent: * / Allow: /` los
admite, incluidos `GPTBot`, `ClaudeBot`, `PerplexityBot` y `Google-Extended`.

## Qué falta, por orden de impacto

1. **`llms.txt` en brisecom.org y laia.brisecom.org.** No es un estándar
   aprobado por ningún organismo, pero sí una convención con adopción real:
   Lighthouse lo audita en su comprobación de navegación agéntica, y OpenAI,
   Anthropic y Google lo publican para su propia documentación. Es barato y
   ayuda a que un agente no tenga que interpretar el HTML.

   Debe decir: qué es el sitio, cuáles son los datos canónicos, dónde viven
   (el catálogo en GitHub) y qué licencia tienen.

2. **Versión Markdown de las páginas que un agente querría citar.** La
   propuesta `llms.txt` v2 recomienda servir `page.md` junto a `page.html`.
   Hugo genera el HTML; publicar el `.md` de cada whitepaper ya se hace en el
   repo, así que es servirlo con el mismo nombre y una cabecera de licencia.

3. **Fechas y versión en el HTML visible**, no solo en el JSON-LD. Un modelo
   que cita sin fecha produce citas que envejecen mal; una fecha a la vista
   permite al usuario juzgar si el dato sigue vigente.

4. **`citation_*` (Highwire) en la web de LAIA.** Es lo que lee Google Scholar
   para indexar los whitepapers como publicaciones académicas, con su DOI. Sin
   esto, los DOIs existen pero Scholar no los asocia a la página.

5. **JSON-LD en laia.brisecom.org.** Es la única de las tres sin datos
   estructurados. `ScholarlyArticle` por whitepaper, con `identifier` = DOI,
   `author` con ORCID y `datePublished`.

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
