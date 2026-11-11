# GeoLogistix — Auditoría del proyecto e informe de fuentes de internet para ingesta de datos

> **Fecha:** 2026-11-10  
> **Alcance auditado:** `GeoLogistix/` (workspace local) — foco activo `costo-entregado-mvp/` + paquetes de especificación `geo-abastecimiento-ar/` (v0.2) y `geologistix_foundation/` (v0.1, referencia).  
> **Objetivo:** estado honesto del proyecto y mapa de **fuentes en internet** útiles para ingestar datos al comparador de costo entregado, con criterios de procedencia, calidad, licencias y viabilidad.  
> **Marco:** P1 (veracidad/procedencia), P7 (seguridad/PII, sin secretos), P8 (módulo autónomo, sin fusión). No inventar datos ni afirmar impacto/licencias sin evidencia.

---

## 1. Resumen ejecutivo (auditoría)

| Aspecto | Estado verificado |
|---|---|
| **Producto (foco)** | Una sola cosa: **comparador de costo entregado** (material + flete + ajustes, FX fechado, procedencia). Decisión humana; no certifica idoneidad técnica/legal/ambiental. |
| **Implementación** | **MVP liviano operativo** en `costo-entregado-mvp/`: `compare.py` (Python stdlib, `contract_version: delivered-cost/0.1`), entrada JSON, salida tabla/JSON/CSV, ranking, alertas `NO COMPARABLE`/`incompleto`, sin asumir 0 en faltantes. Ejemplo y caso anclado en FX real (BNA 2026-11-05) ejecutados. |
| **Artefactos de captura** | `input_template_real.json`, `CHECKLIST_CAPTURA_DATOS.md`, `casos/caso_real_plantilla.json`, `casos/caso_real_fx_bna_2026-11-05_cemento_ref.json`. |
| **Especificación** | v0.2 (amplia, P0 abiertos: piloto/área/material, datos comerciales, FX/reglas fiscales-flete, derechos reutilización, RAG no seleccionado) y v0.1 histórica. **No implementadas** como plataforma. |
| **Validación/CI** | Sin suite de tests ni CI en el MVP (script determinista simple). Specs exigen tests/fixtures offline para evoluciones (INGEST-006, quality gates). |
| **Datos** | **Sin ingesta automatizada.** Caso demo/estimado disponible; caso con **FX observado (BNA)** disponible; **cotizaciones formales y flete reales: pendientes** (requieren captura directa/RFQ). |
| **Repo/gobernanza** | Carpeta sin repo git propio (cambios locales). Módulo autónomo, acoplable por contrato L0/L1 (p. ej. a Poolar). Packs incluyen `AGENTS.md`, gobernanza de datos/reuse. |

**Conclusión:** el motor de comparación es útil y honesto, pero **no tiene pipeline de ingesta ni fuentes conectadas**. El cuello de botella para “datos reales” son **cotizaciones y flete** (principalmente `observado` por contacto directo) y una **regla de FX** consistente; internet aporta bien FX/oficiales y contexto/indicadores, y solo **referencias indicativas** de precios (no sustituye cotización).

---

## 2. Requisitos de datos (lo que el MVP necesita ingerir)

| Dato | Campos clave (MVP) | Procedencia objetivo | Prioridad | Notas |
|---|---|---|---|---|
| **Tipo de cambio ARS/USD** | `pair, rate, date, source, status, url_or_ref` | `observado` (fuente oficial/publicada) o `estimado` (regla acordada) | **Alta** | Definir regla única (billete/divisa, compra/venta, fuente) por caso (OD-004). Fechar siempre. |
| **Precio material (cotización)** | proveedor, material/spec, cantidad/unidad, `unit_price`, `currency`, fecha/vigencia, incluye IVA/impuestos, `source/status` | `observado` (presupuesto formal) | **Alta** | Principal gap. Debe ser comparable (misma spec/unidad/condiciones). |
| **Flete / entrega** | `freight_cost`, `freight_currency`, términos (puesto en obra/retiro), origen-destino, fecha | `observado` (cotización transporte o condición proveedor) | **Alta** | Sin flete informado → **no comparable** como entregado (regla del MVP). |
| **Otros costos/ajustes** | descarga, seguro, pallets, recargos | `observado`/`estimado` declarado | Media | Solo si aplican y están explícitos. |
| **Metadatos de evidencia** | fuente, evidencia/ref, vigencia, inclusiones/exclusiones | trazable | **Alta** | Soporta auditoría y no-repudio de supuestos. |
| **(Futuro, fuera MVP)** rutas/distancias, catálogos normalizados, elegibilidad/circularidad | — | — | Baja | Requiere OD-006/OD-007 y fuentes con licencia/términos claros. |

