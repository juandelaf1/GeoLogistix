"""Carga y normalización de entradas (JSON/CSV) a modelos de dominio.

Regla: los campos ausentes se representan como ausentes + estado explícito.
Nunca se inventa un valor ni se convierte un vacío en 0.
"""

from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional

from .model import FxRate, Quote

# Columnas CSV aceptadas -> campo canónico (español e inglés).
CSV_FIELD_MAP = {
    "supplier": "supplier", "proveedor": "supplier", "empresa": "supplier",
    "origin": "origin", "origen": "origin",
    "material": "material", "producto": "material",
    "spec": "spec", "especificacion": "spec", "especificación": "spec",
    "quantity": "quantity", "cantidad": "quantity", "cant": "quantity",
    "unit": "unit", "unidad": "unit",
    "unit_price": "unit_price", "precio_unitario": "unit_price", "precio": "unit_price",
    "currency": "currency", "moneda": "currency",
    "price_includes_vat": "price_includes_vat", "incluye_iva": "price_includes_vat",
    "freight_cost": "freight_cost", "flete": "freight_cost", "transporte": "freight_cost",
    "freight_currency": "freight_currency", "moneda_flete": "freight_currency",
    "freight_terms": "freight_terms", "condicion_entrega": "freight_terms",
    "other_costs": "other_costs", "otros_costos": "other_costs",
    "other_currency": "other_currency", "moneda_otros": "other_currency",
    "other_label": "other_label", "otros_concepto": "other_label",
    "quote_id": "quote_id", "nro_presupuesto": "quote_id",
    "date": "date", "fecha": "date",
    "valid_until": "valid_until", "vigencia": "valid_until",
    "source": "source", "fuente": "source",
    "status": "status", "procedencia": "status", "estado_dato": "status",
    "evidence_ref": "evidence_ref", "evidencia": "evidence_ref",
    "notes": "notes", "notas": "notes",
}

NUMERIC_FIELDS = {"quantity", "unit_price", "freight_cost", "other_costs"}
BOOLEAN_FIELDS = {"price_includes_vat"}

_NULL_TOKENS = {"", "null", "na", "n/a", "nd", "sin dato", "-", "none"}


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in _NULL_TOKENS:
            return None
        return stripped
    return value


def _to_decimal(value: Any) -> Any:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    if isinstance(cleaned, (int, float, Decimal)):
        return cleaned
    text = str(cleaned).replace(" ", "").replace("$", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return cleaned


def _to_bool(value: Any) -> Any:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    if isinstance(cleaned, bool):
        return cleaned
    text = str(cleaned).strip().lower()
    if text in {"true", "si", "sí", "yes", "1"}:
        return True
    if text in {"false", "no", "0"}:
        return False
    return cleaned


def fx_from_dict(data: Dict[str, Any]) -> FxRate:
    return FxRate(
        pair=str(data.get("pair", "")).strip(),
        rate=_to_decimal(data.get("rate")),
        date=str(data.get("date", "")).strip(),
        source=str(data.get("source", "")).strip(),
        status=(data.get("status") or "observado").strip(),
        url_or_ref=_clean(data.get("url_or_ref")),
        retrieved_at=_clean(data.get("retrieved_at")),
        rate_type=_clean(data.get("rate_type")),
    )


def quote_from_dict(data: Dict[str, Any]) -> Quote:
    kwargs: Dict[str, Any] = {}
    for key in (
        "supplier", "origin", "material", "spec", "unit", "currency",
        "freight_currency", "freight_terms", "other_currency", "other_label",
        "quote_id", "date", "valid_until", "source", "status", "evidence_ref", "notes",
    ):
        kwargs[key] = _clean(data.get(key))
    for key in NUMERIC_FIELDS:
        kwargs[key] = _to_decimal(data.get(key))
    kwargs["price_includes_vat"] = _to_bool(data.get("price_includes_vat"))
    if not kwargs.get("supplier"):
        kwargs["supplier"] = "(sin proveedor)"
    return Quote(**kwargs)


def load_fx_rates(data: Any) -> List[FxRate]:
    """Acepta lista, dict con 'fx_rates' o snapshot con 'fx_rate_entry'."""
    if isinstance(data, dict):
        if "fx_rates" in data:
            data = data["fx_rates"]
        elif data.get("fx_rate_entry"):
            data = [data["fx_rate_entry"]]
        else:
            data = []
    if not isinstance(data, list):
        return []
    return [fx_from_dict(item) for item in data if isinstance(item, dict)]


def load_quotes(data: Any) -> List[Quote]:
    if isinstance(data, dict):
        data = data.get("quotes") or []
    if not isinstance(data, list):
        return []
    return [quote_from_dict(item) for item in data if isinstance(item, dict)]


def load_case(path: str) -> Dict[str, Any]:
    """Carga un caso JSON: proyecto + fx_rates + quotes."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        "project": raw.get("project") or {},
        "base_currency": (raw.get("base_currency") or "ARS").upper(),
        "fx_rates": load_fx_rates(raw),
        "quotes": load_quotes(raw),
    }


def quotes_from_csv(path: str, delimiter: Optional[str] = None) -> List[Quote]:
    """Lee un CSV de cotizaciones y lo normaliza a `Quote`."""
    text = Path(path).read_text(encoding="utf-8-sig")
    if delimiter:
        class _Dialect(csv.excel):
            pass
        _Dialect.delimiter = delimiter
        dialect = _Dialect
    else:
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
        except Exception:
            dialect = csv.excel
    quotes: List[Quote] = []
    for row in csv.DictReader(text.splitlines(), dialect=dialect):
        mapped: Dict[str, Any] = {}
        for key, value in row.items():
            if not key:
                continue
            canonical = CSV_FIELD_MAP.get(key.strip().lower())
            if not canonical:
                continue
            cleaned = _clean(value)
            if cleaned is None:
                continue
            if canonical in NUMERIC_FIELDS:
                cleaned = _to_decimal(cleaned)
            elif canonical in BOOLEAN_FIELDS:
                cleaned = _to_bool(cleaned)
            mapped[canonical] = cleaned
        if mapped:
            mapped.setdefault("supplier", "(sin proveedor)")
            quotes.append(quote_from_dict(mapped))
    return quotes
