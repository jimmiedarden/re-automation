"""Settings loaded from environment variables (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .analysis import DEFAULT_MAO_PERCENT


def load_dotenv(path: str | Path = ".env") -> None:
    """Minimal .env loader: KEY=VALUE lines; existing env vars win."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


# Lead attribute -> default Airtable column name. Override any of them with
# AIRTABLE_FIELD_<ATTR>, e.g. AIRTABLE_FIELD_ARV="After Repair Value".
DEFAULT_AIRTABLE_FIELDS = {
    "address": "Property Address",
    "city": "City",
    "state": "State",
    "zip": "Zip",
    "owner_name": "Owner Name",
    "arv": "ARV",
    "rehab": "Rehab Est",
    "asking": "Asking Price",
    "mao": "MAO",
    # Optional: only written when AIRTABLE_FIELD_VERDICT is set.
    "verdict": "",
}


@dataclass
class Settings:
    airtable_token: str = ""
    airtable_base_id: str = ""
    airtable_table: str = "Leads"
    mao_percent: float = DEFAULT_MAO_PERCENT
    buyer_name: str = ""
    buyer_phone: str = ""
    buyer_email: str = ""
    offer_valid_days: int = 7
    fields: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_AIRTABLE_FIELDS))

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        fields = {
            attr: env.get(f"AIRTABLE_FIELD_{attr.upper()}", default)
            for attr, default in DEFAULT_AIRTABLE_FIELDS.items()
        }
        return cls(
            airtable_token=env.get("AIRTABLE_TOKEN", ""),
            airtable_base_id=env.get("AIRTABLE_BASE_ID", ""),
            airtable_table=env.get("AIRTABLE_TABLE", "Leads"),
            mao_percent=float(env.get("MAO_PERCENT", DEFAULT_MAO_PERCENT)),
            buyer_name=env.get("BUYER_NAME", ""),
            buyer_phone=env.get("BUYER_PHONE", ""),
            buyer_email=env.get("BUYER_EMAIL", ""),
            offer_valid_days=int(env.get("OFFER_VALID_DAYS", 7)),
            fields=fields,
        )

    def require_airtable(self) -> None:
        missing = [
            name
            for name, value in (
                ("AIRTABLE_TOKEN", self.airtable_token),
                ("AIRTABLE_BASE_ID", self.airtable_base_id),
            )
            if not value
        ]
        if missing:
            raise SystemExit(f"Missing settings: {', '.join(missing)} (see .env.example)")
