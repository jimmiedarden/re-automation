from datetime import date

from re_automation.airtable import lead_from_record
from re_automation.cli import main
from re_automation.config import DEFAULT_AIRTABLE_FIELDS, Settings
from re_automation.leads import Lead, parse_money, read_csv
from re_automation.offers import offer_amount, offer_filename, render_offer

CSV = """﻿Address,City,State,Zip,Owner 1 First Name,Owner 1 Last Name,Est. Value,Building Sqft,Asking Price
123 Main St,Richmond,VA,23220,Pat,Lee,"$200,000",1200,"$90,000"
456 Oak Ave,Petersburg,VA,23803,Sam,Ray,"$150,000",1000,
,,,,,,,,
"""


def write_csv(tmp_path):
    p = tmp_path / "leads.csv"
    p.write_text(CSV, encoding="utf-8")
    return p


def test_parse_money():
    assert parse_money("$215,000") == 215_000
    assert parse_money("") is None
    assert parse_money("n/a") is None
    assert parse_money(12) == 12.0


def test_read_propstream_csv(tmp_path):
    leads = read_csv(write_csv(tmp_path), rehab_per_sqft=25)
    assert len(leads) == 2  # blank row dropped
    first = leads[0]
    assert first.owner_name == "Pat Lee"
    assert first.arv == 200_000
    assert first.rehab == 30_000
    assert first.asking == 90_000
    assert first.full_address == "123 Main St, Richmond, VA 23220"


def test_lead_from_airtable_record():
    record = {"id": "rec1", "fields": {"Property Address": "1 A St", "ARV": 100000, "Rehab Est": "$10,000"}}
    lead = lead_from_record(record, DEFAULT_AIRTABLE_FIELDS)
    assert (lead.record_id, lead.address, lead.arv, lead.rehab) == ("rec1", "1 A St", 100_000, 10_000)


def test_offer_amount_rounds_down():
    assert offer_amount(100_499) == 100_000
    assert offer_amount(100_500) == 100_500
    assert offer_amount(100_499, round_to=0) == 100_499


def test_render_offer():
    settings = Settings(buyer_name="Buyer Co", buyer_phone="555-0100", offer_valid_days=7)
    lead = Lead(address="1 A St", city="Richmond", state="VA", zip="23220", owner_name="Pat Lee")
    text = render_offer(lead, 100_000, settings, today=date(2026, 9, 22))
    assert "$100,000" in text
    assert "Dear Pat Lee" in text
    assert "September 29, 2026" in text
    assert "Buyer Co" in text and "555-0100" in text
    assert "$" + "owner_name" not in text
    assert offer_filename(lead) == "offer-1-a-st-richmond-va-23220.md"


def test_cli_analyze_and_offers(tmp_path, capsys):
    src = write_csv(tmp_path)
    out = tmp_path / "results.csv"
    assert main(["analyze", str(src), "--rehab-per-sqft", "25", "--out", str(out)]) == 0
    lines = out.read_text().splitlines()
    assert lines[0].startswith("address,")
    assert "offer" in lines[1]  # 123 Main St: MAO 100k vs asking 90k

    offers_dir = tmp_path / "offers"
    assert main(["offers", "--csv", str(src), "--rehab-per-sqft", "25", "--out", str(offers_dir)]) == 0
    assert len(list(offers_dir.glob("*.md"))) == 2


def test_cli_mao(capsys):
    assert main(["mao", "200000", "30000", "--asking", "90000"]) == 0
    out = capsys.readouterr().out
    assert "MAO: $100,000" in out and "offer" in out
