"""Conversión de moneda con observación FX fechada y trazable.

Reglas:
- Una tasa es meaningful solo con par, tipo, fecha y fuente.
- Si no existe una observación válida para el par, NO se convierte: la opción
  queda no comparable (no se inventa ni se usa una tasa "de facto").
- Se conserva siempre el monto y la moneda originales.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from .model import FxRate


def find_rate(
    fx_rates: List[FxRate],
    from_currency: str,
    to_currency: str,
) -> Tuple[Optional[Decimal], Optional[Dict[str, Any]]]:
    """Devuelve (tasa, metadatos) para from_currency->to_currency, o (None, None).

    Soporta tasa inversa (derivada) cuando la fuente publica el par contrario,
    marcándolo como ``derived_from`` en los metadatos.
    """
    if from_currency == to_currency:
        return Decimal("1"), {
            "pair": f"{from_currency}/{to_currency}",
            "rate": 1,
            "date": None,
            "source": "identity",
            "status": "observado",
        }

    pair = f"{from_currency}/{to_currency}"
    inverse_pair = f"{to_currency}/{from_currency}"

    for rate in fx_rates:
        if rate.pair == pair and rate.rate is not None:
            return rate.rate, rate.to_dict()
        if rate.pair == inverse_pair and rate.rate is not None and rate.rate != 0:
            inverted = Decimal("1") / rate.rate
            meta = rate.to_dict()
            meta.update(
                {
                    "pair": pair,
                    "rate": float(inverted),
                    "derived_from": inverse_pair,
                    "status": "derivado",
                }
            )
            return inverted, meta

    return None, None


def convert(
    amount: Optional[Decimal],
    from_currency: str,
    to_currency: str,
    fx_rates: List[FxRate],
) -> Tuple[Optional[Decimal], Optional[Dict[str, Any]], Optional[str]]:
    """Convierte un monto. Devuelve (importe, metadatos_fx, error).

    ``error`` es None en caso de éxito; en caso contrario es un motivo legible
    (p.ej. "sin tasa FX USD/ARS").
    """
    if amount is None:
        return None, None, "monto no disponible"

    rate, meta = find_rate(fx_rates, from_currency, to_currency)
    if rate is None:
        return None, None, f"sin tasa FX {from_currency}/{to_currency}"

    return amount * rate, meta, None
