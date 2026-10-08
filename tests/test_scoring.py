from datetime import date

from crm_agent.scoring import analyze_all
from crm_agent.sheet import load_csv, parse_amount, parse_date

TODAY = date(2026, 10, 8)


def test_parsing():
    assert parse_amount("45 000 €") == 45000
    assert parse_amount("1.234,50") == 1234.5
    assert parse_date("12/09/2026") == date(2026, 9, 12)
    assert parse_date("nope") is None


def test_columns_and_closed_deals_filtered():
    deals = load_csv("examples/crm_exemple.csv")
    assert len(deals) == 5 and deals[0].company == "Acme" and deals[0].row == 2
    signals = analyze_all(deals, TODAY)
    assert "Umbrella" not in [s.deal.company for s in signals]  # deal gagné exclu


def test_overdue_and_stale_rank_high():
    signals = analyze_all(load_csv("examples/crm_exemple.csv"), TODAY)
    top = {s.deal.company: s for s in signals}
    assert any("en retard" in f for f in top["Acme"].flags)
    assert any("aucune prochaine action" in f for f in top["Initech"].flags)
    assert signals[0].score >= signals[-1].score
