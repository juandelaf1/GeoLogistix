# Checklist de captura de datos reales (costo entregado)

Objetivo: salir de la simulación sintética con **cotizaciones y tasas verificables**, manteniendo el MVP liviano (`compare.py`, `delivered-cost/0.1`). Regla: **no inventar** (si falta, `null` + `status=no_disponible` o dejar fuera).

## 0) Definir el caso (1 comparación acotada)
- [ ] Obra/destino (dirección/localidad) y responsable del caso.
- [ ] **1 material** y especificación comparable (marca/norma/calidad, unidad).
- [ ] Cantidad fija y fecha objetivo/ventana de compra.
- [ ] Moneda base de comparación (ARS o USD) y criterio de decisión.

## 1) Tipo de cambio (FX) — fijar regla antes de comparar
- [ ] Fuente elegida (p. ej. BNA vendedor/divisa, BCRA/otra acordada) y **par** (USD/ARS).
- [ ] Tasa, **fecha/hora de referencia** y `status=observado` (o `estimado` si es acordada).
- [ ] Guardar evidencia (URL/captura/nro de tabla) en `url_or_ref`/`source`.
- [ ] Si las cotizaciones vienen en distintas monedas/fechas, registrar la tasa usada y la consistencia del corte.

## 2) Cotizaciones de material (2–3 proveedores, `observado`)
Pedir por escrito (presupuesto/proforma/email):
- [ ] Proveedor, contacto y origen/planta/depósito.
- [ ] Material y especificación (equivalente entre ofertas).
- [ ] Precio unitario, **moneda**, cantidad/unidad y total si aplica.
- [ ] **Fecha**, vigencia (`valid_until`) e identificador de presupuesto.
- [ ] Inclusiones/exclusiones: **IVA/impuestos**, descuentos, condiciones de pago.
- [ ] Condición de entrega (puesto en obra / retiro / FCA, etc.).
- [ ] Evidencia: archivo o nro de presupuesto (`evidence_ref`, respetando permisos).

## 3) Flete / logística (costo entregado)
- [ ] ¿Precio “puesto en obra”? registrar flete = 0 explícito o incluido (aclarar en notas) según corresponda.
- [ ] Si no incluido: cotización de transporte al destino (monto, moneda, fecha, fuente) → `status=observado`.
- [ ] Si solo hay estimación (km×tarifa): marcar `status=estimado`, documentar método; si no hay dato, dejar `freight_cost` vacío (el comparador lo marcará **no comparable**).
- [ ] Otros costos de entrega (descarga, seguro, peajes/pallet): `other_costs` + `other_label` + moneda.

## 4) Cargar y ejecutar
- [ ] Copiar `input_template_real.json` → `caso_<obra>_<material>_<fecha>.json`.
- [ ] Completar campos, procedencia (`status/source/date`) y referencias; sin PII innecesaria.
- [ ] Ejecutar:
  - `python compare.py caso.json` (tabla)
  - `python compare.py caso.json --format json --out resultado.json`
  - `python compare.py caso.json --format csv --out resultado.csv`
- [ ] Revisar alertas: ítems `NO COMPARABLE`/`incompleto` no sirven como costo entregado cerrado.

## 5) Calidad y permisos (mínimos)
- [ ] Verificar que ofertas sean **comparables** (misma especificación/unidad/cantidad y condiciones de entrega).
- [ ] Confirmar vigencia de precios y de la tasa FX al momento de comparar.
- [ ] Respetar confidencialidad/permisos de las cotizaciones (no publicar datos sensibles sin autorización).
- [ ] Guardar insumos y resultado como evidencia del caso (procedencia trazable).

## Mapeo rápido al input
- `fx_rates[]`: `pair, rate, date, source, status, url_or_ref`
- `quotes[]`: `supplier, origin, material, spec, quantity, unit, unit_price, currency, freight_cost, freight_currency, other_costs, date, valid_until, source, status, evidence_ref, notes`
- Recordatorio: el comparador exige flete **informado** (aunque sea 0 explícito) para marcar una opción como comparable.
