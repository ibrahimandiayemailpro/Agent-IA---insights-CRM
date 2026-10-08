# Agent IA - Insights CRM

Lit un Google Sheet utilisé comme CRM et demande à Claude de produire une liste d'**actions prioritaires**.

## Fonctionnement

1. **Lecture** (`sheet.py`) : Google Sheet via compte de service, ou CSV local. Les colonnes sont reconnues par
   alias FR/EN (Nom, Entreprise, Étape, Montant, Dernier contact, Prochaine action, Date prochaine action,
   Responsable, Notes). Les autres colonnes sont transmises telles quelles.
2. **Pré-analyse déterministe** (`scoring.py`) : retards, contacts froids (> 14 j), absence de prochaine action,
   poids du montant. Les deals gagnés/perdus sont exclus.
3. **Analyse par Claude** (`agent.py`) : sortie structurée (actions classées, risques, qualité des données).

## Installation

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
```

## Accès au Google Sheet

1. Console Google Cloud : activer les APIs *Google Sheets* et *Google Drive*, créer un **compte de service**,
   télécharger sa clé JSON (`~/.config/gspread/service_account.json` ou `--credentials`).
2. Partager la feuille (lecture seule suffit) avec l'e-mail du compte de service.

## Utilisation

```bash
python -m crm_agent --sheet "https://docs.google.com/spreadsheets/d/<ID>/edit" --worksheet "Pipeline"
python -m crm_agent --csv examples/crm_exemple.csv --max-actions 5   # test sans Google
python -m crm_agent --csv export.csv --json
```

Les alias de colonnes se règlent dans `ALIASES` (`crm_agent/sheet.py`) ; les mots désignant un deal clos dans `CLOSED_WORDS`.

## Confidentialité

Les lignes retenues (max 60, les plus prioritaires) sont envoyées à l'API Anthropic. N'exposez pas la clé du compte de service.

## Tests

```bash
pytest
```
