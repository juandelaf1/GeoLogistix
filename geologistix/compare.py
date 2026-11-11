"""Motor de comparación de costo entregado.

Determinista: mismos datos de entrada -> mismo resultado. Sin IA, sin red.

Invariantes:
1. Un dato ausente NUNCA se trata como 0 (salvo 0 explícito del usuario).
2. Una opción es comparable como "costo entregado" solo si tiene material,
   flete informado y conversión completa.
3. El ranking excluye las opciones no comparables (rank=None) y expone
   alertas explícitas.
4. El monto/moneda originales se conservan; la conversión es capa aparte.
5. Aritmética en Decimal (precisión 28), redondeo ROUND_HALF_UP a 2 decimales.
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext
from typing import Any, Dict, List, Optional

from .fx import convert
from .model import CONTRACT_VERSION, FxRate, Quote, QuoteResult

getcontext().prec = 28

TWO_PLACES = Decimal("0.01")


def _dec(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _money(value: Optional[Decimal]) -> Optional[Decimal]:
    if value is None:
        return None
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def evaluate_quote(
    quote: Quote,
    base_currency: str,
    fx_rates: List[FxRate],
) -> QuoteResult:
    """Evalúa una oferta: desglose, conversión, comparabilidad y alertas."""
    alerts: List[str] = []
    currency = (quote.currency or base_currency).upper()
    freight_currency = (quote.freight_currency or currency).upper()
    other_currency = (quote.other_currency or currency).upper()

    quantity = _dec(quote.quantity)
    unit_price = _dec(quote.unit_price)
    freight = _dec(quote.freight_cost)
    other = _dec(quote.other_costs)

    material_cost: Optional[Decimal] = None
    if unit_price is not None and quantity is not None:
        material_cost = unit_price * quantity
    elif unit_price is not None and quantity is None:
        alerts.append("cantidad faltante: no se calcula material total")
    else:
        alerts.append("precio/cantidad no disponible: material_cost incompleto")

    freight_informed = quote.freight_cost is not None and quote.freight_cost != ""
    if not freight_informed:
        alerts.append("flete no informado (costo entregado incompleto)")

    components: List[tuple] = []
    if material_cost is not None:
        components.append(("material", material_cost, currency))
    if freight is not None:
        components.append(("flete", freight, freight_currency))
    if other is not None:
        components.append(("otros", other, other_currency))

    total_base = Decimal("0")
    fx_used: List[Dict[str, Any]] = []
    convertible = True
    breakdown_base: List[Dict[str, Any]] = []

    for name, amount, cur in components:
        converted, meta, error = convert(amount, cur, base_currency, fx_rates)
        if error:
            alerts.append(f"{name}: {error}")
            convertible = False
            breakdown_base.append(
                {"concept": name, "amount_base": None, "currency_from": cur}
            )
            continue
        total_base += converted  # type: ignore[operator]
        if meta and meta not in fx_used:
            fx_used.append(meta)
        breakdown_base.append(
            {
                "concept": name,
                "amount_base": _money(converted),
                "currency_from": cur,
                "fx_pair": meta.get("pair") if meta else None,
                "fx_date": meta.get("date") if meta else None,
                "fx_source": meta.get("source") if meta else None,
                "fx_status": meta.get("status") if meta else None,
            }
        )

    comparable = bool(material_cost is not None and freight_informed and convertible)
    incomplete = bool(
        material_cost is None
        or not freight_informed
        or not convertible
        or any("no disponible" in a or "incompleto" in a for a in alerts)
    )

    return QuoteResult(
        supplier=quote.supplier,
        material=quote.material,
        origin=quote.origin,
        quantity=quantity,
        unit=quote.unit,
        status_dato=quote.status or "desconocido",
        source=quote.source,
        date=quote.date,
        currency_original=currency,
        breakdown_original={
            "material": _money(material_cost),
            "freight": _money(freight),
            "freight_currency": freight_currency if freight is not None else None,
            "other": _money(other),
            "other_label": quote.other_label,
            "unit_price": _money(unit_price),
            "quantity": quantity,
            "unit": quote.unit,
            "price_includes_vat": quote.price_includes_vat,
            "freight_terms": quote.freight_terms,
        },
        breakdown_base=breakdown_base,
        total_base=_money(total_base) if (components and convertible) else None,
        base_currency=base_currency,
        fx_used=fx_used,
        comparable=comparable,
        incomplete=incomplete,
        alerts=alerts,
        notes=quote.notes,
    )


def rank(results: List[QuoteResult]) -> List[QuoteResult]:
    """Ordena: comparables primero (menor total), no comparables al final."""
    def sort_key(result: QuoteResult):
        total = result.total_base if result.comparable else None
        return (0 if result.comparable else 1, total if total is not None else Decimal("Infinity"))

    ordered = sorted(results, key=sort_key)
    position = 0
    for result in ordered:
        if result.comparable and result.total_base is not None:
            position += 1
            result.rank = position
        else:
            result.rank = None
    return ordered


def compare(
    quotes: List[Quote],
    fx_rates: List[FxRate],
    base_currency: str = "ARS",
    project: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compara ofertas y devuelve el payload auditable (formato JSON)."""
    base_currency = (base_currency or "ARS").upper()
    results = rank([evaluate_quote(q, base_currency, fx_rates) for q in quotes])
    return {
        "tool": "geologistix",
        "contract_version": CONTRACT_VERSION,
        "project": project or {},
        "base_currency": base_currency,
        "fx_rates_count": len(fx_rates),
        "quotes_count": len(quotes),
        "results": [r.to_dict() for r in results],
        "disclaimer": (
            "Comparación informativa calculada con los datos provistos; "
            "no certifica idoneidad técnica, legal ni ambiental. "
            "Verificar procedencia, vigencia y exclusiones antes de decidir."
        ),
    }


