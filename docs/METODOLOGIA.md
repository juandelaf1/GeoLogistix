# Metodología — GeoLogistix

> Versión de metodología: `delivered-cost/0.1` · Determinista · Sin IA.

Esta documento describe **cómo se calcula** el costo entregado, **qué reglas lo gobiernan**, y
**qué límites tiene**. Es la referencia normativa para cualquier implementación que consuma o
replique el contrato.

---

## 1. Objetivo y no-objetivo

**Objetivo:** hacer comparables ofertas de abastecimiento que, en su forma original, no lo son
(moneda distinta, flete ausente o incluido, condiciones de entrega distintas, especificaciones
distintas) **sin ocultar lo que falta**.

**No-objetivo (explícito):** no se predice el precio futuro, no se recomienda un proveedor, no se
calculan rutas ni tiempos de tránsito, no se certifica idoneidad técnica/legal/ambiental y no se
ejecutan pagos ni compras.

---

## 2. Definición de costo entregado

Para un destino y una cantidad comparables:

```
delivered_total = material_amount
                + loading
                + transport
                + unloading
                + other_explicit_costs
                + tax_adjustments_explicitly_declared
```

Cada componente se mantiene **separado** en el desglose. No se fusionan en un único número sin
explicación, y no se cuenta dos veces un costo ya incluido en el precio (p. ej. si la oferta es
"puesto en obra", el flete es 0 explícito y no se le suma otro).

`delivered_unit_cost = delivered_total / comparable_quantity`

---

## 3. Fórmulas de implementación (v0.1)

Por cada oferta:

```python
material_cost   = unit_price × quantity
material_base   = material_cost   × fx(currency        → base)
freight_base    = freight_cost    × fx(freight_currency → base)
other_base      = other_costs     × fx(other_currency  → base)
total_base      = material_base + freight_base + other_base
```

- Aritmética **decimal**: `Decimal`, precisión 28, `ROUND_HALF_UP` a 2 decimales. Nunca float binario para dinero.
- Conversión **por capa**: el monto y la moneda originales se conservan; la conversión se registra aparte
  con par, tipo de tasa, fecha, fuente y estado.
- Redondeo: se aplica **al total en moneda base**; los componentes se muestran sin redondeo oculto
  (el JSON incluye el valor con 2 decimales y el desglose por concepto).

---

## 4. Reglas de comparabilidad (invariantes)

| # | Regla | Consecuencia observable |
|---|---|---|
| R1 | Un dato ausente **no** es 0 | Sin precio/cantidad → `material_cost incompleto`; sin flete → `flete no informado` |
| R2 | 0 explícito del usuario sí vale | `freight_cost = 0` (p. ej. "puesto en obra") → comparable |
| R3 | Comparabilidad de costo entregado = material **y** flete informado **y** conversión completa | Si falta cualquiera: `comparable = false` |
| R4 | Sin FX observada no hay conversión | Alerta `sin tasa FX USD/ARS`; opción no comparable |
| R5 | Tasa inversa se marca `derived` | Si la fuente publica el par contrario, la tasa se invierte y se anota `derived_from` |
| R6 | Moneda original inmutable | El total en moneda original siempre es recuperable del desglose |
| R7 | Procedencia por opción y por dato | Cada opción expone `status` (`observed \| derived \| estimated \| synthetic \| no_disponible \| rejected`), `source`, `date`, `valid_until`, `evidence_ref` |
| R8 | Ranking sin forzajes | No comparables quedan fuera del ranking (`rank = null`) y se muestran aparte con su alerta |
| R9 | Determinismo | Sin red, sin aleatoriedad, sin LLM: mismos datos → mismo resultado |
| R10 | Sin alcanceChecker | El motor **no** valida equivalencia técnica/legal/ambiental de materiales; eso requiere revisión humana cualificada |

---

## 5. Estados de procedencia (evidence states)

