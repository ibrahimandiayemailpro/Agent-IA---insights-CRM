"""Lecture du Google Sheet (ou d'un CSV) et normalisation des colonnes du CRM."""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime

# Nom canonique -> alias acceptés (en-têtes normalisés : minuscules, sans accents).
ALIASES: dict[str, list[str]] = {
    "name": ["nom", "name", "contact", "client", "prospect", "nom du contact"],
    "company": ["entreprise", "societe", "company", "organisation"],
    "stage": ["etape", "statut", "status", "stage", "phase", "pipeline"],
    "amount": ["montant", "valeur", "amount", "value", "ca potentiel", "budget"],
    "last_contact": ["dernier contact", "derniere interaction", "last contact", "date dernier contact"],
    "next_action": ["prochaine action", "next action", "action suivante", "next step"],
    "next_action_date": ["date prochaine action", "echeance", "next action date", "date relance", "relance"],
    "owner": ["responsable", "owner", "commercial", "assigne a"],
    "notes": ["notes", "commentaires", "commentaire", "comments", "remarques"],
}

CLOSED_WORDS = ("gagne", "won", "perdu", "lost", "clos", "closed", "abandon")
DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%Y")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip().lower()


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value: str) -> float | None:
    cleaned = re.sub(r"[^\d,.\-]", "", (value or "").replace(" ", "").replace(" ", ""))
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


@dataclass
class Deal:
    row: int  # numéro de ligne dans la feuille (en-tête = ligne 1)
    name: str = ""
    company: str = ""
    stage: str = ""
    amount: float | None = None
    last_contact: date | None = None
    next_action: str = ""
    next_action_date: date | None = None
    owner: str = ""
    notes: str = ""
    extra: dict[str, str] = field(default_factory=dict)  # colonnes non reconnues

    @property
    def is_closed(self) -> bool:
        return any(w in _norm(self.stage) for w in CLOSED_WORDS)


def rows_to_deals(rows: list[list[str]]) -> list[Deal]:
    """`rows` = valeurs brutes, première ligne = en-têtes. Les lignes vides sont ignorées."""
    if not rows:
        return []
    headers = [_norm(h) for h in rows[0]]
    mapping: dict[int, str] = {}
    for idx, h in enumerate(headers):
        for canon, aliases in ALIASES.items():
            if h in aliases and canon not in mapping.values():
                mapping[idx] = canon
                break

    deals: list[Deal] = []
    for line_no, raw in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in raw):
            continue
        deal = Deal(row=line_no)
        for idx, cell in enumerate(raw):
            cell = cell.strip()
            canon = mapping.get(idx)
            if canon in ("last_contact", "next_action_date"):
                setattr(deal, canon, parse_date(cell))
            elif canon == "amount":
                deal.amount = parse_amount(cell)
            elif canon:
                setattr(deal, canon, cell)
            elif cell and idx < len(rows[0]) and rows[0][idx].strip():
                deal.extra[rows[0][idx].strip()] = cell
        deals.append(deal)
    return deals


def load_csv(path: str) -> list[Deal]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return rows_to_deals([list(r) for r in csv.reader(f)])


def load_google_sheet(spreadsheet: str, worksheet: str | None, credentials_path: str | None) -> list[Deal]:
    """`spreadsheet` = URL, ID ou titre. Auth par compte de service (la feuille doit lui être partagée)."""
    import gspread

    gc = gspread.service_account(filename=credentials_path) if credentials_path else gspread.service_account()
    if spreadsheet.startswith("http"):
        book = gc.open_by_url(spreadsheet)
    elif re.fullmatch(r"[\w-]{30,}", spreadsheet):
        book = gc.open_by_key(spreadsheet)
    else:
        book = gc.open(spreadsheet)
    ws = book.worksheet(worksheet) if worksheet else book.sheet1
    return rows_to_deals(ws.get_all_values())
