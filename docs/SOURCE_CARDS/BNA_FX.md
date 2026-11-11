# Source Card — BNA (Tipo de cambio USD/ARS)

- **id:** `bna_fx_usdars`
- **owner/proveedor:** Banco de la Nación Argentina (BNA)
- **url:** https://www.bna.com.ar/Personas ; https://www.bna.com.ar/Cotizador/MonedasHistorico
- **tipo:** oficial/publicada (referencia de cotización), Tier A (referencia pública)
- **campos útiles:** par USD/ARS, compra/venta, billete/divisa, fecha/hora publicación, otras monedas
- **cobertura/geografía:** Argentina, USD/ARS (y otras divisas)
- **actualización:** diaria/según publicación en sitio (verificar hora)
- **acceso/formato:** HTML (tablas en página). No se identificó API pública documentada en esta revisión.
- **licencia/términos:** **verificar** términos de uso del sitio antes de automatización/reutilización sistemática. Tratar como dato público informativo con atribución de fuente/fecha.
- **límites/riesgos:** cambios de maquetado HTML; disponibilidad; diferencia billete vs divisa vs tasa de operación real.
- **calidad/procedencia:** registrar `date` publicada, `retrieved_at`, URL, tipo (billete/divisa, compra/venta) y valores crudos. `status=observado` si proviene de la publicación.
- **uso en MVP:** `fx_rates[]` (`rate`, `pair`, `date`, `source`, `status`, `url_or_ref`).
- **método de ingesta:** manual (copiar) o `tools/record_fx.py` (fetch + extracción con validación; fallback `--manual`).
- **estado:** candidato validado para captura puntual; automatización recurrente sujeta a revisión de términos y robustez del parser.
