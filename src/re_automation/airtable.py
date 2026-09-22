"""Minimal Airtable REST client (stdlib only) plus Lead <-> record mapping."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Iterator

from .config import Settings
from .leads import Lead, parse_money

API_ROOT = "https://api.airtable.com/v0"
MAX_BATCH = 10  # Airtable's per-request limit for updates


class AirtableClient:
    def __init__(self, token: str, base_id: str, table: str):
        self.token = token
        self.url = f"{API_ROOT}/{base_id}/{urllib.parse.quote(table, safe='')}"

    def _request(self, method: str, url: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    def list_records(self, formula: str | None = None) -> Iterator[dict]:
        params: dict[str, str] = {}
        if formula:
            params["filterByFormula"] = formula
        while True:
            query = urllib.parse.urlencode(params)
            page = self._request("GET", f"{self.url}?{query}" if query else self.url)
            yield from page.get("records", [])
            if "offset" not in page:
                return
            params["offset"] = page["offset"]

    def update_records(self, updates: list[tuple[str, dict[str, Any]]]) -> None:
        for i in range(0, len(updates), MAX_BATCH):
            chunk = updates[i : i + MAX_BATCH]
            self._request(
                "PATCH",
                self.url,
                {"records": [{"id": rid, "fields": f} for rid, f in chunk]},
            )


def client_from_settings(settings: Settings) -> AirtableClient:
    settings.require_airtable()
    return AirtableClient(
        settings.airtable_token, settings.airtable_base_id, settings.airtable_table
    )


def lead_from_record(record: dict, fields_map: dict[str, str]) -> Lead:
    f = record.get("fields", {})
    text = lambda attr: str(f.get(fields_map[attr], "") or "").strip()  # noqa: E731
    money = lambda attr: parse_money(f.get(fields_map[attr]))  # noqa: E731
    return Lead(
        address=text("address"),
        city=text("city"),
        state=text("state"),
        zip=text("zip"),
        owner_name=text("owner_name"),
        arv=money("arv"),
        rehab=money("rehab"),
        asking=money("asking"),
        record_id=record.get("id"),
    )
