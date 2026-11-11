# Arquitectura — GeoLogistix

> Principios: multipilar/autónomo, contratos versionados, sin base de datos compartida, sin fusiones
> de dominio, determinismo en el núcleo.

---

## 1. Vista en capas

```text
┌──────────────────────────────────────────────────────────────┐
│  Capas de consumo (otras plataformas)                        │
│  FastAPI · Express · Django · Streamlit · job batch · CLI   │
└───────────────┬──────────────────────────────────────────────┘
                │ contrato delivered-cost/0.1 (JSON)
┌───────────────▼──────────────────────────────────────────────┐
│  Adaptadores de entrada            (geologistix.io)         │
│  JSON ↔ Quote/FxRate · CSV ↔ Quote · normalización          │
│  · no inventan datos · vacíos → ausentes + estado           │
└───────────────┬──────────────────────────────────────────────┘
┌───────────────▼──────────────────────────────────────────────┐
│  Dominio de cálculo                 (compare.py · fx.py)     │
│  · desglose · conversión FX fechada · comparabilidad        │
│  · ranking · alertas · Decimal (prec. 28, HALF_UP)          │
│  · determinista, sin red, sin IA, sin persistencia          │
└───────────────┬──────────────────────────────────────────────┘
┌───────────────▼──────────────────────────────────────────────┐
│  Renderers (tabla · JSON · CSV)         (compare.py)         │
└──────────────────────────────────────────────────────────────┘
```

`model.py` define los tipos (`Quote`, `FxRate`, `QuoteResult`) y los estados de evidencia;
`cli.py` es la envoltura de línea de comandos; `__main__.py` habilita `python -m geologistix`.

---

## 2. Módulos

| Módulo | Responsabilidad | Dependencias |
|---|---|---|
| `geologistix/model.py` | Tipos de dominio y estados de evidencia | — |
| `geologistix/fx.py` | Búsqueda de tasa aplicable y conversión | `model` |
| `geologistix/compare.py` | Evaluación, comparabilidad, ranking, renderers | `model`, `fx` |
| `geologistix/io.py` | Normalización JSON/CSV → modelos | `model` |
| `geologistix/ingest.py` | Snapshot FX (consulta puntual BNA) con procedencia y modo manual | `model` |
| `geologistix/cli.py` | Interfaz de línea de comandos | `compare`, `io`, `ingest`, `model` |

**Sin dependencias externas.** Solo biblioteca estándar. `pytest` es solo para desarrollo.

---

## 3. Contrato de entrada/salida

**Entrada** (`--input`): JSON con

```jsonc
{
  "project": { "name": "...", "destination": "..." },
  "base_currency": "ARS",
  "fx_rates": [ { "pair": "USD/ARS", "rate": 1545.5, "date": "2026-11-05",
                  "source": "...", "status": "observed", "rate_type": "divisa_venta",
                  "url_or_ref": "...", "retrieved_at": "..." } ],
  "quotes": [ { "supplier": "...", "quantity": 100, "unit_price": 8200, "currency": "ARS",
                "freight_cost": 180000, "freight_currency": "ARS", "date": "2026-11-11",
                "status": "observed", "source": "...", "evidence_ref": "..." } ]
}
```

**Salida**: `delivered-cost/0.1` (ver `METODOLOGIA.md` §7). Aditiva por defecto.

---

## 4. Fronteras de dominio (no negociables)

- **Sin base de datos.** El motor no persiste; el consumidor decide si archiva el par caso+resultado.
- **Sin modelos de dominio universales.** `Quote`/`FxRate` son tipos de entrada del motor, no un
  modelo compartido entre repos.
- **Sin red en el núcleo.** La única E/S externa es una CLI opcional para registrar FX (best-effort).
- **Sin IA en el cálculo.** Un LLM puede *extraer* campos de un documento (marcado como
  `machine-extracted`, pendiente de verificación), pero nunca calcula ni sustituye la aritmética.
- **Sin sustituto de certificación.** Ningún output es validación técnica, legal, fiscal ni ambiental.

---

## 5. Decisiones (ADR-light)

| # | Decisión | Alternativas descartadas | Motivo |
|---|---|---|---|
| D1 | Núcleo determinista sin IA | LLM que "evalúa" ofertas | Auditabilidad y reproducibilidad; el LLM no es verificable |
| D2 | Cero dependencias en runtime | pandas/numpy | Portabilidad, instalación trivial, aritmética decimal explícita |
| D3 | Sin persistencia | SQLite/Postgres local | Evita base de datos compartida y simplifica la integración |
| D4 | Faltante ≠ 0 (0 solo explícito) | Asumir 0 y avisar después | Un total silenciosamente incompleto es peor que un hueco visible |
| D5 | Ranking solo de comparables | Rankear todo con penalización artificial | Un rank con supuestos ocultos induce decisiones erróneas |
| D6 | Contrato JSON aditivo | Acoplar a un ORM de dominio | Compatibilidad entre plataformas distintas |
| D7 | CLI + librería | Servicio con API propia obligatoria | Que cada plataforma elija su forma de exponerlo |

---

## 6. No objetivos

Rutas/tiempos de tránsito · precios volumes/escalones · plazos de pago y crédito · multi-destino ·
series históricas de FX · scoring de riesgo de proveedor · UI propia · multi-tenant · sincronización
de catálogos.

---

## 7. Extensión (futuro, requiere ADR)

| Candidate | Nota |
|---|---|
| Descomposición de flete (carga/tránsito/descarga/peajes) | Requiere modelo de transporte; no asumir una tarifa universal |
| Escalones de precio por volumen | Requiere evidencia de contrato con el proveedor |
| Normalización de catálogo de materiales | Requiere identificador de material y criterios de equivalencia documentados |
| Importador de FX recurrente | Solo tras verificar ToS/licencia y robustez del parser |
| UI mínima | Solo si el público no técnico lo necesita (hoy: CLI + librería) |
