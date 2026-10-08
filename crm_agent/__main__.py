from __future__ import annotations

import argparse
import sys
from datetime import date

from .agent import Briefing, build_briefing
from .scoring import analyze_all
from .sheet import load_csv_dir, load_google_sheet, load_xlsx

ICONS = {"critique": "🔴", "haute": "🟠", "moyenne": "🟡"}


def render(b: Briefing) -> str:
    out = ["# Actions prioritaires CRM", "", b.summary, ""]
    for a in sorted(b.actions, key=lambda a: a.rank):
        out += [
            f"## {a.rank}. {ICONS[a.priority]} {a.company} ({a.company_id}) - {a.deadline}",
            f"**Action :** {a.action}",
            f"**Pourquoi :** {a.why}",
            "",
        ]
    if b.risks:
        out += ["## Risques", *[f"- {r}" for r in b.risks], ""]
    if b.data_quality_notes:
        out += ["## Qualité des données", *[f"- {n}" for n in b.data_quality_notes], ""]
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(prog="crm_agent", description="Actions prioritaires à partir d'un CRM Google Sheet")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--sheet", help="URL ou ID du Google Sheet (compte de service requis)")
    src.add_argument("--xlsx", help="Export .xlsx du Sheet (Fichier > Télécharger), sans compte Google")
    src.add_argument("--csv-dir", help="Dossier avec Pipeline.csv, Tâches.csv, Contacts.csv, Notes.csv")
    p.add_argument("--credentials", help="JSON du compte de service (défaut : ~/.config/gspread/service_account.json)")
    p.add_argument("--owner", help="Ne garder que les entreprises dont la personne en charge correspond (ex. Ibrahima)")
    p.add_argument("--max-actions", type=int, default=7)
    p.add_argument("--json", action="store_true", help="Sortie JSON au lieu de Markdown")
    args = p.parse_args()

    if args.xlsx:
        companies = load_xlsx(args.xlsx)
    elif args.csv_dir:
        companies = load_csv_dir(args.csv_dir)
    else:
        companies = load_google_sheet(args.sheet, args.credentials)
    today = date.today()
    signals = analyze_all(companies, today, args.owner)
    if not signals:
        print("Aucune entreprise ouverte trouvée dans la feuille.", file=sys.stderr)
        return 1

    briefing = build_briefing(signals, today, max_actions=args.max_actions)
    print(briefing.model_dump_json(indent=2) if args.json else render(briefing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
