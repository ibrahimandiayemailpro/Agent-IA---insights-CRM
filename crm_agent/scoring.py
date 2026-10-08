"""Pré-analyse déterministe : calcule des signaux fiables avant de solliciter le LLM."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .sheet import Deal

STALE_DAYS = 14  # sans contact au-delà => deal "froid"


@dataclass
class Signals:
    deal: Deal
    days_since_contact: int | None
    days_overdue: int | None  # >0 : action en retard
    flags: list[str]
    score: float  # heuristique 0-100, sert à présélectionner et à départager


def analyze(deal: Deal, today: date, max_amount: float) -> Signals:
    flags: list[str] = []
    score = 0.0

    since = (today - deal.last_contact).days if deal.last_contact else None
    overdue = (today - deal.next_action_date).days if deal.next_action_date else None

    if overdue is not None and overdue > 0:
        flags.append(f"action en retard de {overdue} j")
        score += min(40, 15 + overdue * 2)
    elif overdue is not None and overdue >= -2:
        flags.append("échéance imminente")
        score += 20

    if since is None:
        flags.append("aucun contact enregistré")
        score += 10
    elif since > STALE_DAYS:
        flags.append(f"sans contact depuis {since} j")
        score += min(25, (since - STALE_DAYS) + 10)

    if not deal.next_action and not deal.next_action_date:
        flags.append("aucune prochaine action planifiée")
        score += 15

    if deal.amount and max_amount:
        score += 25 * deal.amount / max_amount

    return Signals(deal, since, overdue, flags, round(min(score, 100), 1))


def analyze_all(deals: list[Deal], today: date) -> list[Signals]:
    """Ne garde que les deals ouverts, triés par score décroissant."""
    open_deals = [d for d in deals if not d.is_closed]
    max_amount = max((d.amount or 0 for d in open_deals), default=0)
    return sorted((analyze(d, today, max_amount) for d in open_deals), key=lambda s: -s.score)
