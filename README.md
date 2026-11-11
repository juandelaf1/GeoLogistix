<p align="center">
  <img src="assets/banner.png" alt="GeoLogistix — comparador auditable de costo entregado" width="100%">
</p>

<p align="center">
  <a href="https://github.com/juandelaf1/GeoLogistix/actions/workflows/ci.yml">
    <img src="https://github.com/juandelaf1/GeoLogistix/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI" height="20">
  </a>
  <a href="https://github.com/juandelaf1/GeoLogistix/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-4FD1C5.svg" alt="License MIT" height="20">
  </a>
  <img src="https://img.shields.io/badge/python-3.10%2B-63B3ED.svg" alt="Python 3.10+" height="20">
  <img src="https://img.shields.io/badge/dependencies-0-9AE6B3.svg" alt="Zero dependencies" height="20">
  <img src="https://img.shields.io/badge/contract-delivered--cost%2F0.1-E2E8F0.svg" alt="Contract delivered-cost/0.1" height="20">
  <img src="https://img.shields.io/badge/AI-none%20by%20design-FFC857.svg" alt="No AI" height="20">
</p>

<h1 align="center">GeoLogistix</h1>

<p align="center">
  <strong>Comparador auditable de costo entregado</strong> para abastecimiento de materiales<br>
  <sub>material + flete + ajustes explícitos · conversión FX fechada · procedencia por dato</sub>
</p>

<p align="center">
  <a href="#inicio-rápido">Inicio rápido</a> ·
  <a href="#cómo-funciona">Cómo funciona</a> ·
  <a href="#integración">Integración</a> ·
  <a href="docs/METODOLOGIA.md">Metodología</a> ·
  <a href="docs/DEFINICIONES.md">Definiciones</a> ·
  <a href="docs/ARQUITECTURA.md">Arquitectura</a> ·
  <a href="docs/GOBERNANZA_DATOS.md">Gobernanza</a> ·
  <a href="docs/ROADMAP.md">Roadmap</a>
</p>

---

## Qué es

Comparar "precios" entre proveedores es engañoso: unos cotizan **sin flete**, otros **puesto en obra**; unos en **dólares** con tasa de hace un mes; las **especificaciones** no siempre son equivalentes; los **precios vencen**. Con eso, se elige por el número más visible y se descubre tarde que faltaba el flete.

**GeoLogistix resuelve ese punto de fricción con una regla mínima: un costo entregado solo es comparable si está completo.**

Es un motor **determinista** (misma entrada → mismo resultado), **sin IA**, **sin dependencias externas** y **sin red por su cuenta**: se le dan cotizaciones y devuelve la comparación con desglose, conversión fechada, supuestos a la vista y los datos que faltan declarados.

> **Lo que NO es:** no predice precios, no recomienda proveedor, no calcula rutas, no certifica idoneidad técnica/legal/ambiental, no mueve dinero y no scrapea precios por su cuenta.

## Estado honesto del proyecto

| Aspecto | Estado |
|---|---|
| Motor de comparación | ✅ Operativo, determinista, aritmética decimal (`Decimal`, sin float) |
| Contrato de salida | ✅ `delivered-cost/0.1` (JSON / CSV / tabla) |
| Regla FX + snapshots con `retrieved_at` | ✅ Operativo (BNA como fuente observada; BCRA documentado) |
| Ingesta CSV de cotizaciones | ✅ Operativo (mapeo es/en, sin inventar datos) |
| Tests | ✅ Suite unittest (17) + CI en Python 3.10/3.11/3.12 — *la ejecución en GitHub Actions estaba en cola en el momento del release; los tests pasan en local con el mismo comando (`pytest -q`)* |
| Casos reales comparables | ⚠️ **Pendiente**: faltan cotizaciones formales + flete de un caso concreto |
| Datos | 🔎 Mixto: FX **observado**, precios web **estimados**, RFQ **pendiente** — etiquetado por dato |
| Licencias de fuentes | ⚠️ Verificar ToS/licencia por fuente **antes** de automatizar ingesta |

*(Estado a 2026-11-11. Ver `docs/ROADMAP.md` para el plan y `docs/GOBERNANZA_DATOS.md` para las reglas de procedencia.)*

## Inicio rápido

```bash
git clone https://github.com/juandelaf1/GeoLogistix.git
cd GeoLogistix

# opción A: sin instalar nada (Python ≥ 3.10)
python -m geologistix compare examples/case_cemento_caba.json

# opción B: como paquete instalable
pip install -e .
geologistix compare examples/case_cemento_caba.json --format json
```

