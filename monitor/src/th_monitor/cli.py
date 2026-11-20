"""On-demand CLI. Run it when you want an answer; it does not stay running.

Examples
--------
  th-monitor check --from SFO --to NRT --start 2026-12-01 --end 2026-12-20 --cabin business
  th-monitor check --from JFK --to MAD --start 2026-12-01 --end 2026-12-10 --cabin business --json

Free-first: works with no keys (seats.aero cached ~60 days). Set
SEATS_AERO_API_KEY to unlock live search and dates beyond the cache window.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import json as _json
from pathlib import Path as _Path

from .knowledge import Knowledge
from .models import Cabin
from .pipeline import evaluate
from .source import (
    KeylessPathUnavailable,
    SeatsAeroSource,
    SourceError,
    from_mcp_json,
)


def _data_dir() -> Path:
    # repo layout: <repo>/data and <repo>/monitor/src/th_monitor/cli.py
    return Path(__file__).resolve().parents[3] / "data"


def _balances_from_file(path: str | None) -> tuple[dict, dict]:
    """Optional balances file: {"direct": {...}, "currencies": {...}}."""
    if not path:
        return {}, {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data.get("direct", {}), data.get("currencies", {})


def cmd_check(args: argparse.Namespace) -> int:
    kb = Knowledge(_data_dir())
    data_warnings = kb.staleness_warnings()
    direct, currencies = _balances_from_file(args.balances)

    source = SeatsAeroSource()
    source_warnings: list[str] = []
    availabilities = []
    mode = "none"

    if args.mcp_json:
        # Keyless path: consume availability the agent (Kiro) fetched via the
        # seats.aero MCP server and saved to a file.
        try:
            payload = _json.loads(_Path(args.mcp_json).read_text(encoding="utf-8"))
            availabilities = from_mcp_json(payload, Cabin(args.cabin))
            mode = "mcp (keyless, via agent)"
        except (OSError, ValueError) as e:
            source_warnings.append(f"could not read --mcp-json: {e}")
    else:
        try:
            availabilities = source.search(
                args.origin, args.destination, args.start, args.end, Cabin(args.cabin)
            )
            mode = "partner API (keyed)"
        except KeylessPathUnavailable as e:
            # Honest: without a key there is no keyless REST path. Point at MCP.
            source_warnings.append(str(e))
            mode = "no key — use MCP via Kiro or set SEATS_AERO_API_KEY"
        except SourceError as e:
            # Never report a source failure as "no availability".
            source_warnings.append(str(e))

    opps = evaluate(
        availabilities,
        kb,
        held_currencies=currencies,
        direct_balances=direct,
        min_seats=args.seats,
        only_high_value=not args.all,
    )

    if args.json:
        print(json.dumps({
            "query": {
                "origin": args.origin, "destination": args.destination,
                "start": args.start, "end": args.end, "cabin": args.cabin,
                "mode": mode, "has_key": source.has_key,
            },
            "opportunities": [o.to_dict() for o in opps],
            "source_warnings": source_warnings,
            "data_warnings": data_warnings,
            "scanned": len(availabilities),
        }, indent=2))
        # Also write the latest result for Kiro to read.
        _write_latest(opps, source_warnings, data_warnings)
        return 0

    _print_human(args, opps, availabilities, source_warnings, data_warnings, mode)
    _write_latest(opps, source_warnings, data_warnings)
    return 0


def _write_latest(opps, source_warnings, data_warnings) -> None:
    out_dir = Path(__file__).resolve().parents[3] / "monitor" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest.json").write_text(
        json.dumps({
            "opportunities": [o.to_dict() for o in opps],
            "source_warnings": source_warnings,
            "data_warnings": data_warnings,
        }, indent=2),
        encoding="utf-8",
    )


def _print_human(args, opps, availabilities, source_warnings, data_warnings, mode) -> None:
    print(f"\nAward check: {args.origin} -> {args.destination}  {args.start}..{args.end}  "
          f"{args.cabin}  [{mode}]\n")
    if source_warnings:
        for w in source_warnings:
            print(f"  ! source: {w}")
        print()
    if not availabilities and not source_warnings:
        print("  No award space found in this window. (This is a real empty result, "
              "not an error.)\n")
    if opps:
        print(f"  {len(opps)} opportunity(ies), ranked:\n")
        print(f"  {'route':<10} {'date':<11} {'program':<26} {'miles':>7} "
              f"{'fees$':>6} {'cpm':>5}  value")
        for o in opps:
            a = o.availability
            star = "★ " if o.sweet_spot_id else "  "
            cpm = f"{o.cpm:.2f}" if o.cpm is not None else "  -"
            print(f"{star}{a.origin}-{a.destination:<6} {a.date:<11} {a.program:<26} "
                  f"{(a.miles_cost or 0):>7} {(a.cash_fees_usd or 0):>6.0f} {cpm:>5}  "
                  f"{o.value_class.value}")
            if o.sweet_spot_id:
                print(f"      sweet spot: {o.sweet_spot_id} — {o.booking_path}")
            for n in o.notes:
                print(f"      note: {n}")
    elif availabilities:
        print("  Award space exists but nothing cleared the value/reachability gate. "
              "Run with --all to see everything.\n")
    for w in data_warnings:
        print(f"  (data) {w}")
    print()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="th-monitor", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="run an on-demand award check now")
    c.add_argument("--from", dest="origin", required=True)
    c.add_argument("--to", dest="destination", required=True)
    c.add_argument("--start", required=True, help="YYYY-MM-DD")
    c.add_argument("--end", required=True, help="YYYY-MM-DD")
    c.add_argument("--cabin", default="business",
                   choices=[c.value for c in Cabin])
    c.add_argument("--seats", type=int, default=1, help="minimum seats")
    c.add_argument("--mcp-json", help="keyless path: a JSON file of availability the "
                                      "agent fetched via the seats.aero MCP server")
    c.add_argument("--balances", help="optional JSON file with your balances")
    c.add_argument("--all", action="store_true", help="show all, not just high-value")
    c.add_argument("--json", action="store_true", help="machine-readable output")
    c.set_defaults(func=cmd_check)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
