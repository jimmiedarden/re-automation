"""Offer letter generation from the Markdown template."""

from __future__ import annotations

import math
import re
from datetime import date, timedelta
from importlib import resources
from pathlib import Path
from string import Template

from .config import Settings
from .leads import Lead

DEFAULT_ROUND_TO = 500


def offer_amount(mao: float, round_to: int = DEFAULT_ROUND_TO) -> int:
    """Round MAO down to a clean number so the offer never exceeds it."""
    if round_to <= 0:
        return int(mao)
    return int(math.floor(mao / round_to) * round_to)


def load_template(path: str | Path | None = None) -> Template:
    if path:
        return Template(Path(path).read_text())
    text = resources.files("re_automation").joinpath("templates/offer_letter.md").read_text()
    return Template(text)


def render_offer(
    lead: Lead,
    amount: int,
    settings: Settings,
    template: Template | None = None,
    today: date | None = None,
) -> str:
    today = today or date.today()
    contact = " | ".join(p for p in (settings.buyer_phone, settings.buyer_email) if p)
    return (template or load_template()).safe_substitute(
        date=today.strftime("%B %d, %Y"),
        owner_name=lead.owner_name or "Property Owner",
        property_address=lead.full_address,
        offer_amount=f"${amount:,}",
        valid_until=(today + timedelta(days=settings.offer_valid_days)).strftime("%B %d, %Y"),
        buyer_name=settings.buyer_name,
        buyer_contact=contact,
    )


def offer_filename(lead: Lead) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", lead.full_address.lower()).strip("-")
    return f"offer-{slug or 'property'}.md"