**Reglas de ingesta (del modelo de gobernanza/spec):** distinguir `observed/derived/estimated/synthetic/test/unavailable/stale/rejected`; no convertir faltantes en 0; conservar moneda/valor original y snapshot FX; registrar `source`, `retrieved_at/observed_at`, vigencia y límites; respetar licencias/términos y no ingerir PII/secretos ni datos sin derecho de uso.

---

## 3. Inventario de fuentes de internet candidatas (Argentina)

> **Leyenda de viabilidad:** `Alta` = dato directo/estable para el campo; `Media` = útil con transformación o como referencia; `Baja` = indirecto o fuera del MVP.  
> **Uso recomendado:** `observado` solo si la fuente publica el dato puntual/fechado utilizable como evidencia; de lo contrario `estimado`/contexto, nunca “observado” ficticio.  
> **Importante:** verificar **términos de uso/licencia, robots, rate limits y derechos** antes de automatizar; preferir APIs/datasets oficiales o captura manual autorizada. No scrapear en violación de términos.

### 3.1 Tipo de cambio (FX) — mayor viabilidad para ingesta real

| Fuente | URL | Qué ofrece | Cobertura/actualización | Acceso/formato | Licencia/términos (verificar) | Uso en MVP | Viabilidad ingesta |
|---|---|---|---|---|---|---|---|
| **BNA (Banco Nación) — cotizador** | https://www.bna.com.ar/Personas , https://www.bna.com.ar/Cotizador/MonedasHistorico | USD/ARS y otras (billete/divisa, compra/venta), histórico/tabla | Diaria/horaria según tabla; Argentina | HTML (página/tabla); sin API pública documentada evidente | Consultar términos del sitio; dato público informativo | `fx_rates` (billete o divisa según regla). **Referencia ya usada** (obs. 2026-11-05). | **Alta** (manual o extracción cuidadosa con registro de fecha/fuente) |
| **BCRA — planilla/cotizaciones** | https://www.bcra.gob.ar/PublicacionesEstadisticas/Planilla_cierre_de_cotizaciones.asp , https://www.bcra.gob.ar/cotizaciones-por-fecha/ | Tipos de cambio de referencia/cierre, series | Oficial, diaria/histórica | HTML/planillas; verificar endpoints descargables | Datos públicos oficiales; verificar condiciones de reutilización | `fx_rates` como referencia de comparación (acordar definición OD-004) | **Alta** |
| **datos.gob.ar (catálogo)** | https://datos.gob.ar/ | Búsqueda de datasets oficiales (economía/finanzas) potencialmente reutilizables | Variable por dataset | CSV/JSON/API según dataset + licencia declarada | **Por dataset** (revisar ficha/licencia) | Soporte para FX u otros indicadores si hay serie adecuada | **Media** (depende del dataset) |

### 3.2 Precios de materiales — brecha principal (internet mayormente indicativo)