| Estado | Significado | Uso típico |
|---|---|---|
| `observado` | Tomado de una fuente verificable, fechada y con referencia | Presupuesto escrito; tipo de cambio publicado |
| `derived` | Calculado a partir de datos observados | Tasa inversa; total en moneda base |
| `estimado` | Estimación declarada (fuente o método conocido) | Precio de referencia web; flete estimado |
| `synthetic` | Generado para pruebas o demo | Fixtures; nunca se presenta como real |
| `no_disponible` | El dato no existe o no se obtuvo | Ítem de RFQ pendiente |
| `rejected` | Descartado por regla de calidad | Cotización fuera de vigencia, spec incompatible |

**Regla dura:** un valor `synthetic` o `estimado` **no habilita** una comparación como si fuera
`observado`. El motor no bloquea la pantalla, pero marca la opción y el usuario decide.

---

## 6. Qué compara dos ofertas (comparability key)

Para que dos opciones sean comparables deben coincidir (o documentarse como equivalentes):

1. **Especificación del material** (marca/norma/calidad/presentación y su versión).
2. **Base de unidad y escala de cantidad** (no comparar toneladas con bolsas sin densidad documentada).
3. **Punto de entrega** (mismo destino; "puesto en obra" vs "retiro" son alcances distintos).
4. **Alcance fiscal** (IVA incluido/excluido, y cualquier recargo declarado).
5. **Ventana temporal** (fecha de emisión y vigencia de la oferta; y el snapshot FX aplicado).
6. **Restricciones mandantes** (calidad mínima, certificaciones exigidas) — las evalúa una persona.

Si dos ofertas no son comparables, **se muestran separadas**, no se fuerzan en un ranking.

---

## 7. Estructura de la salida

```jsonc
{
  "tool": "geologistix",
  "contract_version": "delivered-cost/0.1",
  "project": { "name": "...", "destination": "..." },
  "base_currency": "ARS",
  "fx_rates_count": 2,
  "quotes_count": 3,
  "results": [
    {
      "supplier": "Proveedor A",
      "status_dato": "observado",
      "currency_original": "USD",
      "breakdown_original": { "material": "690.00", "freight": "120000.00", ... },
      "breakdown_base": [
        { "concept": "material", "amount_base": "1066105.00", "currency_from": "USD",
          "fx_pair": "USD/ARS", "fx_date": "2026-11-05", "fx_source": "...", "fx_status": "observado" }
      ],
      "total_base": "1186105.00",
      "fx_used": [ { "pair": "USD/ARS", "rate": 1545.5, "date": "2026-11-05", ... } ],
      "comparable": true,
      "incomplete": false,
      "alerts": [],
      "rank": 1
    }
  ],
  "disclaimer": "Comparación informativa ... no certifica idoneidad técnica, legal ni ambiental."
}
```

---

## 8. Reproducibilidad

Una comparación es reproducible si queda registrado: versión de metodología (`delivered-cost/0.1`),
versión de la fórmula, snapshot FX aplicado (par/tipo/fecha/fuente), supuestos declarados,
exclusiones, alertas y el aprobador humano cuando aplica.

El motor no guarda estado: la reproducibilidad la da el **snapshot de entrada** (el JSON del caso)
más la versión del código. Versionar el caso con el resultado es el mecanismo de auditoría.

---

## 9. Límites conocidos

- No valida equivalencia técnica ni legal de materiales.
- No modela escalas de precio por volumen, descuentos escalonados ni plazos de pago (fuera de v0.1).
- No maneja múltiples destinos en un mismo caso.
- El flete se trata como monto único (no se descompone en carga/tránsito/descarga/peajes).
- La tasa FX se aplica a la fecha del caso; no hay series históricas ni forward.
- El motor no valida licencias de las fuentes: eso es responsabilidad de quien ingesta.

---

## 10. Versionado

| Versión | Cambios |
|---|---|
| `delivered-cost/0.1` | Fórmula base (material + flete + otros), conversión FX fechada, alertas de comparabilidad, ranking por comparabilidad, salida JSON/CSV/tabla. |

Cambios que alteren el significado de un campo o la semántica de comparabilidad requieren
**versión mayor** del contrato y nota de migración.
