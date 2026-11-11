"""Tests del motor de comparación (sin dependencias externas)."""

import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from geologistix.compare import compare, compare_csv, compare_table
from geologistix.io import load_case, quotes_from_csv
from geologistix.model import FxRate, Quote

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def fx_usd_ars(rate="1545.50"):
    return FxRate(
        pair="USD/ARS",
        rate=Decimal(rate),
        date="2026-11-05",
        source="BNA - Divisas (Venta)",
        status="observado",
        rate_type="divisa_venta",
    )


class TestFxConversion(unittest.TestCase):
    def test_conversion_uses_dated_observation(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="B",
                    material="Cemento",
                    quantity=Decimal("100"),
                    unit="bolsa",
                    unit_price=Decimal("6.90"),
                    currency="USD",
                    freight_cost=Decimal("120000"),
                    freight_currency="ARS",
                )
            ],
            fx_rates=[fx_usd_ars()],
        )
        result = payload["results"][0]
        self.assertTrue(result["comparable"])
        self.assertEqual(Decimal(result["total_base"]), Decimal("1186395.00"))
        self.assertEqual(result["fx_used"][0]["date"], "2026-11-05")
        self.assertEqual(result["fx_used"][0]["pair"], "USD/ARS")

    def test_missing_fx_blocks_comparability(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="B",
                    material="Cemento",
                    quantity=Decimal("10"),
                    unit="bolsa",
                    unit_price=Decimal("6.90"),
                    currency="USD",
                    freight_cost=Decimal("1000"),
                    freight_currency="ARS",
                )
            ],
            fx_rates=[],
        )
        result = payload["results"][0]
        self.assertFalse(result["comparable"])
        self.assertTrue(any("sin tasa FX" in a for a in result["alerts"]))

    def test_inverse_pair_is_marked_derived(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="B",
                    material="X",
                    quantity=Decimal("1"),
                    unit="u",
                    unit_price=Decimal("1545.50"),
                    currency="USD",
                    freight_cost=Decimal("0"),
                    freight_currency="USD",
                )
            ],
            fx_rates=[
                FxRate(
                    pair="ARS/USD",
                    rate=Decimal("1"),
                    date="2026-11-05",
                    source="prueba inversa",
                )
            ],
        )
        result = payload["results"][0]
        self.assertTrue(result["comparable"])
        fx_used = result["fx_used"][0]
        self.assertEqual(fx_used["pair"], "USD/ARS")
        self.assertEqual(fx_used["status"], "derivado")
        self.assertEqual(fx_used["derived_from"], "ARS/USD")


class TestComparabilityRules(unittest.TestCase):
    def test_missing_freight_is_not_comparable(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="C",
                    material="Cemento",
                    quantity=Decimal("100"),
                    unit="bolsa",
                    unit_price=Decimal("8200"),
                    freight_cost=None,
                )
            ],
            fx_rates=[],
        )
        result = payload["results"][0]
        self.assertFalse(result["comparable"])
        self.assertTrue(result["incomplete"])
        self.assertIsNone(result["rank"])
        self.assertTrue(any("flete no informado" in a for a in result["alerts"]))

    def test_zero_freight_explicit_is_comparable(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="C",
                    material="Cemento",
                    quantity=Decimal("100"),
                    unit="bolsa",
                    unit_price=Decimal("8200"),
                    freight_cost=Decimal("0"),
                )
            ],
            fx_rates=[],
        )
        result = payload["results"][0]
        self.assertTrue(result["comparable"])
        self.assertEqual(Decimal(result["total_base"]), Decimal("820000.00"))

    def test_missing_price_is_not_comparable(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="D",
                    material="Cemento",
                    quantity=Decimal("100"),
                    unit="bolsa",
                    unit_price=None,
                    freight_cost=Decimal("1000"),
                )
            ],
            fx_rates=[],
        )
        result = payload["results"][0]
        self.assertFalse(result["comparable"])
        self.assertTrue(any("material_cost incompleto" in a for a in result["alerts"]))


class TestRanking(unittest.TestCase):
    def test_comparables_ranked_by_total_and_excluded_others(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="caro",
                    material="X",
                    quantity=Decimal("1"),
                    unit="u",
                    unit_price=Decimal("10000"),
                    freight_cost=Decimal("0"),
                ),
                Quote(
                    supplier="barato",
                    material="X",
                    quantity=Decimal("1"),
                    unit="u",
                    unit_price=Decimal("8000"),
                    freight_cost=Decimal("0"),
                ),
                Quote(
                    supplier="incompleto",
                    material="X",
                    quantity=Decimal("1"),
                    unit="u",
                    unit_price=Decimal("1"),
                ),
            ],
            fx_rates=[],
        )
        results = payload["results"]
        self.assertEqual(results[0]["supplier"], "barato")
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[1]["supplier"], "caro")
        self.assertEqual(results[1]["rank"], 2)
        self.assertEqual(results[2]["supplier"], "incompleto")
        self.assertIsNone(results[2]["rank"])


class TestArithmetic(unittest.TestCase):
    def test_decimal_precision_no_float_drift(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="P",
                    material="X",
                    quantity=Decimal("3"),
                    unit="u",
                    unit_price=Decimal("0.1"),
                    freight_cost=Decimal("0"),
                )
            ],
            fx_rates=[],
        )
        self.assertEqual(Decimal(payload["results"][0]["total_base"]), Decimal("0.30"))

    def test_output_payload_contract(self):
        payload = compare(quotes=[], fx_rates=[])
        self.assertEqual(payload["contract_version"], "delivered-cost/0.1")
        self.assertIn("disclaimer", payload)
        self.assertEqual(payload["base_currency"], "ARS")


class TestRenderers(unittest.TestCase):
    def test_table_and_csv_render(self):
        payload = compare(
            quotes=[
                Quote(
                    supplier="P",
                    material="X",
                    quantity=Decimal("1"),
                    unit="u",
                    unit_price=Decimal("100"),
                    freight_cost=Decimal("0"),
                    date="2026-11-11",
                )
            ],
            fx_rates=[],
        )
        table = compare_table(payload)
        self.assertIn("Costo entregado", table)
        csv_text = compare_csv(payload)
        self.assertTrue(csv_text.startswith("rank,supplier"))


class TestIO(unittest.TestCase):
    def test_load_example_case(self):
        case = load_case(str(EXAMPLES / "case_cemento_caba.json"))
        self.assertEqual(case["base_currency"], "ARS")
        self.assertGreaterEqual(len(case["quotes"]), 2)
        self.assertGreaterEqual(len(case["fx_rates"]), 1)

    def test_quotes_from_csv_skips_empty_values(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "q.csv"
            path.write_text(
                "supplier,material,quantity,unit_price,currency,freight_cost,status\n"
                "A,Cemento,100,8200,ARS,,observado\n",
                encoding="utf-8",
            )
            quotes = quotes_from_csv(str(path))
            self.assertEqual(len(quotes), 1)
            self.assertIsNone(quotes[0].freight_cost)

    def test_json_roundtrip(self):
        payload = compare(quotes=[], fx_rates=[])
        self.assertEqual(json.loads(json.dumps(payload))["contract_version"], "delivered-cost/0.1")


if __name__ == "__main__":
    unittest.main()
