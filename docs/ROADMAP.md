# Roadmap y gates — GeoLogistix

> Priorizado. Un ítem se marca hecho solo con evidencia (commit + test + salida observada).
> Fecha de corte: 2026-11-11.

---

## 1. Hecho (verificado)

- [x] Motor de comparación determinista (`geologistix/compare.py`), aritmética `Decimal` (prec. 28, `HALF_UP`) — *v0.1*
- [x] Contrato de salida `delivered-cost/0.1` con JSON / CSV / tabla
- [x] Reglas de comparabilidad: faltante ≠ 0, comparabilidad estricta, sin FX no hay conversión, ranking solo de comparables
- [x] Módulo FX con observación fechada y soporte de par inverso (`derived`)
- [x] Estados de evidencia (`observed/derived/estimated/synthetic/no_disponible/rejected`)
- [x] Capa de entrada: JSON y CSV → modelos, sin inventar datos (`geologistix/io.py`)
- [x] CLI (`compare`, `fx`, `import`) con código de salida 2 en modo `--strict`
- [x] Suite de tests (unittest, sin deps) + CI en Python 3.10/3.11/3.12
- [x] Documentación: metodología, definiciones, arquitectura, integración, gobernanza, fuentes
- [x] Banner (SVG + PNG), README profesional, `LICENSE` MIT, `pyproject.toml` instalable
- [x] Ejemplo reproducible con FX **observado** (BNA) + precios web **estimados** + RFQ **pendiente**

---

## 2. En curso / siguiente

| # | Ítem | Dependencia | Notas |
|---|---|---|---|
| R1 | **Caso real comparable**: 1 obra + 1 material + ≥2 presupuestos formales con flete | Acción externa (RFQ) | Sin esto el producto no tiene evidencia de uso real |
| R2 | Fijar regla FX del caso (fuente, tipo, fecha de corte) y versionarla | Decisión | Ya documentada en `FX_RULE.md`; falta aplicarla al caso real |
| R3 | Fichas de fuente con verificación de licencia/Términos | Revisión | `docs/FUENTES.md` marca "verificar" |
| R4 | Importador de FX recurrente (con ToS aprobado y parser robusto) | R3 | Hoy: puntual + manual |
| R5 | Tests de equivalencia para reimplementaciones en otros lenguajes | Opcional | Documentados en `INTEGRACION.md` §6 |
| R6 | Versionar el contrato de entrada/salida en registro público | Opcional | Hoy: `delivered-cost/0.1` |

---

## 3. Backlog (cuando haya evidencia de necesidad)

- [ ] Descomposición de flete (carga / tránsito / descarga / peajes) — requiere modelo de transporte, no una tarifa universal
- [ ] Escalones de precio por volumen y plazos de pago (fuera del motor actual)
- [ ] Múltiples destinos en un mismo caso
- [ ] Series históricas de FX y escenarios de sensibilidad
- [ ] Identificador de material y catálogo normalizado (con criterios de equivalencia documentados)
- [ ] UI mínima (hoy: CLI + librería) — solo si el público no técnico lo necesita
- [ ] Exportación a formatos contables (sujeto a revisión fiscal humana)

---

## 4. Fuera de alcance (por diseño)

Rutas y tiempos de tránsito · predicción de precios · scoring de riesgo de proveedor ·
certificación técnica/legal/ambiental · RAG/agentes para decidir · ejecución de pagos ·
economía circular y materiales secundarios · multi-tenant · base de datos propia ·
fusión de dominios con otros productos del ecosistema.

---

## 5. Gates

| Gate | Criterio de avance |
|---|---|
| **G1 — Evidencia real** | ≥2 ofertas `observed`, flete informado, spec equivalente, snapshot FX fechado → **primera comparación comparable** |
| **G2 — Uso operativo** | Regla FX aprobada + fichas de fuente validadas + permisos de uso confirmados + caso archivado |
| **G3 — Integración** | ≥1 consumidor externo usando el contrato `delivered-cost/0.1` con tests de equivalencia |
| **G4 — Escala** | CI verde, contrato versionado, documentación de cambios, sin deuda técnica abierta sin registrar |

---

## 6. Riesgos abiertos

| Riesgo | Impacto | Mitigación actual |
|---|---|---|
| No hay cotizaciones formales todavía | El producto no puede usarse de verdad | Todo marcado `estimated`/`no_disponible`; output honesto y no comparable |
| Términos/licencias sin verificar | Ingesta automatizada ilegal | Ingesta puntual y manual; verificación pendiente antes de automatizar |
| Fragmentación del parser BNA | Snapshot FX puede fallar | Modo `--manual` y warnings explícitos; nunca valor inventado |
| Equivalencia de specs no validada | Comparación engañosa | El motor no valida specs; lo hace una persona, y se documenta la clave de comparabilidad |
| Presión por "comparar algo ya" | temptation de rellenar con ceros | Invariante R1 en código y tests que lo fijan |
