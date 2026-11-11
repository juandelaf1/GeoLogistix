# Fuentes — fichas de fuente candidatas

> Estado: **candidatas a investigar**, no fuentes aprobadas. Antes de automatizar cualquier ingesta
> hay que verificar licencia/Términos, cobertura, límites y una prueba de extracción reproducible.
> Ver `docs/GOBERNANZA_DATOS.md` §6.

---

## 1. Resumen

| Fuente | Dato | Tipo | Viabilidad | Uso en el motor |
|---|---|---|---|---|
| [BNA](https://www.bna.com.ar/Personas) | USD/ARS (billete y divisa) | Oficial (A) | **Alta** | `fx_rates[]` como `observed` |
| [BCRA](https://www.bcra.gob.ar/PublicacionesEstadisticas/Planilla_cierre_de_cotizaciones.asp) | Cotizaciones de referencia/cierre | Oficial (A) | Alta | Alternativa/consistencia histórica de FX |
| Proveedores / corralones / fabricantes | Precio, spec, vigencia, flete | Negocio (B/C) | **Alta** (RFQ) | Fuente primaria de `quotes[]` (`observed`) |
| Transportistas | Flete puesto en destino | Negocio (B/C) | Alta (RFQ) | `freight_cost` (`observed`) |
| Retail online (Sodimac, Easy) | Precio publicado | Web (A/D) | Media | **Solo** `estimated` |
| Agregadores de precios | Rangos orientativos | Web (A/D) | Media | **Solo** `estimated` / contexto |
| Marketplaces | Listados heterogéneos | Web | Baja | Solo referencia manual, con cautela |
| Índices sectoriales (INDEC, cámaras) | Contexto macro | Oficial/sectorial | Media | Contexto; no precio transable |
| Redes viales / geografía (IGN, datos.gob.ar) | Distancias referenciales | Oficial (A) | Media | **Futuro** (rutas), fuera de v0.1 |

---

## 2. Fichas

### 2.1 BNA — tipo de cambio USD/ARS
- **Owner:** Banco de la Nación Argentina.
- **URL:** `https://www.bna.com.ar/Personas` (billetes) · `https://www.bna.com.ar/Cotizador/MonedasHistorico` (divisas).
- **Campos:** par, compra/venta, tipo (billete/divisa), fecha/hora de publicación, otras divisas.
- **Acceso:** HTML; sin API pública documentada en esta revisión.
- **Licencia/Términos:** **verificar** antes de automatización; el dato es público informativo.
- **Riesgos:** cambios de maquetado (parser frágil), diferencia billete vs divisa vs tasa operativa.
- **Procedencia mínima:** `pair`, `rate`, `date` (publicada), `source` (tipo), `rate_type`, `url_or_ref`, `retrieved_at`.
- **Uso:** `fx_rates[]`; regla por defecto en `FX_RULE.md`.

### 2.2 BCRA — cotizaciones de referencia
- **Owner:** Banco Central de la República Argentina.
- **URL:** `https://www.bcra.gob.ar/PublicacionesEstadisticas/Planilla_cierre_de_cotizaciones.asp`.
- **Definición:** "cierre/referencia" ≠ billete/divisa BNA: requiere regla explícita (OD-004).
- **Uso:** consistencia histórica y comparabilidad de fuentes.

### 2.3 Proveedores (RFQ) — fuente primaria
- **Canales:** web, email, teléfono, proforma/presupuesto escrito.
- **Datos mínimos:** proveedor, material + spec, cantidad/unidad, precio y moneda, IVA/inclusiones,
  vigencia, condición de entrega, flete, origen, nro de presupuesto, evidencia.
- **Riesgos:** comparabilidad entre specs, vigencia corta, sesgo de muestra, confidencialidad.
- **Uso:** `quotes[]` con `status=observed` y `evidence_ref`.

### 2.4 Transportistas — flete
- **Datos:** monto, moneda, origen/destino, fecha, qué incluye (descarga, seguro, peajes).
- **Uso:** `freight_cost`. Si no existe dato → la opción **no es comparable** (correcto).

### 2.5 Retail online y agregadores — solo referencia
- **Riesgos:** no es cotización B2B ni puesto en obra; IVA y condiciones opacas; spec no comparable;
  vigencia incierta; posibles restricciones anti-scraping.
- **Uso:** `estimated` con `source` + fecha de consulta; nunca sustituyen un RFQ.

### 2.6 Índices y contexto
- **Uso:** contexto macro o normalización analítica (`derived`); **no** precio de proveedor.

---

## 3. Procedencia de precios de referencia (web)

Si se registra un precio de referencia, el caso debe incluir:
`source` (URL/nombre) · `date` (fecha de consulta) · `status = estimated` · `evidence_ref` ·
limitaciones en `notes` ("no es cotización formal", "sin flete", "spec a confirmar").

---

## 4. Estado actual de los datos

| Dato | Estado | Dónde |
|---|---|---|
| USD/ARS (BNA, publicado 2026-11-05) | `observed` | `examples/case_cemento_caba.json` |
| Precios de cementos publicados en web | `estimated` | `examples/case_cemento_caba.json` |
| Cotización formal (RFQ) + flete | `no_disponible` | pendiente — bloquea la comparación |

**Un caso no es comparable hasta que existan ≥2 ofertas `observed` con flete informado.**
