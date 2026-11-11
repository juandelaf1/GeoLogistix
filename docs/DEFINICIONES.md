# Definiciones — GeoLogistix

> Glosario normativo. Si un término aparece en el código o en el contrato, significa exactamente
> lo que dice aquí.

---

## 1. Offering / comparación

**Oferta (Quote).** Conjunto de condiciones comerciales para un material, cantidad y destino
concretos, atribuible a un proveedor. Contiene precio, moneda, condiciones de entrega y vigencia.

**Costo entregado (delivered cost).** Suma del costo del material **más** los costos explícitos
de hacerse llegar al destino: flete, carga/descarga y otros costos declarados. No incluye costos
no declarados ni estimados sin etiquetar.

**Costo entregado comparable.** Costo entregado de dos o más ofertas que comparten
especificación, base de unidad y cantidad, punto de entrega, alcance fiscal y ventana temporal
(comparability key).

**Comparable (opción comparable).** Bandera `comparable = true`: la opción tiene material
calculable, flete **informado** y conversión completa. Las demás son visibles pero **no** rankeables.

**Incompleto (incompleto / `incomplete`).** La opción tiene al menos un componente material o
logístico ausente o no convertible.

**Ranking.** Orden de las opciones comparables por total en moneda base, ascendente. Las no
comparables se listan aparte, con `rank = null` y su alerta.

**Moneda base (base currency).** Moneda en la que se presenta la comparación. Es una **base de
comparación**, no una contabilidad ni una conclusión fiscal.

**Snapshot FX.** Observación de tipo de cambio registrada con par, tipo, valor, fecha publicada,
fuente, `retrieved_at` y estado. Es inmutable: una nueva tasa produce una nueva comparación, no
reescribe la anterior.

---

## 2. Procedencia / evidencia

**Estado de evidencia (evidence state).** Etiqueta que declara cómo se obtuvo un dato:
`observed`, `derived`, `estimated`, `synthetic`, `no_disponible`, `rejected`.

**Observado.** Dato tomado directamente de una fuente verificable, fechada y referenciada
(presupuesto escrito, cotización de transporte, tipo de cambio publicado).

**Derivado.** Dato calculado a partir de datos observados (tasa invertida, total en moneda base,
porcentaje). Nunca se presenta como observación.

**Estimado.** Valor aproximado cuyo origen o método se declara explícitamente (precio de
referencia web, flete estimado por distancia × tarifa). **No habilita** comparación como observada.

**Sintético.** Valor generado para pruebas o demostración. Se identifica como tal y no se reporta
como observación real.

**No disponible.** El dato no existe o no se obtuvo. Se representa como ausente + estado, nunca
como 0.

**Rechazado.** Dato descartado por una regla de calidad (fuera de vigencia, especificación
incompatible, error de unidad).

**Procedencia (provenance).** Cadena que permite reconstruir de dónde salió cada cifra:
`source` + `date` + `valid_until` + `evidence_ref` + `status` + (para FX) `rate_type` y
`retrieved_at`.

**Vigencia (validity).** Período durante el cual la oferta mantiene sus condiciones. Si no viene
declarada, se registra como desconocida y se envejece en la alerta.

**Inclusiones y exclusiones.** Qué queda dentro del precio cotizado (IVA, flete, descarga, plazo) y
qué no. Dos ofertas con alcances distintos no son comparables aunque el número coincida.

---

## 3. Material y logística

**Especificación (spec).** Identidad técnica del material (marca, norma, calidad, presentación) y
su versión. Sin especificación comparable, dos precios no son comparables.

**Base de unidad.** Denominador de la unidad de venta (bolsa, tn, m³, viaje). Comparar unidades
distintas exige una densidad o conversión documentada.

**Origen (origin).** Planta, depósito o punto de despacho del material.

**Destino (destination).** Punto de entrega (obra o punto acordado) que define el flete.

**Flete (freight).** Costo de llevar el material al destino. Su **existencia** y su monto se
registran por separado; un flete de 0 explícito significa "incluido/puesto en obra", no "desconocido".

**Condición de entrega (freight terms).** Alcance del precio en logística: puesto en obra, retiro,
FCA, a convenir. Define comparabilidad.

**Otros costos (other costs).** Descarga, seguro, pallets, peajes u otros conceptos explícitos, con
su etiqueta y moneda.

**IVA / impuestos.** Alcance fiscal de la oferta. Se registra como `price_includes_vat` y debe
coincidir para comparar.

---

## 4. Tipos de cambio

**Par (pair).** Cadena de monedas, p. ej. `USD/ARS`.

**Tipo de tasa (rate type).** Qué cotiza exactamente la fuente: `billete_compra`,
`billete_venta`, `divisa_compra`, `divisa_venta`, `custom`. Regla: **no mezclar tipos** en una misma
comparación sin declararlo.

**Tasa observada.** Valor publicado por una fuente en una fecha concreta. Solo es aplicable si su
fecha y tipo son compatibles con el caso.

**Tasa invertida.** Tasa recíproca derivada de un par publicado en sentido contrario; se marca
`derived` y conserva `derived_from`.

**Sin tasa FX.** Situación en la que no existe observación aplicable: la conversión falla y la
opción queda **no comparable**. Nunca se usa una tasa "de facto" implícita.

---

## 5. Contrato

**`delivered-cost/0.1`.** Versión del contrato de salida (JSON) y de la metodología de cálculo.
Campos clave: `project`, `base_currency`, `fx_rates[]`, `quotes[]`, `results[]`, `disclaimer`,
`contract_version`.

**Additividad.** Los cambios aditivos (campos nuevos opcionales) son compatibles; los cambios que
alteran el significado de un campo o la semántica de comparabilidad requieren versión mayor y
nota de migración.

---

## 6. Roles y límites

**Motor.** Calcula, declara supuestos y alertas. No decide.

**Usuario humano.** Decide, valida equivalencias técnicas y asume los riesgos del contexto.

**Revisor cualificado.** Valida idoneidad técnica, legal, ambiental o fiscal. Ningún output del
motor lo sustituye.

**Consumidor (otra plataforma).** Puede usar el motor como proveedor de evidencia (nivel L0/L1)
sin adoptar sus dominios ni su persistencia.
