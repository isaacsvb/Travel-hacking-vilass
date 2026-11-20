"""Loads and queries the shared reference data in the repo's data/ directory."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path


class Knowledge:
    """Thin accessor over the toolkit's data/*.json reference files."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.alliances = self._load("alliances.json")
        self.partner_awards = self._load("partner-awards.json")
        self.sweet_spots = self._load("sweet-spots.json")
        self.transfer_partners = self._load("transfer-partners.json")
        self.points_valuations = self._load("points-valuations.json")

    def _load(self, name: str) -> dict:
        path = self.data_dir / name
        if not path.exists():
            raise FileNotFoundError(f"reference data missing: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def staleness_warnings(self) -> list[str]:
        """Return a warning per dataset whose last_updated exceeds its threshold."""
        warnings: list[str] = []
        for name, data in [
            ("alliances", self.alliances),
            ("partner-awards", self.partner_awards),
            ("sweet-spots", self.sweet_spots),
            ("transfer-partners", self.transfer_partners),
            ("points-valuations", self.points_valuations),
        ]:
            meta = data.get("_meta", {})
            lu = meta.get("last_updated")
            days = meta.get("staleness_days")
            if not lu or not days:
                continue
            try:
                age = (date.today() - datetime.fromisoformat(lu).date()).days
            except ValueError:
                continue
            if age > int(days):
                warnings.append(f"{name} is {age}d old (threshold {days}d) — refresh it")
        return warnings

    def program_valuation(self, program: str) -> tuple[float, float] | None:
        """Return (floor, ceiling) CPM for an airline program, or None if unknown."""
        airline = self.points_valuations.get("airline_miles", {})
        entry = airline.get(program)
        if not entry:
            return None
        return float(entry["floor"]), float(entry["ceiling"])

    def booking_programs_for(self, operating_carrier: str) -> list[str]:
        """Programs that can issue an award on this operating carrier.

        Uses the alliance membership of the carrier plus any program whose
        bookable map lists that alliance, matching the data file's shape
        ("all members"). Cross-alliance highlights are also included.
        """
        alliance = self._carrier_alliance(operating_carrier)
        result: list[str] = []
        for prog_id, prog in self.partner_awards.get("programs", {}).items():
            bookable = prog.get("bookable", {})
            if alliance and alliance in bookable:
                result.append(prog_id)
        # Cross-alliance explicit paths (e.g. Virgin Atlantic -> ANA)
        for hi in self.partner_awards.get("cross_alliance_highlights", []):
            if operating_carrier.lower() in hi.get("name", "").lower():
                # name is like "Virgin Atlantic to ANA"; map the booking program
                prog = hi["name"].split(" to ")[0].strip().lower().replace(" ", "_")
                # best-effort match against program ids
                for pid in self.partner_awards.get("programs", {}):
                    if prog in pid and pid not in result:
                        result.append(pid)
        return result

    def _carrier_alliance(self, carrier: str) -> str | None:
        c = carrier.strip().lower()
        if not c:
            return None
        for alliance in ("star_alliance", "oneworld", "skyteam"):
            members = self.alliances.get(alliance, {}).get("members", [])
            for m in members:
                name = m.get("airline", "").lower()
                iata = m.get("iata", "").lower()
                # IATA is an exact match; airline name matches either direction
                # so "United" finds "United Airlines" and vice versa.
                if c == iata or c == name or c in name or name in c:
                    return alliance
        return None

    def transfer_options(self, program: str, held_currencies: dict[str, int]) -> list[int]:
        """Ratio-adjusted program miles reachable from each held card currency.

        held_currencies: {currency_id: balance}. Returns a list of transferable
        amounts (one per currency that has a path to `program`).
        """
        out: list[int] = []
        currencies = self.transfer_partners.get("currencies", {})
        for cur_id, balance in held_currencies.items():
            cur = currencies.get(cur_id)
            if not cur:
                continue
            ratio_str = cur.get("airline_partners", {}).get(program)
            if not ratio_str:
                continue
            out.append(_apply_ratio(balance, ratio_str))
        return out


def _apply_ratio(balance: int, ratio: str) -> int:
    """Apply a 'a:b' transfer ratio to a balance (bank:program)."""
    try:
        a, b = ratio.split(":")
        return int(balance * (float(b) / float(a)))
    except (ValueError, ZeroDivisionError):
        return 0
