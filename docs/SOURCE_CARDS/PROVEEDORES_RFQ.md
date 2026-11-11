# Source Card — Proveedores / RFQ (cotizaciones y flete)

- **id:** `supplier_rfq_quotes`
- **owner/proveedor:** corralones, distribuidores, fabricantes, transportistas (B2B/B2C)
- **url/canal:** sitios web de proveedores, email, teléfono, proforma/presupuesto escrito
- **tipo:** negocio/evidencia presentada por proveedor, Tier B/C
- **campos útiles:** material/spec, cantidad/unidad, precio unitario y moneda, IVA/inclusiones, vigencia, condición de entrega, flete/puesto en obra, origen, contacto, nro presupuesto
- **cobertura/geografía:** según proveedor y zona de obra (Argentina)
- **actualización:** por oferta (vigencia explícita o acotada)
- **acceso/formato:** PDF, email, imagen, webform, mensaje; heterogéneo
- **licencia/términos:** **confidencialidad/permiso de uso** variable; no publicar ni compartir sin autorización. Registrar solo lo permitido.
- **límites/riesgos:** comparabilidad (spec/unidad/condiciones distintas), vigencia vencida, sesgo de muestra, datos incompletos.
- **calidad/procedencia:** `status=observado` cuando hay presupuesto verificable; guardar referencia/evidencia (`evidence_ref`, nro, fecha); declarar inclusiones/exclusiones.
- **uso en MVP:** fuente primaria de `quotes[]` y flete real para costo entregado comparable.
- **método de ingesta:** manual estructurada (`input_template_real.json`) o `tools/import_quotes_csv.py` desde CSV normalizado.
- **estado:** **fuente principal requerida** para casos reales (brecha actual).
