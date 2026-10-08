from __future__ import annotations

import argparse
import sys
from datetime import date

from .agent import Briefing, build_briefing
from .scoring import analyze_all
from .sheet import load_csv, load_google_sheet

ICONS = {"critique": "🔴", "haute": "🟠", "moyenne": "🟡"}


def render(b: Briefing) -> str:
    out = ["# Actions prioritaires CRM", "", b.summary, ""]
    for a in sorted(b.actions, key=lambda a: a.rank):
        out += [
            f"## {a.rank}. {ICONS[a.priority]} {a.deal} (ligne {a.row}) - {a.deadline}",
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
    src.add_argument("--sheet", help="URL, ID ou titre du Google Sheet")
    src.add_argument("--csv", help="Fichier CSV local (export du CRM)")
    p.add_argument("--worksheet", help="Nom de l'onglet (défaut : premier)")
    p.add_argument("--credentials", help="JSON du compte de service (défaut : ~/.config/gspread/service_account.json)")
    p.add_argument("--max-actions", type=int, default=7)
    p.add_argument("--json", action="store_true", help="Sortie JSON au lieu de Markdown")
    args = p.parse_args()

    deals = load_csv(args.csv) if args.csv else load_google_sheet(args.sheet, args.worksheet, args.credentials)
    today = date.today()
    signals = analyze_all(deals, today)
    if not signals:
        print("Aucune affaire ouverte trouvée dans la feuille.", file=sys.stderr)
        return 1

    briefing = build_briefing(signals, today, max_actions=args.max_actions)
    print(briefing.model_dump_json(indent=2) if args.json else render(briefing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
