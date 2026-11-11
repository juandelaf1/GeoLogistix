# GeoLogistix — Informe del producto: comparador de costo entregado

> **Fecha:** 2026-11-11 · **Alcance:** `GeoLogistix/` (workspace local, sin repo git propio) · **Estado:** MVP determinista operativo, con ingesta asistida y gobernanza de datos.  
> **Qué es:** una sola cosa útil — comparar opciones de abastecimiento de materiales por **costo entregado auditable**. Nada más.

---

## 1. Resumen en una frase

**GeoLogistix (foco activo) es un comparador de costo entregado**: le das cotizaciones de material y te dice cuál sale más barato **en la obra, con tu moneda y tu tasa del día**, mostrando el desglose, de dónde sale cada número y qué datos faltan para poder decidir.

No es un chatbot, no predice precios, no certifica materiales ni legality, no scrapea nada por su cuenta, no mueve dinero.

---

## 2. El problema que resuelve

En una obra, comparar "precios" entre proveedores es engañososo:
- unos cotizan **sin flete**, otros **puesto en obra**;
- unos cotizan en **dólares** y otros en **pesos**, con tasas de días distintos;
- las **especificaciones** no siempre son equivalentes (marca, norma, peso de bolsa);
- los **precios vencen** y no se sabe si el precio “sin impuestos” es comparable con el precio “con IVA”.

El resultado habitual: se elige por el número más visible y se descubre tarde que faltaba el flete o que no eran el mismo producto.

**GeoLogistix resuelve exactamente ese punto de fricción**, con la regla mínima: *un costo entregado solo es comparable si está completo* (material + flete informado + conversión con tasa fechada + especificación equivalente).

---

## 3. Cómo funciona (mecánica)

### 3.1 Flujo de trabajo

```text
1. Definir el caso      → 1 obra/destino + 1 material (spec, cantidad, unidad)
2. Capturar FX          → regla FX + snapshot fechado (tools/record_fx.py)
3. Capturar cotizaciones→ presupuestos formales (RFQ) o referencias (CSV)
4. Comparar             → compare.py  (desglose, conversión, ranking, alertas)
5. Decidir (humano)     → con supuestos y faltantes a la vista
```

### 3.2 El cálculo (determinista, sin IA)

Por cada cotización:

```
material        = unit_price × quantity
material_base   = material        × fx(moneda → base)      [tasa fechada]
freight_base    = freight_cost    × fx(moneda_flete → base)
other_base      = other_costs     × fx(moneda → base)
total_base      = material_base + freight_base + other_base
```

Criterios que **no** se negocian en el código:

| Regla | Comportamiento |
|---|---|
| **Faltante ≠ 0** | Si falta flete/precio/cantidad → alerta `flete no informado` / `material_cost incompleto`. Nunca se asume 0. |
| **Comparabilidad estricta** | Una opción sin flete informado **no** es comparable como “costo entregado” (aunque el total parcial se muestre). |
| **Sin FX no hay conversión** | Si falta tasa para una moneda, la conversión falla y la opción queda no comparable (`sin tasa FX USD/ARS`). |
| **Moneda original inmutable** | Se conserva precio y moneda originales; la conversión es una capa aparte con su snapshot. |
| **Procedencia explícita** | Cada opción trae `status` (`observado|estimado|no_disponible`), `source`, `date`, `valid_until`, `evidence_ref`. |
| **Aritmética decimal** | `Decimal` (precisión 28), redondeo `ROUND_HALF_UP` a 2 decimales. Sin float binario para dinero. |
| **Ranking honesto** | Ordena comparables por total; los no comparables quedan fuera del ranking (`rank = null`) con su alerta visible. |

### 3.3 Salidas

| Formato | Uso |
|---|---|
| **Tabla** (stdout) | Lectura rápida en reunión: ranking, total, estado del dato, fecha, alertas. |
| **JSON** (`--format json`) | Evidencia auditable: desglose por concepto, par/fecha FX usada, `fx_used`, cobertura, supuestos. |
| **CSV** (`--format csv`) | Hoja de cálculo / informe de obra: una fila por opción con alertas y notas. |

Contrato de salida: `contract_version: delivered-cost/0.1`, `tool`, `base_currency`, `procedencia`, `pii: none` (los agregados no llevan datos personales).

---

## 4. Componentes