def compare_table(payload: Dict[str, Any]) -> str:
    """Render legible para consola/reunión."""
    base = payload.get("base_currency", "ARS")
    project = payload.get("project") or {}
    destination = project.get("destination") or "-"
    lines = [
        f"Costo entregado — destino: {destination} | base: {base} | "
        f"cotizaciones: {payload.get('quotes_count', 0)}",
        "-" * 100,
    ]
    for r in payload.get("results", []):
        rank_label = r.get("rank") if r.get("rank") is not None else "-"
        total = f"{r['total_base']} {base}" if r.get("total_base") is not None else "N/D"
        flags = []
        if not r.get("comparable"):
            flags.append("NO COMPARABLE")
        if r.get("incomplete"):
            flags.append("incompleto")
        flag_text = f" [{', '.join(flags)}]" if flags else ""
        quantity = r.get("quantity")
        quantity_label = "" if quantity is None else f"{quantity:g} " if isinstance(quantity, float) else f"{quantity} "
        lines.append(
            f"#{rank_label} {r.get('supplier')} | {r.get('material')} "
            f"{quantity_label}{r.get('unit') or ''} | total: {total} | "
            f"dato: {r.get('status_dato')} | fecha: {r.get('date')}{flag_text}"
        )
        for alert in r.get("alerts") or []:
            lines.append(f"    alertas: {alert}")
    return "\n".join(lines)


CSV_COLUMNS = [
    "rank", "supplier", "origin", "material", "quantity", "unit", "status_dato",
    "date", "source", "material_original", "freight_original", "other_original",
    "currency_original", "total_base", "base_currency", "comparable", "incomplete",
    "alerts", "notes",
]


def compare_csv(payload: Dict[str, Any]) -> str:
    """Render CSV (una fila por opción) para hoja de cálculo / informe."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for r in payload.get("results", []):
        original = r.get("breakdown_original") or {}
        writer.writerow(
            {
                "rank": r.get("rank"),
                "supplier": r.get("supplier"),
                "origin": r.get("origin"),
                "material": r.get("material"),
                "quantity": r.get("quantity"),
                "unit": r.get("unit"),
                "status_dato": r.get("status_dato"),
                "date": r.get("date"),
                "source": r.get("source"),
                "material_original": original.get("material"),
                "freight_original": original.get("freight"),
                "other_original": original.get("other"),
                "currency_original": r.get("currency_original"),
                "total_base": r.get("total_base"),
                "base_currency": r.get("base_currency"),
                "comparable": r.get("comparable"),
                "incomplete": r.get("incomplete"),
                "alerts": " | ".join(r.get("alerts") or []),
                "notes": r.get("notes"),
            }
        )
    return buffer.getvalue()
