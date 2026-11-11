"""Modelos de dominio: cotizaciones, FX y resultados de comparación.

Invariantes clave (ver docs/DEFINITIONS.md):
- El monto y la moneda originales de una cotización son inmutables.
- La conversión es una capa separada, con par, fecha y fuente.
- Un dato ausente se representa como ausente + estado explícito; nunca 0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

# Estados de evidencia/procedencia admitidos por el comparador.
EVIDENCE_STATES = (
    "observado",        # dato tomado de una fuente verificable y fechada
    "derivado",         # calculado a partir de datos observados
    "estimado",         # estimación declarada (fuente o método conocido)
    "sintético",        # generado para pruebas/demo (nunca observado)
    "no_disponible",    # el dato no existe / no se obtuvo
    "rechazado",        # descartado por regla de calidad
)

CONTRACT_VERSION = "delivered-cost/0.1"


@dataclass
class FxRate:
    """Observación de tipo de cambio. Inmutable una vez registrada."""

    pair: str                       # p.ej. "USD/ARS"
    rate: Optional[Decimal]
    date: str                       # fecha publicada por la fuente (YYYY-MM-DD)
    source: str                     # emisor + tipo de tasa ("BNA - Divisas (Venta)")
    status: str = "observado"       # uno de EVIDENCE_STATES
    url_or_ref: Optional[str] = None
    retrieved_at: Optional[str] = None   # ISO-8601 UTC de captura
    rate_type: Optional[str] = None      # billete_compra|billete_venta|divisa_compra|divisa_venta

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["rate"] = float(self.rate) if self.rate is not None else None
        return d


@dataclass
class Quote:
    """Oferta comercial de material. Cantidad y moneda originales inmutables."""

    supplier: str
    origin: Optional[str] = None
    material: Optional[str] = None
    spec: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    currency: str = "ARS"
    price_includes_vat: Optional[bool] = None
    freight_cost: Optional[Decimal] = None
    freight_currency: Optional[str] = None
    freight_terms: Optional[str] = None
    other_costs: Optional[Decimal] = None
    other_currency: str = "ARS"
    other_label: Optional[str] = None
    quote_id: Optional[str] = None
    date: Optional[str] = None
    valid_until: Optional[str] = None
    source: Optional[str] = None
    status: str = "observado"
    evidence_ref: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        for k in ("quantity", "unit_price", "freight_cost", "other_costs"):
            v = d.get(k)
            if v is not None:
                d[k] = float(v)
        return d

@dataclass
class QuoteResult:
    """Resultado evaluado de una oferta, con desglose y alertas."""

    supplier: str
    material: Optional[str] = None
    origin: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    status_dato: str = "desconocido"
    source: Optional[str] = None
    date: Optional[str] = None
    currency_original: str = "ARS"
    breakdown_original: Dict[str, Any] = field(default_factory=dict)
    breakdown_base: List[Dict[str, Any]] = field(default_factory=list)
    total_base: Optional[Decimal] = None
    base_currency: str = "ARS"
    fx_used: List[Dict[str, Any]] = field(default_factory=list)
    comparable: bool = False
    incomplete: bool = False
    alerts: List[str] = field(default_factory=list)
    rank: Optional[int] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a JSON.

        Los importes monetarios se serializan como **string decimal** (2 decimales)
        para no perder exactitud con punto flotante binario. La cantidad se
        serializa como número.
        """
        d = asdict(self)
        total = d.get("total_base")
        d["total_base"] = None if total is None else f"{Decimal(total):.2f}"
        quantity = d.get("quantity")
        if quantity is not None:
            q = Decimal(quantity)
            d["quantity"] = int(q) if q == q.to_integral_value() else float(q)
        for b in d.get("breakdown_base", []):
            amount = b.get("amount_base")
            b["amount_base"] = None if amount is None else f"{Decimal(amount):.2f}"
        original = d.get("breakdown_original") or {}
        for key in ("material", "freight", "other", "unit_price"):
            value = original.get(key)
            if value is not None:
                original[key] = f"{Decimal(value):.2f}"
        original_quantity = original.get("quantity")
        if original_quantity is not None:
            q = Decimal(original_quantity)
            original["quantity"] = int(q) if q == q.to_integral_value() else float(q)
        return d