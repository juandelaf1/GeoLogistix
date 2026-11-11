"""Tests del parser de FX (sin red: fixtures HTML embebidos)."""

import unittest
from decimal import Decimal

from geologistix.ingest import parse_bna, record_fx_manual

HTML_FIXTURE = """
<html><body>
  <span>Fecha: 5/11/2026</span>
  <table id="billetes">
    <tr><td class="tit">Dolar U.S.A</td><td>1520,00</td><td>1570,00</td></tr>
  </table>
  <table id="divisas">
    <tr><td class="tit">Dolar U.S.A</td><td>1536.5000</td><td>1545.5000</td></tr>
  </table>
</body></html>
"""


class TestParseBna(unittest.TestCase):
    def test_extracts_date_and_separates_billetes_from_divisas(self):
        published, billetes, divisas, warnings = parse_bna(HTML_FIXTURE)
        self.assertEqual(published, "2026-11-05")
        self.assertEqual(billetes["compra"], Decimal("1520.00"))
        self.assertEqual(billetes["venta"], Decimal("1570.00"))
        self.assertEqual(divisas["compra"], Decimal("1536.5000"))
        self.assertEqual(divisas["venta"], Decimal("1545.5000"))

    def test_missing_values_do_not_raise(self):
        published, billetes, divisas, warnings = parse_bna("<html><body>nada</body></html>")
        self.assertIsNone(published)
        self.assertIsNone(billetes)
        self.assertIsNone(divisas)


class TestManualRecord(unittest.TestCase):
    def test_manual_observation_keeps_provenance(self):
        rate = record_fx_manual(
            pair="USD/ARS",
            rate="1545.50",
            date="2026-11-05",
            source="BNA - Divisas (Venta)",
            rate_type="divisa_venta",
            url_or_ref="https://www.bna.com.ar/Personas",
        )
        self.assertEqual(rate.rate, Decimal("1545.50"))
        self.assertEqual(rate.date, "2026-11-05")
        self.assertEqual(rate.status, "observado")
        self.assertIsNotNone(rate.retrieved_at)


if __name__ == "__main__":
    unittest.main()
