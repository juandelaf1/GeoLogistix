# Source Card — Referencias de precios web (indicativas)

- **id:** `web_price_references`
- **owner/proveedor:** agregadores/retail (p. ej. redmateriales.com.ar, sodimac.com.ar, easy.com.ar) y marketplaces (MercadoLibre)
- **url:** https://redmateriales.com.ar/precios/cemento ; https://www.sodimac.com.ar/ ; https://www.easy.com.ar/ ; https://www.mercadolibre.com.ar/
- **tipo:** publicación web/listado, Tier A/D según caso, **no** cotización contractual
- **campos útiles:** precio publicado, producto/SKU, moneda, fecha de consulta (a veces stock/sucursal)
- **cobertura/geografía:** variable; retail o agregados
- **actualización:** dinámica/desconocida; puede no reflejar condiciones B2B ni entrega
- **acceso/formato:** HTML; posibles restricciones (ToS, anti-scraping)
- **licencia/términos:** **verificar ToS y derechos** por sitio antes de automatizar. Atribuir fuente y fecha de consulta.
- **límites/riesgos:** no es cotización formal, puede excluir flete/impuestos, spec no comparable, vigencia incierta, sesgo.
- **calidad/procedencia:** usar **solo** como `status=estimado` (referencia indicativa) o contexto; **nunca** como `observado` de cotización firme ni como sustituto de RFQ.
- **uso en MVP:** `references/` o quotes marcadas `estimado` con fuente/URL/fecha de consulta y advertencia.
- **método de ingesta:** registro manual/referencia (`tools/import_quotes_csv.py` marcando status estimado) tras revisión de términos.
- **estado:** útil para contexto/rango; no suficiente para caso comparable.
