from datetime import date

from crm_agent.scoring import analyze_all
from crm_agent.sheet import load_csv_dir, parse_date

TODAY = date(2026, 10, 8)
DIR = "examples/crm"


def test_join_and_closed_filtered():
    companies = {c.id: c for c in load_csv_dir(DIR)}
    assert len(companies["ENT-0004"].tasks) == 3 and len(companies["ENT-0005"].notes) == 3
    assert companies["ENT-0099"].is_closed
    assert "ENT-0099" not in [s.company.id for s in analyze_all(list(companies.values()), TODAY)]


def test_signals():
    s = {x.company.id: x for x in analyze_all(load_csv_dir(DIR), TODAY)}
    assert s["ENT-0004"].overdue_tasks == 1 and s["ENT-0004"].open_tasks == 1  # annulée/faite ignorées
    assert any("sans interaction" in f or "dernière interaction" in f for f in s["ENT-0005"].flags)
    assert any("aucun contact" in f for f in s["ENT-0008"].flags)
    assert any("décideur" in f for f in s["ENT-0001"].flags)
    # négociation avec tâche en retard > simple « à contacter »
    assert s["ENT-0004"].score > s["ENT-0001"].score


def test_owner_filter_and_dates():
    assert analyze_all(load_csv_dir(DIR), TODAY, owner="Autre") == []
    assert len(analyze_all(load_csv_dir(DIR), TODAY, owner="ibrahima")) == 5
    assert parse_date("07/08/2026") == date(2026, 8, 7)


def test_briefing_to_rows():
    from crm_agent.agent import Action, Briefing
    from crm_agent.output import HEADER, briefing_to_rows

    b = Briefing(summary="Résumé.", risks=["Backlog"], data_quality_notes=[],
                 actions=[Action(rank=2, company_id="ENT-2", company="B", priority="haute", action="x", why="y", deadline="d"),
                          Action(rank=1, company_id="ENT-1", company="A", priority="critique", action="x", why="y", deadline="d")])
    rows = briefing_to_rows(b, TODAY)
    i = rows.index(HEADER)
    assert rows[i + 1][2] == "ENT-1" and rows[i + 2][2] == "ENT-2"  # trié par rang
    assert ["Risques"] in rows and ["Backlog"] in rows and ["Qualité des données"] not in rows