Salida (tabla):

```
Costo entregado — destino: Obra en CABA, Buenos Aires | base: ARS | cotizaciones: 3
----------------------------------------------------------------------------------------------------
#- Distribuidor A (referencia web) | Cemento portland bolsa 50 kg 100bolsa | total: 832500.00 ARS | dato: estimado | fecha: 2026-11-11 [NO COMPARABLE, incompleto]
    alertas: flete no informado (costo entregado incompleto)
#- Retail B (precio publicado)     | Cemento portland CPC40 100bolsa        | total: 973900.00 ARS | dato: estimado | fecha: 2026-11-11 [NO COMPARABLE, incompleto]
    alertas: flete no informado (costo entregado incompleto)
#- Proveedor formal [PENDIENTE RFQ] | Cemento CPC40 100bolsa                | total: N/D | dato: no_disponible | fecha: None [NO COMPARABLE, incompleto]
    alertas: precio/cantidad no disponible: material_cost incompleto; flete no informado (costo entregado incompleto)
```

> **Esto es correcto y es el punto del producto**: sin flete informado no hay "costo entregado" comparable. La herramienta no rellena el hueco con ceros ni con supuestos silenciosos.

### Comandos

```bash
# Comparar un caso (JSON con quotes[] + fx_rates[])
python -m geologistix compare caso.json                      # tabla
python -m geologistix compare caso.json --format json        # payload auditable
python -m geologistix compare caso.json --format csv         # hoja de cálculo / informe
python -m geologistix compare caso.json --strict             # exit 2 si nada es comparable

# Normalizar una observación de tipo de cambio
python -m geologistix fx --fetch                       # consulta puntual el BNA (verifica el valor)
python -m geologistix fx --file snapshot.json
python -m geologistix fx --pair USD/ARS --rate 1544.00 --date 2026-11-11 \
    --source "BNA - Divisas (Venta)" --rate-type divisa_venta --url https://www.bna.com.ar/Personas

# Convertir CSV de cotizaciones → caso JSON
python -m geologistix import examples/quotes_template.csv --out caso.json
```

## Cómo funciona

```text
1. Definir el caso        → 1 obra/destino + 1 material (spec, cantidad, unidad)
2. Registrar FX           → par + tipo + fecha + fuente + retrieved_at
3. Capturar cotizaciones  → presupuestos formales (RFQ) o referencias (CSV)
4. Comparar               → desglose, conversión, ranking, alertas
5. Decidir (humano)       → con supuestos y faltantes a la vista
```

Fórmula (por opción):

```
material_base = unit_price × quantity × fx(moneda → base)
total_base    = material_base + freight_base + other_base
```

Reglas que **no** se negocian en el código:

| Regla | Comportamiento verificable |
|---|---|
| Faltante ≠ 0 | Sin flete/precio/cantidad → alerta; nunca se asume 0 (salvo 0 explícito del usuario) |
| Comparabilidad estricta | Sin flete informado → **no comparable** como costo entregado, aunque se muestre el total parcial |
| Sin FX no hay conversión | Sin tasa fechada para el par → no comparable (`sin tasa FX USD/ARS`) |
| Moneda original inmutable | Se conserva precio y moneda originales; la conversión es capa aparte con su snapshot |
| Procedencia por dato | Cada opción declara `observed \| derived \| estimated \| synthetic \| no_disponible \| rejected` + `source`, `date`, `valid_until`, `evidence_ref` |
| Aritmética decimal | `Decimal` (precisión 28), `ROUND_HALF_UP` a 2 decimales. Sin float binario para dinero |
| Ranking honesto | Comparables primero por total; los no comparables quedan fuera (`rank = null`) con alerta visible |
| Determinismo | Sin red, sin IA, sin aleatoriedad: mismos datos → mismo resultado |

Detalle completo en [`docs/METODOLOGIA.md`](docs/METODOLOGIA.md) y glosario en [`docs/DEFINICIONES.md`](docs/DEFINICIONES.md).

## Integración en cualquier plataforma

GeoLogistix es una **librería + CLI**, no un servicio acoplante. Se integra como motor de cálculo detrás de la API de tu plataforma: **sin base de datos compartida, sin modelos de dominio comunes, sin acoplar tu arquitectura**.

<details open>
<summary><b>Python (FastAPI / Flask / Django / Streamlit)</b></summary>

