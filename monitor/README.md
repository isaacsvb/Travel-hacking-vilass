# Award Check (on-demand) + Kiro

A small local tool that checks premium-award availability **when you ask** — no background daemon, no alerts. You run it (or Kiro runs it for you in a session), it searches seats.aero, computes cents-per-mile (CPM) against the toolkit's reference data, and prints ranked opportunities.

## How it fits together

```
You ask  ──▶  th-monitor check ...  ──▶  searches seats.aero, computes CPM
                      │                   writes monitor/output/latest.json
                      ▼
               Kiro reads latest.json (or runs the command for you) and
               explains the ranked opportunities with the math
```

- **On-demand only.** It does not run in the background and does not send Telegram/n8n alerts. (The spec for an autonomous alerting version lives in `docs/specs/backend-milhas/` if you ever want it.)
- **Free-first (with a caveat on how).** seats.aero has **no keyless REST endpoint** — its Partner API always requires a key. The genuinely free path is the **seats.aero MCP server** (next ~60 days), which an MCP client (Kiro) calls. So the free flow is: Kiro runs the seats.aero MCP search, saves the JSON, and this tool ranks it (`--mcp-json`). Set `SEATS_AERO_API_KEY` to let the CLI query the Partner API directly instead (live search + beyond 60 days).

## Install (one time)

```bash
pip install -e monitor          # from the repo root
# or, without installing:  cd monitor && PYTHONPATH=src python3 -m th_monitor.cli ...
```

## Run a check

**Free path (no key):** let Kiro call the seats.aero MCP tool, save its JSON, then rank it:

```bash
th-monitor check --from SSA --to YQR --start 2026-12-22 --end 2027-01-25 \
  --cabin economy --seats 2 --mcp-json output/mcp-raw.json
```

**Keyed path (`SEATS_AERO_API_KEY` set):** the CLI queries the Partner API directly:

```bash
th-monitor check --from SFO --to NRT --start 2026-12-01 --end 2026-12-20 --cabin business
```

Options:
- `--cabin` economy | premium_economy | business | first
- `--seats N` minimum seats (default 1)
- `--mcp-json FILE` keyless: availability JSON that Kiro fetched from the seats.aero MCP
- `--balances balances.json` gate results by what you can actually reach (direct + transfers). Copy `balances.example.json` to `balances.json` and fill it in. Never commit real balances.
- `--all` show everything, not just high-value / sweet spots
- `--json` machine-readable output (also written to `monitor/output/latest.json`)

## Use it through Kiro

In a Kiro session, type `#run-award-check` (a manual steering file) and tell Kiro the route/dates. Kiro runs the command, reads the JSON, and presents the opportunities with the CPM math. Nothing runs unless you ask.

## What it does with the result

- Gates each award by **reachability** (direct balance or a transfer path in `data/transfer-partners.json`).
- Computes **CPM** = (cash − award fees) / miles × 100 and classifies it against each program's floor/ceiling in `data/points-valuations.json`.
- Flags **sweet spots** from `data/sweet-spots.json`.
- Marks **stale** cached data (24h+) as needing verification before booking.
- A source being down is reported as a warning, **never** as "no availability".

## Tests

```bash
cd monitor && PYTHONPATH=src python3 -m pytest -q
```
