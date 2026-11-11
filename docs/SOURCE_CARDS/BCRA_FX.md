# Source Card — BCRA (Cotizaciones de referencia/cierre)

- **id:** `bcra_fx_ref`
- **owner/proveedor:** Banco Central de la República Argentina (BCRA)
- **url:** https://www.bcra.gob.ar/PublicacionesEstadisticas/Planilla_cierre_de_cotizaciones.asp ; https://www.bcra.gob.ar/cotizaciones-por-fecha/
- **tipo:** oficial, Tier A
- **campos útiles:** cotizaciones de cierre/referencia por moneda y fecha
- **cobertura/geografía:** Argentina, múltiples monedas
- **actualización:** diaria/histórica (según publicación)
- **acceso/formato:** HTML/planillas (verificar opciones de descarga/series)
- **licencia/términos:** datos públicos oficiales; **verificar** condiciones de reutilización/redistribución.
- **límites/riesgos:** definición de “cierre/referencia” puede diferir de billete/divisa BNA y de tasas operativas; requiere regla explícita (OD-004).
- **calidad/procedencia:** registrar fecha, fuente exacta/URL, definición de la tasa y `retrieved_at`.
- **uso en MVP:** alternativa/fuente de `fx_rates` si la regla del caso la adopta.
- **método de ingesta:** captura manual o adapter dedicado (pendiente, tras validar formato/descarga).
- **estado:** candidato recomendado para consistencia histórica/referencia.