```text
GeoLogistix/
├─ README.md                          ← estado honesto del workspace
├─ AUDIT_INFORME_FUENTES_INGESTA.md   ← auditoría + mapa de fuentes internet para ingesta
├─ INFORME_PRODUCTO_COSTO_ENTREGADO.md← este informe
└─ costo-entregado-mvp/               ← el producto (módulo autónomo)
   ├─ compare.py                      ← motor de comparación (Python stdlib, sin deps)
   ├─ FX_RULE.md                      ← regla de tipo de cambio (fuente/tipo/fecha)
   ├─ CHECKLIST_CAPTURA_DATOS.md      ← qué pedir a proveedor/transportista
   ├─ input_template_real.json        ← plantilla de caso real (procedencia/vigencia)
   ├─ example_input.json              ← ejemplo de prueba
   ├─ tools/
   │   ├─ record_fx.py                ← snapshot FX (fetch BNA best-effort o manual)
   │   └─ import_quotes_csv.py        ← CSV de cotizaciones → quotes[] canónicos
   ├─ source_cards/                   ← ficha por fuente (licencia/ToS, campos, riesgos)
   │   ├─ BNA_FX.md · BCRA_FX.md · PROVEEDORES_RFQ.md
   │   └─ REFERENCES... INDICES_CONTEXTO.md
   ├─ fx_snapshots/                   ← snapshots con retrieved_at + evidencia
   ├─ references/                     ← precios indicativos (SIEMPRE estimados)
   └─ casos/                          ← plantilla + casos + resultados (JSON/CSV)
```

Fuera de esta carpeta, como **referencia** (no implementadas): `geo-abastecimiento-ar/` (spec v0.2: gobernanza de datos, requisitos, ADR, backlog, auditoría de reutilización) y `geologistix_foundation/` (v0.1 histórica).

---

## 5. Ingesta de datos (cómo entra la información)

### 5.1 Flujos y estados

| Flujo | Estado del dato | Herramienta | Resultado |
|---|---|---|---|
| **Tipo de cambio** | `observado` (fuente publicada, fechada) o `estimado` (regla acordada) | `tools/record_fx.py` | Snapshot con `retrieved_at`, fuente, URL, fecha publicada, 4 tasas (billete/divisa × compra/venta) y selección por regla |
| **Cotizaciones formales (RFQ)** | `observado` (presupuesto escrito, con vigencia y evidencia) | captura manual → `input_template_real.json`; o CSV → `tools/import_quotes_csv.py` | `quotes[]` con proveedor, spec, precio/moneda, flete, inclusiones, vigencia, `evidence_ref` |
| **Precios web de referencia** | `estimado` (indicativos; **nunca** cotización firme) | `references/indicative_prices_template.csv` + importador con `--status estimado` | Contexto/rango; suficiente para exploration, insuficiente para decidir |
| **Flete/entrega** | `observado` (cotización transporte o condición del proveedor) | mismo flujo de cotizaciones | Sin flete → la opción **no es comparable** (correcto) |
| **Índices/contexto (INDEC, cámaras)** | `derivado`/contexto | fuera del comparador hoy | Contexto macro, no precio transable |

### 5.2 Reglas de la ingesta

1. **Procedimiento antes que automatización**: cada fuente tiene `source_card` (owner, URL, campos, cobertura, actualización, formato, **licencia/ToS a verificar**, límites, riesgos, método de extracción). Automatizar sin validar términos =Incumplimiento.
2. **Sin datos inventados**: faltante = `null` + estado explícito (`no_disponible`). Nada de ceros silenciosos ni valores sintéticos presentados como reales.
3. **Idempotencia y trazabilidad**: cada snapshot lleva `retrieved_at`; cada cotización, `source` + `evidence_ref` + vigencia.
4. **Fail-safe**: error de fetch/parse → warning explícito + fallback a modo manual (`--manual`), nunca un valor “creíble” inventado.
5. **Sin PII/secretos**: el comparador es de datos de costo, no de personas; nada de datos personales ni claves en repo, logs o salidas.

---

## 6. Estado verificado del trabajo (evidence snapshot)

| Elemento | Estado | Evidencia |
|---|---|---|
| Motor de comparación | **Operativo** | `compare.py` ejecutado: ejemplo, caso real y referencia importada |
| Regla FX + snapshot | **Operativo** | `FX_RULE.md`; `fx_snapshots/fx_USD-ARS_20261111T125500Z.json` (BNA, publicado 2026-11-05: billete 1520.00/1570.00, divisa 1536.50/1545.50; selección `divisa_venta` 1545.50) |
| Importador CSV | **Operativo** | `import_quotes_csv.py` importó 1 quote y el comparador lo procesó |
| Plantillas/checklist | **Listos** | `input_template_real.json`, `casos/caso_real_plantilla.json`, `CHECKLIST_CAPTURA_DATOS.md` |
| Source cards | **5 fichas** | BNA, BCRA, RFQ/proveedores, referencias web, índices/contexto |
| Caso real creado | **Ejecutado, NO comparable** | `casos/caso_real_2026-11-11_cemento_caba.json` + resultados JSON/CSV: 3 opciones, 2 con precios web `estimado`, 1 `no_disponible` (RFQ pendiente), **flete no informado en todas** → `NO COMPARABLE/incompleto` |
| Parser FX | **Corregido y verificado** | Parsea `#billetes`/`#divisas` por separado (fallback por orden de aparición) |
| Informe de fuentes | **Listo** | `AUDIT_INFORME_FUENTES_INGESTA.md` (requisitos, brechas, viabilidad por fuente, backlog I-01…I-05, riesgos) |
| Tests/CI automatizados | **No** | El MVP es un script determinista simple; no hay suite ni CI en esta carpeta |
| Repo git propio | **No** | `GeoLogistix/` es carpeta de trabajo; cambios locales (no versionados) |