| Fuente | URL | Qué ofrece | Cobertura/actualización | Acceso/formato | Licencia/términos (verificar) | Uso en MVP | Viabilidad ingesta |
|---|---|---|---|---|---|---|---|
| **Proveedores directos (RFQ, fuera “web abierta” pero canal digital)** | sitios/emails de corralones, distribuidores, fabricantes | **Cotización formal**: precio, moneda, spec, vigencia, IVA, condiciones de entrega | Caso a caso, vigente a la oferta | PDF/email/webform | Confidencial/contractual; requiere permiso para almacenar/compartir | `quotes` `observado` (fuente primaria) | **Alta** para dato real; **ingesta manual/semiestructurada** (parseo posterior) |
| **Red Materiales (referencia)** | https://redmateriales.com.ar/precios/cemento | Rangos/precios de referencia por material/corralones | Variable; orientativo | HTML | Verificar términos; contenido de terceros/agregado | `estimado` (referencia), **nunca** cotización firme | **Media** (referencia; ya usado como ejemplo) |
| **Sodimac / Easy / grandes retail** | https://www.sodimac.com.ar/ , https://www.easy.com.ar/ | Precios publicados, SKU, disponibilidad (retail) | Dinámica; puede variar por sucursal | HTML; anti-scraping/ToS posibles | **Revisar ToS/licencia** antes de automatizar | `estimado` indicativo (no puesto en obra, no condiciones B2B) | **Baja-Media** (manual puntual ok si se cita; automatización sujeta a términos) |
| **MercadoLibre (listados)** | https://www.mercadolibre.com.ar/ | Ofertas/publicaciones de vendedores | Muy variable, heterogénea | Web/API con restricciones de uso | **Términos estrictos**; datos de terceros | `estimado` muy débil (calidad/spec/vigencia inciertas) | **Baja** (solo referencia manual, con cautela) |
| **Cámaras/índices (CAC, INDEC/ICC, otros)** | https://www.camarco.org.ar/ (y publicaciones), https://www.indec.gob.ar/ | Índices de costos, insumos, contexto sectorial | Periódica (mensual, etc.) | Informes/PDF/series; algunos datasets en INDEC/datos.gob.ar | Verificar licencia de reutilización por publicación/dataset | **Contexto/benchmark macro** (`estimado`/derivado), no precio de proveedor | **Media** (para normalizar/deflactar o contexto, no para quote) |

### 3.3 Flete y logística — datos mayormente no públicos

| Fuente | URL | Qué ofrece | Cobertura/actualización | Acceso/formato | Licencia/términos (verificar) | Uso en MVP | Viabilidad ingesta |
|---|---|---|---|---|---|---|---|
| **Transportistas / condición del proveedor** | (cotización directa) | Tarifa/condición “puesto en obra”, origen-destino, fecha | Caso a caso | Presupuesto/email | Confidencial/contractual | `freight_cost` `observado` | **Alta** (manual) |
| **Red vial / geografía (soporte futuro)** | https://www.ign.gob.ar/ , https://datos.gob.ar/ (capas viales), https://www.argentina.gob.ar/obras-publicas/vialidad-nacional | Capas geográficas/red vial, distancias referenciales | Oficial, actualización variable | WMS/WFS/descargas según fuente | Verificar licencia por capa/dataset | Estimación de rutas/distancias **futuro** (OD-006); hoy fuera de MVP | **Media** (futuro) |
| **Routing/proveedores de mapas** | (p. ej. OSRM/servicios comerciales) | Tiempos/distancias por ruta | Depende proveedor | API/ToS | **Crítico**: términos y costos | `derivado/estimado` de distancia (no costo real) | **Baja-Media** (futuro, con ADR) |

### 3.4 Catálogo/normas de materiales (contexto, no precio)

| Fuente | URL | Qué ofrece | Uso | Viabilidad |
|---|---|---|---|---|
| **IRAM / normas técnicas** | https://www.iram.org.ar/ | Normas/especificaciones (acceso generalmente pago/restringido) | Normalizar `spec`/comparabilidad (no precios) | **Baja** para ingesta abierta (derechos/acceso) |
| **Fichas técnicas de fabricantes** | sitios oficiales (Loma Negra, Holcim, etc.) | Especificaciones de producto | Contexto de comparabilidad (`spec`) | **Media** (manual, verificar derechos de uso) |

---

## 4. Mapa de brechas (realidad de ingesta)

| Necesidad | Fuente internet adecuada | Gap real | Acción |
|---|---|---|---|
| FX diario con evidencia | BNA/BCRA (sí) | Regla de comparación no fijada (OD-004) | Definir regla + rutina de captura (manual/adapter) con fecha/fuente |
| Precios comparables “observados” | **No hay fuente pública general confiable** | Precios reales son B2B/caso a caso y con vigencia | Captura por **RFQ** (2–3 proveedores) → ingesta semiestructurada al JSON |
| Flete “puesto en obra” | **No público** | Depende de origen-destino y acuerdo | Cotizar transporte o condición de entrega; si no, `no_disponible` |
| Benchmark de mercado | Índices (CAC/INDEC), rangos publicados | No equivalen a oferta transable | Usar solo como `estimado`/contexto, nunca como sustituto de cotización |

