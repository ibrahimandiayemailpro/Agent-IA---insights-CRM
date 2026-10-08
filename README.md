# Agent IA - Insights CRM partenariats

Lit le Google Sheet « CRM - partenariats » et demande à Claude de produire une liste d'**actions prioritaires**.

## Fonctionnement

1. **Lecture** (`sheet.py`) : onglets `Pipeline`, `Tâches`, `Contacts`, `Notes`, reliés par l'ID entreprise
   (`ENT-xxxx`). Les autres onglets (Accueil, formulaires, tableau de bord) sont ignorés.
2. **Signaux déterministes** (`scoring.py`) : tâches « À faire » en retard ou imminentes, ancienneté de la dernière
   note, absence de prochaine étape, contacts manquants ou sans décideur, poids du statut. Les entreprises dont le
   statut est clos (`CLOSED_WORDS`) sont exclues.
3. **Analyse par Claude** (`agent.py`) : reçoit les 40 entreprises les mieux classées (statut, tâches ouvertes,
   contacts, 3 dernières notes, signaux) et renvoie des actions classées, des risques et des remarques sur la qualité des données.

## Installation

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
```

## Utilisation

Sans compte Google : dans le Sheet, *Fichier > Télécharger > Microsoft Excel (.xlsx)*, puis :

```bash
python -m crm_agent --xlsx "CRM - partenariats.xlsx"
python -m crm_agent --xlsx crm.xlsx --owner Ibrahima --max-actions 5
python -m crm_agent --csv-dir examples/crm          # jeu d'exemple
```

Directement sur le Sheet (compte de service Google Cloud avec les APIs Sheets et Drive activées, clé JSON dans
`~/.config/gspread/service_account.json` ou `--credentials`, feuille partagée avec l'e-mail du compte de service) :

```bash
python -m crm_agent --sheet "https://docs.google.com/spreadsheets/d/<ID>/edit"
```

## Écrire les actions dans le Sheet

```bash
python -m crm_agent --sheet "<URL ou ID>" --owner Ibrahima --write-tab            # onglet « Actions prioritaires »
python -m crm_agent --sheet "<URL ou ID>" --write-tab "Actions du lundi"
```

L'onglet est créé (ou vidé puis réécrit à chaque exécution) avec : résumé, tableau Rang / Priorité / ID / Entreprise /
Action / Pourquoi / Échéance, risques et qualité des données. Aucun autre onglet n'est modifié.
Le compte de service doit être **Éditeur** du Sheet (Lecteur ne suffit plus). Ne renommez pas l'onglet en y mettant
vos propres notes : il est écrasé à chaque exécution.

## À adapter

- `CLOSED_WORDS` (`sheet.py`) : mots désignant une affaire terminée. Seuls « A contacter », « En veille / Pause » et
  « En négociation » ont été vus ; ajoutez vos autres statuts.
- `STATUS_WEIGHT` et `STALE_DAYS` (`scoring.py`) : importance de chaque étape, seuil de « contact froid ».

## Confidentialité

Le contenu des entreprises retenues (dont les notes) est envoyé à l'API Anthropic. Les mails et téléphones ne sont
pas transmis, seulement leur présence.

## Tests

```bash
pytest
```
