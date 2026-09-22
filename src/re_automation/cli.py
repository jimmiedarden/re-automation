"""`reauto` command line interface."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from . import airtable
from .analysis import analyze
from .config import Settings, load_dotenv
from .leads import Lead, read_csv
from .offers import DEFAULT_ROUND_TO, load_template, offer_amount, offer_filename, render_offer


def _money(value: float | None) -> str:
    return "" if value is None else f"${value:,.0f}"


def _analyzable(lead: Lead) -> bool:
    return lead.arv is not None and lead.rehab is not None


def cmd_mao(args: argparse.Namespace, settings: Settings) -> int:
    result = analyze(args.arv, args.rehab, args.asking, pct=args.pct or settings.mao_percent)
    print(f"MAO: {_money(result.mao)}")
    if result.asking is not None:
        print(f"Asking: {_money(result.asking)}  Spread: {_money(result.spread)}  -> {result.verdict}")
    return 0


def cmd_analyze(args: argparse.Namespace, settings: Settings) -> int:
    pct = args.pct or settings.mao_percent
    leads = read_csv(args.csv, rehab_per_sqft=args.rehab_per_sqft)
    rows, skipped = [], 0
    for lead in leads:
        if not _analyzable(lead):
            skipped += 1
            continue
        r = analyze(lead.arv, lead.rehab, lead.asking, pct=pct)
        rows.append((lead, r))
    rows.sort(key=lambda lr: (lr[1].spread is None, -(lr[1].spread or 0)))

    out = open(args.out, "w", newline="") if args.out else sys.stdout
    try:
        w = csv.writer(out)
        w.writerow(["address", "owner", "arv", "rehab", "asking", "mao", "spread", "verdict"])
        for lead, r in rows:
            w.writerow([lead.full_address, lead.owner_name, lead.arv, lead.rehab,
                        lead.asking, r.mao, r.spread, r.verdict])
    finally:
        if args.out:
            out.close()
    print(f"Analyzed {len(rows)} leads; skipped {skipped} missing ARV or rehab.", file=sys.stderr)
    return 0


def cmd_sync(args: argparse.Namespace, settings: Settings) -> int:
    """Compute MAO for Airtable leads that have ARV + rehab, and write it back."""
    client = airtable.client_from_settings(settings)
    fields = settings.fields
    updates = []
    for record in client.list_records():
        lead = airtable.lead_from_record(record, fields)
        if not _analyzable(lead):
            continue
        r = analyze(lead.arv, lead.rehab, lead.asking, pct=settings.mao_percent)
        new = {fields["mao"]: r.mao}
        if fields.get("verdict"):
            new[fields["verdict"]] = r.verdict
        current = record.get("fields", {})
        if all(current.get(k) == v for k, v in new.items()):
            continue
        updates.append((lead.record_id, new))
        print(f"{lead.full_address}: MAO {_money(r.mao)} ({r.verdict})")
    if args.dry_run:
        print(f"Dry run: {len(updates)} records would be updated.")
    else:
        client.update_records(updates)
        print(f"Updated {len(updates)} records.")
    return 0


def cmd_offers(args: argparse.Namespace, settings: Settings) -> int:
    if args.csv:
        leads = read_csv(args.csv, rehab_per_sqft=args.rehab_per_sqft)
    else:
        client = airtable.client_from_settings(settings)
        leads = [airtable.lead_from_record(r, settings.fields) for r in client.list_records()]

    template = load_template(args.template)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for lead in leads:
        if not _analyzable(lead):
            continue
        r = analyze(lead.arv, lead.rehab, lead.asking, pct=settings.mao_percent)
        if args.only_offers and r.verdict == "pass":
            continue
        amount = offer_amount(r.mao, args.round_to)
        if amount <= 0:
            continue
        (out_dir / offer_filename(lead)).write_text(render_offer(lead, amount, settings, template))
        written += 1
    print(f"Wrote {written} offer letters to {out_dir}/")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="reauto", description="Real estate automation tools")
    sub = p.add_subparsers(dest="command", required=True)

    m = sub.add_parser("mao", help="Calculate MAO for one property")
    m.add_argument("arv", type=float)
    m.add_argument("rehab", type=float)
    m.add_argument("--asking", type=float)
    m.add_argument("--pct", type=float, help="ARV percentage (default 0.65 or MAO_PERCENT)")
    m.set_defaults(func=cmd_mao)

    a = sub.add_parser("analyze", help="Score a PropStream CSV export")
    a.add_argument("csv")
    a.add_argument("--out", help="Write results CSV here instead of stdout")
    a.add_argument("--pct", type=float)
    a.add_argument("--rehab-per-sqft", type=float,
                   help="Estimate rehab as sqft x rate when the CSV has no rehab column")
    a.set_defaults(func=cmd_analyze)

    s = sub.add_parser("sync", help="Write MAO back to Airtable leads")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_sync)

    o = sub.add_parser("offers", help="Generate offer letters")
    o.add_argument("--csv", help="Read leads from a CSV instead of Airtable")
    o.add_argument("--out", default="offers")
    o.add_argument("--template", help="Custom Markdown template")
    o.add_argument("--round-to", type=int, default=DEFAULT_ROUND_TO,
                   help="Round offers down to this amount (default 500)")
    o.add_argument("--rehab-per-sqft", type=float)
    o.add_argument("--all", dest="only_offers", action="store_false",
                   help="Include leads whose asking price is well above MAO")
    o.set_defaults(func=cmd_offers)
    return p


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)
    return args.func(args, Settings.from_env())


if __name__ == "__main__":
    raise SystemExit(main())