```python
from fastapi import FastAPI
from geologistix import compare, FxRate, Quote

app = FastAPI()

@app.post("/api/delivered-cost/compare")
def comparar(payload: dict):
    # payload: {project, base_currency, fx_rates[], quotes[]}
    from geologistix.io import load_case  # o mapea dicts a Quote/FxRate
    ...
    return compare(
        quotes=[Quote(**q) for q in payload["quotes"]],
        fx_rates=[FxRate(**f) for f in payload["fx_rates"]],
        base_currency=payload.get("base_currency", "ARS"),
        project=payload.get("project"),
    )
```

</details>

<details>
<summary><b>Node.js / Express / Next.js</b></summary>

```js
// Expón el motor como micro-servicio Python mínimo y consúmelo por HTTP,
// o replica la fórmula en TS Decimal (misma especificación: delivered-cost/0.1).
const res = await fetch("http://geologistix:8080/compare", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ base_currency: "ARS", fx_rates, quotes }),
});
const { results } = await res.json();
```

</details>

<details>
<summary><b>Java / Kotlin / Go / C#</b></summary>

El contrato es JSON estable (`delivered-cost/0.1`). Consumir el motor como servicio HTTP
y mapear `quotes[]` / `fx_rates[]` con los mismos nombres de campo. Al calcular de forma nativa,
aplicar la misma especificación: aritmética decimal, redondeo `HALF_UP` a 2 decimales, y las
mismas reglas de comparabilidad y alertas (ver `docs/METODOLOGIA.md`).

</details>

<details>
<summary><b>Integración como módulo acoplado (Poolar y otros)</b></summary>

Niveles sugeridos (contrato versionado, sin fusión de dominios):

- **L0 — referencia/documentación:** publicar el contrato `delivered-cost/0.1` y la metodología.
- **L1 — consulta/evaluación:** el consumidor (p. ej. Poolar como pilar de cooperación) aporta el
  caso y los actores; GeoLogistix devuelve la comparación de costo como **evidencia**, con sus
  supuestos. La decisión sigue siendo humana y del consumidor.

</details>

Contrato, semántica de campos y checklist de integración: [`docs/INTEGRACION.md`](docs/INTEGRACION.md).

## Estructura del proyecto

```text
geologistix/                 # paquete Python (0 dependencias)
├─ model.py                  # Quote, FxRate, QuoteResult, estados de evidencia
├─ fx.py                     # conversión con observación FX fechada
├─ compare.py                # motor determinista + renderers (tabla/JSON/CSV)
├─ io.py                     # carga/normalización JSON/CSV (nunca inventa datos)
├─ ingest.py                 # snapshot FX (consulta puntual BNA) con procedencia
└─ cli.py                    # CLI: compare | fx | import
docs/
├─ METODOLOGIA.md            # cómo se calcula, invariantes y límites
├─ DEFINICIONES.md           # glosario (costo entregado, comparable, procedencias…)
├─ ARQUITECTURA.md           # capas, contrato, fronteras de dominio
├─ INTEGRACION.md            # integrar en FastAPI/Express/otras plataformas
├─ GOBERNANZA_DATOS.md       # tiers, procedencia, frescura, derechos de uso
├─ FUENTES.md                # fichas de fuentes (BNA, BCRA, RFQ, web, índices)
└─ ROADMAP.md                # gates y backlog priorizado
examples/                    # caso de ejemplo + plantilla CSV
tests/                       # suite unittest (sin deps)
assets/                      # banner (SVG + PNG)
```

## Metodología en una línea

**Evidencia antes que narrativa**: cada cifra es `observada` (fuente verificable y fechada),
`derivada` (calculada), `estimada` (declarada) o **no está** (y se dice). El comparador no ranks
opciones incomparables porque un número sin flete, sin spec o sin tasa fechada es una cifra, no
una decisión.

## Contribuir

Lee [`docs/GOBERNANZA_DATOS.md`](docs/GOBERNANZA_DATOS.md) y [`CONTRIBUTING.md`](CONTRIBUTING.md).
Reglas no negociables: no inventar cotizaciones, tasas, permisos ni beneficios; no degradar un
dato faltante a 0; no certificar idoneidad técnica/legal/ambiental; no subir datos personales,
secretos o datasets sin licencia.

## Licencia

MIT © 2026 [Juan de la Fuente](https://github.com/juandelaf1) — ver [`LICENSE`](LICENSE).
