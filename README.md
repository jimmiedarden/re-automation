# re-automation

Real estate automation tools for the PropStream → Airtable → GoHighLevel lead pipeline. See [docs/pipeline.md](docs/pipeline.md) for the full picture.

**Phase 3 (current):** deal analysis and offer letters.

- **MAO:** `ARV × 65% − rehab`
- **Analyze** a PropStream CSV export and rank leads by spread (MAO minus asking price)
- **Sync** MAO back to Airtable
- **Generate** offer letters from a Markdown template

## Setup

Requires Python 3.10 or newer. There are no runtime dependencies.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in your Airtable token, base ID and signature
```

## Usage

```bash
# One property
reauto mao 200000 30000 --asking 90000
# MAO: $100,000
# Asking: $90,000  Spread: $10,000  -> offer

# Rank a PropStream export. Use --rehab-per-sqft when the CSV has no rehab column.
reauto analyze propstream.csv --rehab-per-sqft 25 --out results.csv

# Write MAO to Airtable (preview first)
reauto sync --dry-run
reauto sync

# Offer letters, from Airtable or a CSV
reauto offers --out offers/
reauto offers --csv propstream.csv --rehab-per-sqft 25 --out offers/
```

By default, `offers` skips leads with a `pass` verdict. Add `--all` to include them. To use your own wording, pass `--template my_letter.md`; the placeholders are listed in `src/re_automation/templates/offer_letter.md`.

## Configuration

All settings come from environment variables or `.env`. See [.env.example](.env.example). If your Airtable column names differ from the defaults, set `AIRTABLE_FIELD_<NAME>`.

## Development

```bash
pytest
```

Keep secrets, lender or legal documents, and personal financial details out of this repo.
