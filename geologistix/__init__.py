"""GeoLogistix — comparador auditable de costo entregado.

Calcula costo entregado por opción de abastecimiento (material + flete +
ajustes explícitos) con conversión FX fechada y procedencia por dato.

Determinista, sin dependencias externas, sin IA. No inventa datos faltantes.
"""

__version__ = "0.1.0"

from .compare import compare, compare_csv, compare_table
from .model import (
    EVIDENCE_STATES,
    FxRate,
    Quote,
    QuoteResult,
)

__all__ = [
    "__version__",
    "EVIDENCE_STATES",
    "FxRate",
    "Quote",
    "QuoteResult",
    "compare",
    "compare_csv",
    "compare_table",
]
