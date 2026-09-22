"""Lead records and loading them from a PropStream CSV export."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

# Lead attribute -> accepted CSV column names (first match wins, case-insensitive).
CSV_COLUMNS = {
    "address": ["Address", "Property Address", "Street Address"],
    "city": ["City", "Property City"],
    "state": ["State", "Property State"],
    "zip": ["Zip", "Zip Code", "Property Zip"],
    "owner_name": ["Owner Name", "Owner 1 Full Name"],
    "owner_first": ["Owner 1 First Name", "Owner First Name"],
    "owner_last": ["Owner 1 Last Name", "Owner Last Name"],
    "arv": ["ARV", "After Repair Value", "Est. Value", "Estimated Value"],
    "rehab": ["Rehab Est", "Rehab Estimate", "Rehab"],
    "asking": ["Asking Price", "List Price", "Listing Price"],
    "sqft": ["Building Sqft", "Living Sqft", "Sqft", "Square Feet"],
}


def parse_money(value: object) -> float | None:
    """'$215,000' -> 215000.0; blanks and junk -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


@dataclass
class Lead:
    address: str
    city: str = ""
    state: str = ""
    zip: str = ""
    owner_name: str = ""
    arv: float | None = None
    rehab: float | None = None
    asking: float | None = None
    sqft: float | None = None
    record_id: str | None = None  # Airtable record id, when loaded from Airtable

    @property
    def full_address(self) -> str:
        locality = " ".join(p for p in (self.state, self.zip) if p)
        return ", ".join(p for p in (self.address, self.city, locality) if p)


def _pick(row: Mapping[str, str], names: Iterable[str]) -> str:
    lowered = {k.strip().lower(): v for k, v in row.items() if k}
    for name in names:
        value = lowered.get(name.lower())
        if value not in (None, ""):
            return str(value).strip()
    return ""


def lead_from_row(row: Mapping[str, str], rehab_per_sqft: float | None = None) -> Lead:
    get = lambda attr: _pick(row, CSV_COLUMNS[attr])  # noqa: E731
    owner = get("owner_name") or " ".join(
        p for p in (get("owner_first"), get("owner_last")) if p
    )
    sqft = parse_money(get("sqft"))
    rehab = parse_money(get("rehab"))
    if rehab is None and rehab_per_sqft is not None and sqft:
        rehab = round(sqft * rehab_per_sqft, 2)
    return Lead(
        address=get("address"),
        city=get("city"),
        state=get("state"),
        zip=get("zip"),
        owner_name=owner,
        arv=parse_money(get("arv")),
        rehab=rehab,
        asking=parse_money(get("asking")),
        sqft=sqft,
    )


def read_csv(path: str | Path, rehab_per_sqft: float | None = None) -> list[Lead]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [
            lead
            for lead in (lead_from_row(r, rehab_per_sqft) for r in csv.DictReader(f))
            if lead.address
        ]
