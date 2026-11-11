# Integración — cómo usar GeoLogistix en cualquier plataforma

> Objetivo: usar el motor de costo entregado **dentro** de tu arquitectura, sin que se imponga
> una base de datos, un framework ni un modelo de dominio ajeno.

---

## 1. Principios de integración

1. **Librería primero.** El paquete es importable y la CLI es una envoltura fina. Si tu plataforma
   es Python, no necesitas ningún proceso extra.
2. **Sin base de datos compartida.** GeoLogistix no persiste nada. Quien llama, guarda el caso y el
   resultado (si quiere auditabilidad).
3. **Sin modelo de dominio común.** Usa tus propias entidades; mapea a `Quote` / `FxRate` en el borde.
4. **Contrato versionado.** `delivered-cost/0.1`. Versiona el contrato al integrarlo; si evoluciona,
   communicates la versión.
5. **Sin decisión automática.** El motor devuelve números, desglose y alertas. La decisión es de tu
   aplicación/humano.
6. **Sin credenciales en el motor.** No hay API keys ni sesiones: la autenticación es responsibility
   de tu plataforma.

---

## 2. Opciones de despliegue

| Opción | Cuándo | Qué implica |
|---|---|---|
| **A. Importar la librería** | Backend en Python (FastAPI, Flask, Django, Streamlit) | Latencia mínima, sin red, sin proceso extra |
| **B. CLI como proceso batch** | Jobs programados (cron, Airflow, GitHub Actions) | `python -m geologistix compare caso.json --format json > out.json` |
| **C. Micro-servicio HTTP** | Backend en otro lenguaje, o necesidad de aislamiento | Envolver la librería en un servicio mínimo; contrato JSON estable |
| **D. Replicar la fórmula** | Requisito de latencia extremo o lenguaje con decimal nativo | Misma especificación (`METODOLOGIA.md`); tests de equivalencia contra el motor |

---

## 3. Opción A — importar la librería (Python)

```python
from geologistix import compare, FxRate, Quote
from decimal import Decimal

payload = compare(
    quotes=[
        Quote(
            supplier="Proveedor A",
            material="Cemento portland CPC40",
            spec="50 kg",
            quantity=Decimal("100"),
            unit="bolsa",
            unit_price=Decimal("8200"),
            currency="ARS",
            freight_cost=Decimal("180000"),      # puesto en obra
            freight_currency="ARS",
            date="2026-11-11",
            valid_until="2026-11-25",
            source="Presupuesto formal P-0001",
            status="observed",                  # o "observed"/"estimated"/"no_disponible"
            evidence_ref="presupuestos/P-0001.pdf",
        )
    ],
    fx_rates=[
        FxRate(
            pair="USD/ARS",
            rate=Decimal("1545.50"),
            date="2026-11-05",
            source="BNA - Divisas (Venta)",
            status="observed",
            rate_type="divisa_venta",
            url_or_ref="https://www.bna.com.ar/Personas",
            retrieved_at="2026-11-11T12:55:00Z",
        )
    ],
    base_currency="ARS",
    project={"name": "Obra centro", "destination": "CABA"},
)

results = payload["results"]
best = next((r for r in results if r["rank"] == 1), None)
```

Claves útiles del resultado: `results[].rank`, `.comparable`, `.incomplete`, `.alerts`,
`.total_base`, `.breakdown_base[]`, `.fx_used[]`.

### Mapeo desde tus entidades

```python
from geologistix.io import quote_from_dict, fx_from_dict

quote = quote_from_dict(mi_entidad.to_dict())   # acepta claves del contrato
```

---

## 4. Opción B — CLI en jobs

```bash
# 1) construir el caso (JSON) desde tu fuente
python -m geologistix import cotizaciones.csv --out caso.json

# 2) registrar FX del día
python -m geologistix fx --pair USD/ARS --rate 1545.50 --date 2026-11-05 \
    --source "BNA - Divisas (Venta)" --rate-type divisa_venta --out fx.json

# 3) comparar y archivar resultado (pares caso+resultado = evidencia)
python -m geologistix compare caso.json --fx fx.json --format json --out resultado.json
```

**Código de salida:** `0` ok · `1` error de uso/entrada · `2` (`--strict`) ninguna opción comparable.
Ideal para **fallar el pipeline** cuando la evidencia no alcanza.

---

## 5. Opción C — micro-servicio HTTP

Envoltorio mínimo (Python, sin framework extra necesario):

```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from geologistix import compare
from geologistix.io import load_fx_rates, load_quotes

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/compare":
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        out = compare(
            quotes=load_quotes(body),
            fx_rates=load_fx_rates(body),
            base_currency=body.get("base_currency", "ARS"),
            project=body.get("project"),
        )
        payload = json.dumps(out, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

HTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
```

Cliente Node/TS:

```ts
const res = await fetch("http://geologistix:8080/compare", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ base_currency: "ARS", fx_rates, quotes }),
});
const { results } = await res.json();
const best = results.find((r) => r.rank === 1);
```

Cliente Java/Go/C#: mismo contrato JSON; mapear `quotes[]` y `fx_rates[]` con los nombres de campo
de `docs/DEFINICIONES.md`.

---

## 6. Opción D — replicar la fórmula

Especificación mínima a replicar (ver `METODOLOGIA.md` para el detalle y los casos límite):

1. Decimal con precisión ≥ 28; redondeo `HALF_UP` a 2 decimales en el total en moneda base.
2. `total = material×qty + freight + other`, cada uno convertido a moneda base con la tasa fechada.
3. `comparable = material_total_existe && flete_informado && conversion_completa`.
4. Sin tasa aplicable → no comparable; nunca tasa implícita.
5. No comparables → `rank = null`, con alerta legible.
6. Preservar moneda y monto originales; registrar par/fecha/fuente de cada conversión.

**Regla de equivalencia:** toda reimplementación debe pasar los mismos casos que
`tests/test_compare.py` (arithmetic, missing freight, missing FX, ranking, estados).

---

## 7. Checklist de integración

- [ ] ¿Tu plataforma es Python? → Opción A (sin proceso extra).
- [ ] ¿Necesitas el resultado en un job? → Opción B con `--strict` para fallar el pipeline.
- [ ] ¿Backend en otro lenguaje? → Opción C (micro-servicio) o D (replicar + tests de equivalencia).
- [ ] ¿Quién aporta FX? → tu plataforma registra la observación (fecha, tipo, fuente) y la pasa.
- [ ] ¿Quién valida specs equivalentes? → un humano cualificado, no el motor.
- [ ] ¿Se guardan PII o datos confidenciales en el caso? → no: el motor solo necesita costo, spec y
      ubicación; aplica minimización y control de acceso en tu plataforma.
- [ ] ¿Se versiona el contrato? → anota `contract_version` en tus respuestas y en tus logs.
- [ ] ¿Se archiva el par caso+resultado? → para reproducibilidad y auditoría.

---

## 8. Uso como módulo acoplado (niveles)

| Nivel | Qué significa | Qué expone GeoLogistix |
|---|---|---|
| **L0** | Referencia/documentación | Contrato `delivered-cost/0.1` + metodología + definiciones |
| **L1** | Consulta/evaluación | El consumidor aporta caso y datos; GeoLogistix devuelve comparación con alertas y supuestos. **Sin** ejecución de acciones ni datos reales del consumidor |
| **L2** | Operaciones delegadas | **No aplica en v0.1**: requeriría autorización explícita, idempotencia y reconciliación |

Frontera de autoridad: el motor **evalúa y evidencia**; el consumidor **decide**. Un score o
comparación nunca sustituye certificación técnica, legal ni ambiental.
