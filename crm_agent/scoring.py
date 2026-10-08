"""Pré-analyse déterministe : signaux fiables calculés avant de solliciter le LLM."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .sheet import Company, norm

STALE_DAYS = 14  # sans interaction au-delà => affaire qui refroidit

# Poids de l'étape : plus l'affaire est avancée, plus elle mérite d'attention. Statuts inconnus => 10.
STATUS_WEIGHT = {"en negociation": 30, "en discussion": 25, "rendez-vous": 22, "rdv": 22, "a contacter": 12,
                 "contacte": 15, "en veille": 3, "pause": 3}


@dataclass
class Signals:
    company: Company
    days_since_interaction: int | None
    open_tasks: int
    overdue_tasks: int
    max_overdue_days: int
    flags: list[str]
    score: float


def _status_weight(status: str) -> int:
    s = norm(status)
    for key, w in STATUS_WEIGHT.items():
        if key in s:
            return w
    return 10


def analyze(c: Company, today: date) -> Signals:
    flags: list[str] = []
    score = float(_status_weight(c.status))

    dated = [n.date for n in c.notes if n.date]
    last = max(dated) if dated else None
    ref = last or c.added
    since = (today - ref).days if ref else None
    if since is not None and since > STALE_DAYS:
        label = "dernière interaction" if last else "ajoutée sans aucune interaction"
        flags.append(f"{label} il y a {since} j")
        score += min(25, since - STALE_DAYS + 8)

    open_tasks = [t for t in c.tasks if t.is_open]
    overdue = [t for t in open_tasks if t.due and t.due < today]
    max_over = max(((today - t.due).days for t in overdue), default=0)
    if overdue:
        flags.append(f"{len(overdue)} tâche(s) en retard (jusqu'à {max_over} j)")
        score += min(30, 10 + max_over // 3 + 3 * len(overdue))
    soon = [t for t in open_tasks if t.due and 0 <= (t.due - today).days <= 3]
    if soon:
        flags.append(f"{len(soon)} tâche(s) à échéance sous 3 j")
        score += 12
    if not open_tasks and not c.is_closed and norm(c.status) not in ("en veille / pause",):
        flags.append("aucune tâche ouverte : prochaine étape non planifiée")
        score += 10

    if not c.contacts:
        flags.append("aucun contact enregistré")
        score += 6
    elif not any(ct.is_decision_maker for ct in c.contacts):
        flags.append("aucun décideur identifié parmi les contacts")
        score += 4
    if c.contacts and not any(ct.has_mail or ct.has_phone for ct in c.contacts):
        flags.append("contacts sans mail ni téléphone")

    return Signals(c, since, len(open_tasks), len(overdue), max_over, flags, round(min(score, 100), 1))


def analyze_all(companies: list[Company], today: date, owner: str | None = None) -> list[Signals]:
    """Entreprises ouvertes (filtrables par responsable), triées par score décroissant."""
    pool = [c for c in companies if not c.is_closed and (not owner or norm(owner) in norm(c.owner))]
    return sorted((analyze(c, today) for c in pool), key=lambda s: -s.score)
