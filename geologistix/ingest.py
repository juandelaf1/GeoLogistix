"""Ingesta de observaciones de tipo de cambio (BNA) con procedencia.

Best-effort y verificable: el parser extrae las tablas de billetes y divisas,
separa ambos tipos y **nunca** inventa una tasa. Si la extraccion falla, se
reporta el error y se debe usar el modo manual (`record_fx_manual`).

Antes de automatizar ingesta recurrente hay que verificar los terminos de uso
de la fuente (ver docs/FUENTES.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen

from .model import FxRate

BNA_BILLETES_URL = "https://www.bna.com.ar/Personas"
BNA_DIVISAS_URL = "https://www.bna.com.ar/Cotizador/MonedasHistorico"
USER_AGENT = "GeoLogistix/0.1 (fx-snapshot; lectura puntual de pagina publica)"

RATE_TYPES = ("billete_compra", "billete_venta", "divisa_compra", "divisa_venta")


@dataclass
class FxSnapshot:
    """Snapshot de una consulta de tipo de cambio."""

    pair: str
    retrieved_at: str
    source: str
    url: str
    published_date: Optional[str]
    rates: Dict[str, Optional[Decimal]]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": "geologistix",
            "contract_version": "fx-snapshot/0.1",
            "pair": self.pair,
            "retrieved_at": self.retrieved_at,
            "source": self.source,
            "url": self.url,
            "published_date": self.published_date,
            "rates": {k: (float(v) if v is not None else None) for k, v in self.rates.items()},
            "warnings": list(self.warnings),
        }

    def selected(self, rate_type: Optional[str] = None) -> Optional[FxRate]:
        """Devuelve la observacion aplicable (por defecto `divisa_venta`)."""
        preference = rate_type or "divisa_venta"
        order = [preference] + [t for t in RATE_TYPES if t != preference]
        for key in order:
            value = self.rates.get(key)
            if value is None or self.published_date is None:
                continue
            return FxRate(
                pair=self.pair,
                rate=value,
                date=self.published_date,
                source=f"{self.source} ({key})",
                status="observado",
                url_or_ref=self.url,
                retrieved_at=self.retrieved_at,
                rate_type=key,
            )
        return None


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_number(text: str) -> Optional[Decimal]:
    """Parsea '1520,00' o '1536.5000' a Decimal exacto."""
    cleaned = text.strip().replace("\xa0", "").replace(" ", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def fetch_html(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _usd_row(chunk: str) -> Optional[Dict[str, Decimal]]:
    """Extrae {compra, venta} de la fila 'Dolar U.S.A' dentro de un fragmento."""
    row = re.search(r"Dolar U\.S\.A.*?</tr>", chunk, re.I | re.S)
    if not row:
        return None
    numbers = re.findall(r"([0-9]{3,5}[\.,][0-9]{2,4})", row.group(0))
    if len(numbers) < 2:
        return None
    compra = _to_number(numbers[0])
    venta = _to_number(numbers[1])
    if compra is None or venta is None:
        return None
    return {"compra": compra, "venta": venta}


def parse_bna(
    html: str,
) -> Tuple[Optional[str], Optional[Dict[str, Decimal]], Optional[Dict[str, Decimal]], List[str]]:
    """Extrae (fecha, billetes, divisas, warnings) del HTML publico del BNA."""
    warnings: List[str] = []

    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", html)
    published_date: Optional[str] = None
    if date_match:
        day, month, year = date_match.group(1).split("/")
        published_date = f"{year}-{int(month):02d}-{int(day):02d}"
    else:
        warnings.append("No se encontro fecha de publicacion en la pagina")

    billetes: Optional[Dict[str, Decimal]] = None
    divisas: Optional[Dict[str, Decimal]] = None

    for container in ("billetes", "divisas"):
        anchor = re.search(r'id=["\']' + container + r'["\']', html, re.I)
        if not anchor:
            continue
        values = _usd_row(html[anchor.start(): anchor.start() + 8000])
        if not values:
            continue
        if container == "billetes":
            billetes = values
        else:
            divisas = values

    if billetes is None or divisas is None:
        rows = list(re.finditer(r"Dolar U\.S\.A.*?</tr>", html, re.I | re.S))
        parsed: List[Dict[str, Decimal]] = []
        for row in rows:
            numbers = re.findall(r"([0-9]{3,5}[\.,][0-9]{2,4})", row.group(0))
            if len(numbers) >= 2:
                compra, venta = _to_number(numbers[0]), _to_number(numbers[1])
                if compra is not None and venta is not None:
                    parsed.append({"compra": compra, "venta": venta})
        if billetes is None and parsed:
            billetes = parsed[0]
        if divisas is None and len(parsed) > 1:
            divisas = parsed[1]
        warnings.append("Extraccion por fallback (orden de aparicion): verificar contra la fuente")

    return published_date, billetes, divisas, warnings


def fetch_bna_snapshot(pair: str = "USD/ARS", timeout: int = 20) -> FxSnapshot:
    """Consulta puntual la pagina publica del BNA y devuelve el snapshot."""
    retrieved_at = now_utc_iso()
    warnings: List[str] = []
    try:
        html = fetch_html(BNA_BILLETES_URL, timeout=timeout)
    except Exception as exc:  # sin red: no hay snapshot, nunca valor inventado
        return FxSnapshot(
            pair=pair,
            retrieved_at=retrieved_at,
            source="BNA (Banco de la Nacion Argentina)",
            url=BNA_BILLETES_URL,
            published_date=None,
            rates={},
            warnings=[f"No se pudo consultar la fuente: {exc}"],
        )

    published_date, billetes, divisas, parse_warnings = parse_bna(html)
    warnings.extend(parse_warnings)

    rates: Dict[str, Optional[Decimal]] = {t: None for t in RATE_TYPES}
    if billetes:
        rates["billete_compra"] = billetes["compra"]
        rates["billete_venta"] = billetes["venta"]
    if divisas:
        rates["divisa_compra"] = divisas["compra"]
        rates["divisa_venta"] = divisas["venta"]
    if not any(value is not None for value in rates.values()):
        warnings.append("No se extrajeron tasas; verificar la pagina o usar el modo manual")

    return FxSnapshot(
        pair=pair,
        retrieved_at=retrieved_at,
        source="BNA (Banco de la Nacion Argentina)",
        url=BNA_BILLETES_URL,
        published_date=published_date,
        rates=rates,
        warnings=warnings,
    )


def record_fx_manual(
    pair: str,
    rate: str,
    date: str,
    source: str,
    rate_type: Optional[str] = None,
    url_or_ref: Optional[str] = None,
    status: str = "observado",
) -> FxRate:
    """Registra una observacion declarada por el usuario (fallback auditable)."""
    return FxRate(
        pair=pair,
        rate=Decimal(str(rate)),
        date=date,
        source=source,
        status=status,
        url_or_ref=url_or_ref,
        retrieved_at=now_utc_iso(),
        rate_type=rate_type,
    )
