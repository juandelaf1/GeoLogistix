# Gobernanza de datos — GeoLogistix

> Reglas de procedencia, calidad, frescura y derechos de uso. Alineadas con la gobernanza de datos
> del ecosistema (tiers A–F) y con los requisitos `DATA-PROVENANCE-001`, `INGEST-002..007`.

---

## 1. Principios

1. **Evidencia antes que narrativa.** Cada cifra declara su origen y su estado.
2. **Lo ausente se declara ausente.** Nunca se sustituye un dato faltante por 0, por un promedio ni
   por un valor "razonable".
3. **El original no se reescribe.** Monto y moneda originales, fecha de emisión y vigencia de una
   oferta se conservan; una nueva tasa FX genera una **nueva** comparación, no una reescritura.
4. **Frescura explícita.** Un dato viejo se muestra con su edad y exige decisión humana.
5. **Permisos antes que uso.** No se ingiere nada sin derecho de uso verificado.

---

## 2. Tiers de evidencia

| Tier | Tipo | Ejemplo | Uso en el motor |
|---|---|---|---|
| **A** | Oficial / público de referencia | Tipo de cambio publicado (BNA/BCRA), datasets oficiales | `observed` |
| **B** | Datos de negocio del cliente | Historial de compras, facturas, precios negociados | `observed` (uso del cliente) |
| **C** | Evidencia submitting el proveedor | Presupuesto, proforma, ficha técnica, certificado | `observed` |
| **D** | Derivado / calculado | Total en moneda base, tasa invertida, comparación | `derived` |
| **E** | Extraído por IA (OCR/clasificación) | Campos leídos de un PDF | `machine-extracted` + pendiente de verificación |
| **F** | Sintético / prueba | Fixtures, ejemplos | `synthetic`, jamás reportado como real |

---

## 3. Estados y campos obligatorios

**Estados:** `observed` · `derived` · `estimated` · `synthetic` · `no_disponible` · `rejected`.

**Campos mínimos por observación crítica:**

```
evidence_id · claim_or_field · value · unit · source_name · source_url_or_document_id
issuer · published_or_issued_at · observed_at · valid_from · valid_until
geographic_scope · material_or_batch_scope · extraction_method · verification_status
limitations · license_or_use_rights · reviewer_id (si verificado por persona) · supersedes_id
```

No todos aplican a todos los casos. Lo que no se conoce se registra como estado definido, **nunca
como valor inventado**.

**Campos mínimos del contrato de entrada:** ver `docs/DEFINICIONES.md` §4 y `docs/ARQUITECTURA.md` §3.

---

## 4. Controles de calidad

| Control | Regla |
|---|---|
| Esquema | Tipos, unidades, códigos de moneda, fechas válidas |
| Idempotencia | Deduplicación por id nativo de la fuente o clave compuesta estable |
| Outliers | Se **señalan y explican**, no se descartan silenciosamente |
| Coherencia de moneda | Importe vs moneda vs unidad; cantidades positivas |
| FX | Fecha, par, tipo y fuente; límites de frescura por caso |
| Vigencia | Oferta vencida → `rejected` o `estimated` con edad visible |
| Comparabilidad | Spec, unidad, destino, alcance fiscal y ventana temporal |
| Rechazo | Entradas incompletas, sospechosas o inconsistentes van a cuarentena, conservando el artefacto bruto si los derechos lo permiten |
| Validación ≠ validación | "Parseó correctamente" **no** significa "validado" |

---

## 5. Frescura

No hay un TTL global: se define por fuente y por caso.

| Dato | Frescura esperada | Comportamiento |
|---|---|---|
| Tipo de cambio | Fecha del día de comparación | Tasa de otra fecha → declarar y justificar |
| Oferta de material | Vigencia explícita del presupuesto | Vencida → `rejected`/alerta; no comparar sin override auditado |
| Referencia web | Fecha de consulta | Siempre `estimated`; nunca `observed` |
| FleteCotización | Fecha de cotización | Vencida → pedir nueva |

Un dato stale **se muestra con su edad** y exige un override explícito y auditado.

---

## 6. Derechos de uso y fichas de fuente

Antes de automatizar cualquier ingesta:

1. **Ficha de fuente** (`docs/FUENTES.md`): propietario, URL, licencia/Términos, campos disponibles,
   geografía, cobertura histórica, cadencia de actualización, límites (API/descargas), derechos de
   retención, riesgos de calidad y **prueba de extracción reproducible**.
2. Preferir fuentes primarias y APIs oficiales.
3. **No** scrapear sitios en violación de sus términos ni inferir precios privados de páginas
   incompletas.
4. Verificar si el uso previsto (comercial) está permitido por los términos.
5. Las referencias públicas de precio se tratan como `estimated` y se citan con fecha de consulta.

---

## 7. Privacidad y confidencialidad

- El motor trabaja con **datos de costo**, no con personas: proveedor, material, precio, origen,
  destino. Minimizar: no incluir datos personales, RUT, cuentas bancarias, contactos individuales
  ni condiciones confidenciales del cliente.
- Las cotizaciones pueden ser confidenciales: permiso del emisor antes de storing, compartir o publicar.
- Retención: definir con el cliente (no se define en el motor; es responsabilidad del consumidor).
- Exports: sin datos personales por defecto; agregar agregados si hace falta.
- Sin secretos ni claves en el repo, en logs ni en snapshots versionados.

---

## 8. Auditoría

Cada comparación debe poder reconstruirse con: versión de metodología (`delivered-cost/0.1`),
versión de fórmula, snapshot FX aplicado (par/tipo/fecha/fuente/`retrieved_at`), entradas del caso,
supuestos, exclusiones, alertas y — cuando aplique — el aprobador humano.

Mecanismo: **archivar el par caso + resultado**. El motor no persiste nada por diseño.

---

## 9. Gates de avance

| Gate | Criterio |
|---|---|
| G1 — Caso comparable | ≥2 ofertas `observed` con flete informado, spec equivalente y snapshot FX fechado |
| G2 — Uso operativo | Regla FX aprobada + fichas de fuente validadas + permisos de uso confirmados |
| G3 — Auditoría | Par caso+resultado archivado y versionado |
| G4 — Escala | Tests de regresión verdes en CI y contrato versionado con consumidores |

---

## 10. Lo que el motor nunca hará

- Inventar cotizaciones, tasas, fletes, permisos, capacidades o beneficios.
- Presentar un score o comparación como certificación técnica, legal, fiscal o ambiental.
- Dejar que un precio menor anule una restricción técnica, legal o de seguridad.
- Enviar datos sensibles a un proveedor de modelos sin decisión aprobada.
- Reportar datos sintéticos como observaciones reales.
