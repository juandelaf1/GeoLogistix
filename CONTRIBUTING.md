# Cómo contribuir

Gracias por querer mejorar GeoLogistix. Las reglas de abajo existen para que el proyecto siga siendo
**auditable**: un número sin procedencias o un supuesto silencioso valen menos que un hueco declarado.

## Reglas no negociables

1. **No inventar** cotizaciones, tipos de cambio, fletes, permisos, capacidades ni beneficios ambientales.
2. **No degradar un dato faltante a 0** (salvo 0 explícito del usuario). Un vacío declarado vale más
   que un total engañosamente completo.
3. **No** presentar una comparación o score como certificación técnica, legal, fiscal ni ambiental.
4. **No** dejar que un precio menor anule una restricción técnica, legal o de seguridad.
5. **No** subir secretos, datos personales, cotizaciones confidenciales ni datasets sin licencia.
6. **No** enviar datos sensibles a un proveedor de modelos sin decisión aprobada.
7. El **núcleo es determinista**: sin IA, sin red, sin aleatoriedad en el cálculo.
8. Cambios que alteren la semántica del contrato requieren **versión mayor** + nota de migración.

## Flujo de trabajo

```bash
git clone https://github.com/juandelaf1/GeoLogistix.git && cd GeoLogistix
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -e ".[dev]"

python -m pytest -q                 # tests
python -m geologistix compare examples/case_cemento_caba.json   # smoke
```

Antes de abrir un PR:

- [ ] `python -m pytest -q` en verde (Python 3.10, 3.11 y 3.12)
- [ ] CLI smoke ejecutado y **salida observada** (no afirmar sin ejecutar)
- [ ] Sin secretos ni datos de ejemplo que parezcan reales (marca lo sintético como `synthetic`)
- [ ] Tests nuevos para cada invariante tocada (`tests/test_compare.py`)
- [ ] Docs actualizadas si cambian contrato, metodología o definiciones
- [ ] `git diff` revisado; artefactos runtime fuera del repo

## Estilo

- Código y documentación en **español** (identificadores en inglés cuando son parte del contrato).
- Comentarios que expliquen **por qué**, no el qué.
- Sin dependencias nuevas en runtime sin ADR y necesidad medida.
- Números de dinero: `Decimal`, nunca `float`.

## Áreas donde se necesita ayuda

| Área | Qué buscamos |
|---|---|
| **Fuentes y datos** | Fichas verificadas (licencia, cobertura, cadencia) de FX/precios/flete en Argentina |
| **Dominio** | Revisión de la clave de comparabilidad con un comprador/procurement real |
| **Casos** | Un caso real con ≥2 presupuestos formales (preferiblemente anonimizado) |
| **Tests** | Casos límite: múltiples conversiones FX, moneda mixta, cantidades fraccionarias, specs no comparables |
| **Docs** | Traducciones y ejemplos por plataforma (FastAPI, Express, Go, Java) |

## Conducta

Código de conducta: trato respetuoso, foco técnico, revisiones constructivas. Ninguna decisión
técnica ni de producto se toma sin responsable identificable.
