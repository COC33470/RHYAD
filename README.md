# RHYAD Document Engine

Générateur documentaire YAML pour le projet RHYAD.

Le dépôt produit des livrables DOCX/PDF avec la charte CEVA, le logo, le cartouche documentaire, la page de garde, le tableau `Document Control`, le pied de page et la table des matières Word.

## Référentiel Officiel

Le référentiel documentaire validé est décrit dans `config/rhyad_repository.yaml`.

```text
000 — Documents de Gouvernance Projet
- 000 Modèle documentaire RHYAD-CEVA
- 001 Charte Projet
- 001A ACAP – Analyse de Contexte et d’Adaptation du Projet
- 002 Programme Fonctionnel
- 003 Glossaire
- 004 Registre des Risques
- 005 Registre des Décisions
- 006 Plan Directeur Documentaire

100 — Fonctions du Programme Fonctionnel
- F01 Réception et Expédition
- F02 Stockage des Matières Premières et Consommables
- F03 Préparation des Matières Premières et Solutions
- F04 Production des Autovaccins
- F05 Conditionnement et Expédition des Produits
- F06 Gestion des Flux
- F07 Lavage, Stérilisation et Préparation des Équipements
- F08 Contrôle Qualité
- F09 Utilités Industrielles
- F10 Maintenance et Exploitation Technique
- F11 Gestion des Déchets et Effluents
- F12 Sûreté, Protection des Actifs et Contrôle des Accès
- F13 Systèmes d’Information, Automatismes et Cybersécurité
- F14 Administration, Formation et Services Généraux
- F15 Gouvernance du Campus et Fonctions Transverses

200 — DT
- DT-000 Registre des Hypothèses de Conception
- DT-F01-xx à DT-F15-xx

300 — Design Basis
- DB-001 Process
- DB-002 Architecture
- DB-003 CVC / HVAC
- DB-004 Utilités
- DB-005 Électricité
- DB-006 IT / OT
- DB-007 Maintenance
- DB-008 Sécurité / Sûreté
- DB-009 Logistique
- DB-010 Instrumentation & Automatisme

400 — Réunions
- R00 Kick-off
- R01 Réunion de Programmation Fonctionnelle
- R02 Réunion IT / OT
- R03 Process
- R04 Utilités

500 — Registres Projet
- REG-001 Registre des Actions
- REG-002 Registre des Décisions
- REG-003 Registre des Risques
- REG-004 Registre des Hypothèses
- REG-005 Registre des Interfaces

600 — Dossiers d’Études
- APS
- APD
- PRO
- DCE
- EXE
- VISA
- DOE
```

## Documents YAML

Les documents générables sont définis dans `config/documents/<CODE>.yaml`.

Squelettes actuellement disponibles :

- `000` — Modèle documentaire RHYAD-CEVA
- `001` — Charte Projet
- `001A` — ACAP – Analyse de Contexte et d’Adaptation du Projet
- `002` — Programme Fonctionnel
- `003` — Glossaire
- `006` — Plan Directeur Documentaire
- `F01` — Réception et Expédition

Ces fichiers sont des squelettes. Les contenus complets ne doivent être rédigés qu’après validation.

## Sorties

Les sorties sont classées par famille officielle :

```text
output/docx/000 ... output/docx/600
output/pdf/000  ... output/pdf/600
output/xlsx/000 ... output/xlsx/600
```

Exemples :

```text
output/docx/000/RHYAD-002.docx
output/pdf/000/RHYAD-002.pdf
output/docx/100/RHYAD-F01.docx
output/pdf/100/RHYAD-F01.pdf
```

## Prérequis

- Python 3.10 ou supérieur
- LibreOffice installé et disponible via `soffice` ou `libreoffice` dans le `PATH`

Installation :

```bash
python3 -m pip install -r requirements.txt
```

## Commandes

Générer le Programme Fonctionnel :

```bash
python3 scripts/main.py 002
```

Générer la fonction F01 :

```bash
python3 scripts/main.py F01
```

## Import de contenu validé

Un contenu validé peut être déposé au format Markdown dans `inbox/validated/`, puis importé en une seule commande.

Exemple :

```text
inbox/validated/002.md
```

Commande :

```bash
python3 scripts/import_validated.py 002
```

Le script :

- lit `inbox/validated/<CODE>.md` ;
- extrait `reference`, `title`, `subtitle`, `revision` et `status` lorsque ces métadonnées sont présentes ;
- convertit les titres Markdown en chapitres YAML ;
- convertit les listes Markdown en `bullets` YAML ;
- convertit les tableaux Markdown simples en `tables` YAML ;
- écrit `config/documents/<CODE>.yaml` ;
- exécute `python3 scripts/main.py <CODE>` ;
- exécute `python3 -m unittest discover` ;
- vérifie les fichiers DOCX/PDF produits ;
- exécute `git add .` puis `git commit -m "Integrate validated <CODE> content"`.

Le fichier Markdown reste dans `inbox/validated/` après import. Le Markdown validé est la source de vérité ; si une information obligatoire est absente, le script utilise le référentiel officiel lorsque c’est possible ou affiche une erreur explicite.

Lancer les tests :

```bash
python3 -m unittest discover
```

## Configuration

`config/project.yaml` contient les métadonnées projet, la révision, le statut, la confidentialité, les auteurs, les approbateurs, le logo CEVA et les chemins de sortie racine.

`config/rhyad_repository.yaml` contient la nomenclature officielle et permet au générateur de router les livrables dans la bonne famille.