---

## 7. Qué falta para que el producto sea operativo de verdad

| # | Pendiente | Por qué bloquea | Quién/qué |
|---|---|---|---|
| 1 | **≥2 cotizaciones formales** (RFQ) del mismo material/spec/cantidad/destino | Sin `observado` real, todo queda `estimado` | Acción externa (contacto con proveedores) |
| 2 | **Flete / condición de entrega** por oferta | Sin flete, no hay costo entregado comparable | Acción externa (proveedor/transportista) |
| 3 | **Dirección exacta de obra** | Flete depende del destino; condición de entrega, del alcance | Acción externa |
| 4 | Confirmar **IVA incluido/excluido** y equivalencia de specs | Sin homogeneidad, la comparación miente | Acción externa |
| 5 | Snapshot FX del **día de comparación** (regla ya definida) | Tasas cambian; comparar con tasa vieja distorsiona | `tools/record_fx.py` (1 comando) |
| 6 | Tests offline + CI del comparador | Regresiones en el motor de cálculo | Trabajo interno (siguiente lote) |
| 7 | Versionar el módulo (repo propio) o integrarlo como carpeta con historia | Cambios locales sin trazabilidad | Decisión de gobernanza |

---

## 8. Cómo usarlo (comandos)

```bash
cd costo-entregado-mvp

# 1) Snapshot de FX (verifica el valor; usa --manual si el parser falla o la fuente cambió)
python tools/record_fx.py --outdir fx_snapshots
python tools/record_fx.py --manual --type divisa_venta --rate 1545.50 --date 2026-11-05 --note "BNA published" --outdir fx_snapshots

# 2) Importar cotizaciones (CSV normalizado) uniendo el snapshot de FX
python tools/import_quotes_csv.py quotes.csv --fx-json fx_snapshots/<snapshot>.json --out casos/mi_caso.json

# 3) Comparar
python compare.py casos/mi_caso.json
python compare.py casos/mi_caso.json --format json --out casos/mi_caso_resultado.json
python compare.py casos/mi_caso.json --format csv  --out casos/mi_caso_resultado.csv
```

Semántica del ranking: **comparables primero (menor total)**, no comparables al final con `rank = null` y alerta visible. `compare.py` usa solo la biblioteca estándar (Python 3.10+).

---

## 9. Límites y límites éticos (deliberados)

- **No** calcula rutas/distancias, **no** predice precios futuros, **no** recomienda proveedor, **no** certifica idoneidad técnica/legal/ambiental.
- **No** scrapea automáticamente: la extracción FX es puntual y best-effort, y toda fuente web de precios queda como `estimado`.
- **No** confunde precio de referencia con cotización firme.
- **No** inventa FX, flete, precios ni condiciones; lo faltante se declara.
- **No** fusiona dominios: es un módulo autónomo, acoplable por contrato (L0/L1) a Poolar u otros sin compartir base de datos ni modelos.

---

## 10. Encaje en el ecosistema (Poolar)

- **Rol posible:** proveedor de evidencia/comparación de costo, como módulo acoplado **L0/L1** (contrato versionado).
- **Frontera de autoridad:** Poolar aporta el caso, los actores y la decisión; GeoLogistix devuelve la comparación con su desglose y supuestos. La decisión es humana.
- **Sin claims indebidos:** no se afirma ahorro, impacto ambiental ni superioridad de proveedor; el producto expone números y supuestos, y el usuario decide.

---

## 11. Conclusión

GeoLogistix está hoy en un estado coherente y útil: **el motor de comparación funciona, la ingesta tiene reglas y herramientas, la procedencia está trazada y el caso real está creado con honestidad** (FX observado, precios web etiquetados como estimados, RFQ y flete declarados como faltantes, resultado marcado no comparable).

Lo que falta no es tecnología: son **dos o tres presupuestos formales y el flete** de un caso concreto. Con eso, el mismo comparador entrega su primera comparación válida — sin una sola línea de código adicional.
