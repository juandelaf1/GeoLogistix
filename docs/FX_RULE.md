# Regla de Tipo de Cambio (FX) — GeoLogistix costo-entregado-mvp

> **Decisión operativa (I-01, liviana):** regla explícita y versionable para comparar costos en ARS/USD. Registrar siempre `rate, pair, date, source, status, url_or_ref, retrieved_at`.

## Regla por defecto (comparación de costos)
- **Fuente primaria:** Banco de la Nación Argentina (BNA), cotizador público.
  - Billetes: https://www.bna.com.ar/Personas
  - Divisas/histórico: https://www.bna.com.ar/Cotizador/MonedasHistorico
- **Par:** `USD/ARS`.
- **Tipo a usar (elegir uno por caso y mantenerlo en todas las ofertas del caso):**
  - **`divisa_venta`** (recomendado para convertir costos referenciados en USD a ARS en comparación de abastecimiento): BNA Divisas, Dólar U.S.A, **Venta**.
  - Alternativas válidas si se declara: `billete_venta`, `divisa_compra`, `billete_compra`.
- **Fecha:** la fecha publicada por la fuente (`date`) y la fecha/hora de captura (`retrieved_at`, UTC ISO-8601).
- **Estado:** `observado` si se toma de fuente publicada verificable con evidencia (URL/captura/registro); `estimado` si es tasa acordada/proyectada.

## Reglas de uso
1. **No mezclar tipos** (p. ej. billete y divisa) dentro de una misma comparación sin declararlo.
2. **No convertir sin tasa fechada**: si falta FX necesario, el ítem queda no comparable por conversión (el comparador lo marca).
3. **Moneda original inmutable:** registrar siempre el monto y moneda originales de la cotización.
4. **Vigencia:** si la cotización y la comparación tienen fechas distintas, conservar ambas; la tasa aplicada debe corresponder al criterio del caso (p. ej. día de comparación) y declararse.
5. **Evidencia:** todo snapshot automático/manual debe incluir `source`, `url_or_ref`, `retrieved_at` y, cuando sea posible, extracto/valores crudos.

## Limitaciones
- La cotización publicada es informativa/referencial según la fuente; puede diferir de la tasa efectiva de una operación real.
- Requiere verificación de términos de uso de la fuente antes de automatizar ingesta recurrente.
- Cambios de formato del sitio pueden romper extractores: usar validación y fallback manual (`tools/record_fx.py --manual`).
