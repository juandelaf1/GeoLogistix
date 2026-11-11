"""Interfaz de línea de comandos de GeoLogistix.

Comandos:
  compare   Compara cotizaciones de un caso JSON/CSV y emite tabla/JSON/CSV.
  fx        Registra una observación de tipo de cambio (archivo JSON o manual).
  import    Convierte un CSV de cotizaciones al formato de caso JSON.

Sin dependencias externas. Códigos de salida: 0 ok, 1 error de uso/entrada,
2 datos insuficientes para comparar (ninguna opción comparable).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .compare import compare, compare_csv, compare_table
from .io import load_case, load_fx_rates, quotes_from_csv
from .model import CONTRACT_VERSION


def _write_or_print(text: str, out: Optional[str]) -> None:
    if out:
        Path(out).write_text(text, encoding="utf-8", newline="")
        sys.stdout.write(f"[ok] {out}\n")
    else:
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))


def cmd_compare(args) -> int:
    case = load_case(args.input)
    fx_rates = list(case["fx_rates"])

    if args.fx:
        fx_rates.extend(load_fx_rates(json.loads(Path(args.fx).read_text(encoding="utf-8"))))

    quotes = list(case["quotes"])
    if args.quotes_csv:
        quotes.extend(quotes_from_csv(args.quotes_csv))

    if not quotes:
        sys.stderr.write("error: no hay cotizaciones que comparar\n")
        return 1

    payload = compare(
        quotes,
        fx_rates,
        base_currency=case["base_currency"],
        project=case["project"],
    )

    if args.format == "json":
        _write_or_print(json.dumps(payload, ensure_ascii=False, indent=2), args.out)
    elif args.format == "csv":
        _write_or_print(compare_csv(payload), args.out)
    else:
        _write_or_print(compare_table(payload), args.out)

    if args.strict and not any(r.get("comparable") for r in payload["results"]):
        sys.stderr.write(
            "datos insuficientes: ninguna opción comparable como costo entregado "
            "(revisar flete informado, especificación y FX)\n"
        )
        return 2
    return 0


def cmd_fx(args) -> int:
    if args.fetch:
        from .ingest import fetch_bna_snapshot

        snapshot = fetch_bna_snapshot(pair=args.pair)
        entry = snapshot.selected(args.rate_type)
        payload = snapshot.to_dict()
        if entry is None:
            payload["fx_rate_entry"] = None
            sys.stderr.write(
                "advertencia: no se pudo seleccionar una tasa observada; "
                "revisar la fuente o usar --rate/--date/--source (modo manual)\n"
            )
        else:
            payload["fx_rate_entry"] = entry.to_dict()
        _write_or_print(json.dumps(payload, ensure_ascii=False, indent=2), args.out)
        return 0 if entry is not None else 1

    if args.file:
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    else:
        if args.rate is None or not args.date or not args.source:
            sys.stderr.write(
                "error: --file, --fetch o (--rate --date --source) son obligatorios\n"
            )
            return 1
        data = {
            "fx_rate_entry": {
                "pair": args.pair,
                "rate": args.rate,
                "date": args.date,
                "source": args.source,
                "status": args.status,
                "url_or_ref": args.url,
                "rate_type": args.rate_type,
            }
        }
    entry = data.get("fx_rate_entry") if isinstance(data, dict) else None
    if not entry:
        sys.stderr.write("error: el archivo no contiene 'fx_rate_entry'\n")
        return 1
    _write_or_print(json.dumps(entry, ensure_ascii=False, indent=2), args.out)
    return 0


def cmd_import(args) -> int:
    quotes = quotes_from_csv(args.csv)
    if not quotes:
        sys.stderr.write("error: el CSV no contiene cotizaciones reconocibles\n")
        return 1
    case = {
        "project": {"name": args.project_name or "", "destination": args.destination or ""},
        "base_currency": (args.base_currency or "ARS").upper(),
        "fx_rates": [],
        "quotes": [q.to_dict() for q in quotes],
    }
    if args.fx:
        case["fx_rates"] = [
            r.to_dict() for r in load_fx_rates(json.loads(Path(args.fx).read_text(encoding="utf-8")))
        ]
    _write_or_print(json.dumps(case, ensure_ascii=False, indent=2), args.out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geologistix",
        description="Comparador auditable de costo entregado (material + flete + ajustes, FX fechado).",
    )
    parser.add_argument("--version", action="version", version=f"geologistix {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_compare = sub.add_parser("compare", help="compara cotizaciones de un caso")
    p_compare.add_argument("input", help="caso JSON (quotes[] + fx_rates[])")
    p_compare.add_argument("--format", choices=["table", "json", "csv"], default="table")
    p_compare.add_argument("--out", help="archivo de salida (default: stdout)")
    p_compare.add_argument("--fx", help="archivo JSON adicional de tasas FX")
    p_compare.add_argument("--quotes-csv", help="CSV adicional de cotizaciones")
    p_compare.add_argument(
        "--strict",
        action="store_true",
        help="código de salida 2 si ninguna opción es comparable",
    )
    p_compare.set_defaults(func=cmd_compare)

    p_fx = sub.add_parser("fx", help="normaliza una observación de tipo de cambio")
    p_fx.add_argument("--file", help="JSON con fx_rate_entry")
    p_fx.add_argument(
        "--fetch",
        action="store_true",
        help="consulta puntual la pagina publica del BNA (verificar valores)",
    )
    p_fx.add_argument("--pair", default="USD/ARS")
    p_fx.add_argument("--rate", type=float)
    p_fx.add_argument("--date")
    p_fx.add_argument("--source")
    p_fx.add_argument("--status", default="observado")
    p_fx.add_argument("--url")
    p_fx.add_argument("--rate-type", dest="rate_type")
    p_fx.add_argument("--out")
    p_fx.set_defaults(func=cmd_fx)

    p_import = sub.add_parser("import", help="convierte CSV de cotizaciones a caso JSON")
    p_import.add_argument("csv")
    p_import.add_argument("--fx", help="JSON con fx_rates[] o fx_rate_entry")
    p_import.add_argument("--base-currency", default="ARS")
    p_import.add_argument("--project-name")
    p_import.add_argument("--destination")
    p_import.add_argument("--out")
    p_import.set_defaults(func=cmd_import)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
