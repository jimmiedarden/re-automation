# Lead pipeline

```
PropStream CSV ──> Airtable (leads base) ──> GoHighLevel
                        │
                        └── re-automation: MAO + offer letters (Phase 3)
```

Make runs the data movement between tools. This repo holds the logic that is easier to write and test as code.

## Phases

| Phase | Flow | Status |
|---|---|---|
| 1 | PropStream CSV → Airtable | Done (Make) |
| 2 | Airtable → GoHighLevel | Done (Make) |
| 3 | Deal analysis and offer letters | In progress (this repo) |

## Deal formula

```
MAO = ARV × 65% − rehab estimate
```

- Offers are MAO rounded **down** to the nearest $500 (`--round-to`).
- Verdicts compare the asking price to MAO:
  - `offer`: asking ≤ MAO
  - `negotiate`: asking is up to 10% over MAO
  - `pass`: asking is more than 10% over MAO, or MAO is $0
  - `no-asking`: no asking price on file

## Airtable fields not yet mapped

These still need columns in Airtable, mappings in Make, or both:

- [ ] Lead Source
- [ ] Motivation Score
- [x] ARV / Rehab Est / MAO (MAO written by `reauto sync`)
- [ ] Property specs (beds, baths, sqft)
- [ ] Offer, contract and close dates
- [ ] Sentiment

## Roadmap

- Acquisition workflows
- Renovation photo management
- Rental automation (Buildium)
- Contractor CRM
- Short-term rental management (Airbnb)
