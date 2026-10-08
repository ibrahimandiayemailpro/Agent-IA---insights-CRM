"""Écriture du briefing dans un onglet du Google Sheet."""
from __future__ import annotations

from datetime import date

from .agent import Briefing

HEADER = ["Rang", "Priorité", "ID entreprise", "Entreprise", "Action", "Pourquoi", "Échéance"]


def briefing_to_rows(b: Briefing, today: date) -> list[list[str]]:
    """Tableau 2D prêt à écrire : titre, résumé, actions, puis risques et qualité des données."""
    rows: list[list[str]] = [
        [f"Actions prioritaires - généré le {today.strftime('%d/%m/%Y')}"],
        [b.summary],
        [],
        HEADER,
    ]
    for a in sorted(b.actions, key=lambda a: a.rank):
        rows.append([str(a.rank), a.priority, a.company_id, a.company, a.action, a.why, a.deadline])
    if b.risks:
        rows += [[], ["Risques"], *[[r] for r in b.risks]]
    if b.data_quality_notes:
        rows += [[], ["Qualité des données"], *[[n] for n in b.data_quality_notes]]
    return rows


def write_tab(spreadsheet: str, credentials_path: str | None, tab: str, rows: list[list[str]]) -> str:
    """Crée (ou vide) l'onglet `tab` et y écrit `rows`. Le compte de service doit être Éditeur du Sheet.
    Seul cet onglet est modifié ; les onglets du CRM ne sont jamais touchés. Renvoie l'URL de l'onglet."""
    import gspread

    gc = gspread.service_account(filename=credentials_path) if credentials_path else gspread.service_account()
    book = gc.open_by_url(spreadsheet) if spreadsheet.startswith("http") else gc.open_by_key(spreadsheet)
    width = max(len(r) for r in rows)
    try:
        ws = book.worksheet(tab)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(title=tab, rows=len(rows) + 10, cols=max(width, len(HEADER)))
    ws.update(values=rows, range_name="A1", value_input_option="RAW")

    header_row = rows.index(HEADER) + 1
    ws.format("A1", {"textFormat": {"bold": True, "fontSize": 13}})
    ws.format(f"A{header_row}:{chr(64 + len(HEADER))}{header_row}", {"textFormat": {"bold": True}})
    ws.format(f"E{header_row + 1}:F{len(rows)}", {"wrapStrategy": "WRAP"})
    ws.freeze(rows=header_row)
    return f"{book.url}#gid={ws.id}"