---

## 5. Estrategia de ingesta recomendada (pragmática, MVP)

1. **Ahora (sin automatización frágil):** ingesta **manual/semiestructurada** usando `input_template_real.json` + `CHECKLIST_CAPTURA_DATOS.md`.
   - FX: capturar de BNA/BCRA (valor, fecha, tipo billete/divisa, compra/venta) → `observado`.
   - Cotizaciones/flete: registrar presupuestos recibidos (evidencia/ref) → `observado` cuando aplique.
2. **Siguiente (ligero, determinista):** adaptadores de importación **opt-in** por fuente, uno a uno, con “source card” y pruebas offline:
   - (a) normalizador CSV/JSON de presupuestos estructurados, (b) capturador/registrador de FX (entrada asistida o fetch controlado si términos lo permiten) que guarde `retrieved_at`, URL y valor original.
3. **Gobernanza mínima por fuente (antes de automatizar):** ficha con owner, URL, licencia/ToS, campos, cobertura, actualización, límites/rate, calidad, retención y método de extracción reproducible (docs `data/00-data-governance.md`).
4. **Evitar:** scraping que viole términos, inferir precios privados de páginas incompletas, mezclar `estimado` como `observado`, y dependencias/IA para cálculos de negocio.

---

## 6. Backlog de ingesta sugerido (corto)

| ID | Ítem | Tipo | Valor | Dependencia |
|---|---|---|---|---|
| I-01 | Fijar regla FX (fuente, billete/divisa, compra/venta) y registrar snapshots | dato/proceso | Alto | decisión OD-004 |
| I-02 | Completar 1 **caso real comparable** (1 obra, 1 material, ≥2 cotizaciones formales + flete) | dato | Muy alto | RFQ/contactos |
| I-03 | Source card + importador manual guiado para presupuestos (CSV/JSON) → `quotes` | ingesta | Alto | esquema estable |
| I-04 | Source card FX BNA/BCRA + registro de `retrieved_at`/evidencia (manual o fetch permitido) | ingesta | Alto | términos/licencia verificados |
| I-05 | Catálogo de referencias indicativas (marcadas `estimado`) para saneamiento, no para decisión | contexto | Medio | términos por fuente |

---

## 7. Riesgos y controles (P1/P7)

- **Veracidad:** precios web/listados ≠ cotización firme; flete ausente invalida “costo entregado” comparable. Control: estados de procedencia y alerta `NO COMPARABLE`.
- **Licencias/ToS:** automatizar extracción sin derecho puede ser incumplimiento. Control: source card + aprobación antes de adapter/scraper.
- **Vigencia/sesgo:** precios/FX cambian; muestras no representativas. Control: fecha/vigencia, no extrapolar, cobertura explícita.
- **Privacidad/confidencialidad:** presupuestos pueden ser sensibles (OD-008). Control: no publicar PII/condiciones confidenciales; permisos/retención.
- **Técnico:** HTML inestable en fuentes sin API. Control: preferir datasets/API oficiales; parsers tolerantes + validación de esquema + tests offline con fixtures.

---

## 8. Fuentes ya identificadas/usadas (evidencia en repo)

- **BNA (observado, FX):** https://www.bna.com.ar/Personas , https://www.bna.com.ar/Cotizador/MonedasHistorico — registrado en `casos/caso_real_fx_bna_2026-11-05_cemento_ref.json` (USD/ARS billete venta 1570.00 y divisa venta 1545.50, fecha 2026-11-05, consulta 2026-11-10).
- **Red Materiales (estimado, referencia de rango):** https://redmateriales.com.ar/precios/cemento — usado como referencia indicativa en el mismo caso (no cotización formal).

*Este informe no certifica licencias, disponibilidad ni exactitud futura de las fuentes externas; cada una debe validarse (términos, acceso, vigencia) antes de ingesta automatizada o uso operativo.*
