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

Les documents générables sont déclarés dans `config/document_registry.yaml`, qui associe chaque code RHYAD à son code documentaire officiel, sa famille de sortie et son fichier source YAML.

Squelettes actuellement disponibles :

- `config/documents/000.yaml` — Modèle documentaire RHYAD-CEVA
- `config/documents/001.yaml` — Charte Projet
- `config/documents/001A.yaml` — ACAP – Analyse de Contexte et d’Adaptation du Projet
- `config/documents/002.yaml` — Programme Fonctionnel
- `config/documents/003.yaml` — Glossaire
- `config/documents/006.yaml` — Plan Directeur Documentaire
- `config/documents/functions/F01.yaml` — Réception et Expédition

Ces fichiers restent compatibles avec le moteur documentaire existant. Les contenus complets ne doivent être rédigés qu’après validation.

## Knowledge Core

Le dossier `knowledge/` constitue le futur référentiel documentaire unique de RHYAD. Il centralise progressivement les informations projet structurées afin que les documents YAML puissent les lire sans dupliquer les données.

Principe directeur :

```text
Une information = une seule source
```

Fichiers du Knowledge Core :

- `knowledge/project.yaml` : métadonnées projet issues de `config/project.yaml`.
- `knowledge/glossary.yaml` : acronymes et définitions.
- `knowledge/decisions.yaml` : décisions, impacts et références.
- `knowledge/risks.yaml` : risques, mitigations, responsables et statuts.
- `knowledge/assumptions.yaml` : hypothèses de conception et impacts.
- `knowledge/requirements.yaml` : exigences projet et références.
- `knowledge/interfaces.yaml` : interfaces entre origines, destinations et documents.
- `knowledge/meetings.yaml` : structure destinée aux comptes rendus.
- `knowledge/traceability.yaml` : relations entre sources et documents impactés.

À ce stade, le moteur charge le Knowledge Core sans modifier les documents existants. Les futures mises à jour pourront propager les données validées vers les documents concernés, tout en conservant une source documentaire unique.

## Sorties

Les sorties sont classées par famille officielle :

```text
output/docx/000 ... output/docx/600
output/pdf/000  ... output/pdf/600
output/xlsx/000 ... output/xlsx/600
```

Exemples :

```text
output/docx/000/CEVA-RHYAD-002-PF_Rev0.1.docx
output/pdf/000/CEVA-RHYAD-002-PF_Rev0.1.pdf
output/docx/100/CEVA-RHYAD-100-F01_Rev0.1.docx
output/pdf/100/CEVA-RHYAD-100-F01_Rev0.1.pdf
```

## Prérequis

- Python 3.10 ou supérieur
- LibreOffice installé et disponible via `soffice` ou `libreoffice` dans le `PATH`

Installation :

```bash
python3 -m pip install -r requirements.txt
```

## Commandes

La commande unifiée RHYAD est disponible via :

```bash
python3 scripts/rhyad.py help
```

Alias optionnel :

```bash
alias rhyad='python3 scripts/rhyad.py'
```

Commandes principales :

```bash
rhyad status
rhyad list
rhyad generate 002
rhyad import 003
rhyad validate
rhyad doctor
rhyad impact D-014
rhyad trace suggest
rhyad trace approve
rhyad dashboard
```

Sans alias, utiliser la forme compatible :

```bash
python3 scripts/rhyad.py status
python3 scripts/rhyad.py list
python3 scripts/rhyad.py generate 002
python3 scripts/rhyad.py import 003
python3 scripts/rhyad.py validate
python3 scripts/rhyad.py doctor
python3 scripts/rhyad.py impact D-014
python3 scripts/rhyad.py trace suggest
python3 scripts/rhyad.py trace approve
python3 scripts/rhyad.py dashboard
```

Les scripts historiques restent disponibles. Générer le Programme Fonctionnel :

```bash
python3 scripts/main.py 002
```

Générer la fonction F01 :

```bash
python3 scripts/main.py F01
```

## Production documentaire automatisée

La chaîne automatisée permet de produire un document validé à partir d'un unique fichier Markdown.

L'utilisateur dépose le contenu validé dans `inbox/validated/` :

```text
inbox/validated/002.md
inbox/validated/F01.md
inbox/validated/DB01.md
```

Puis lance une seule commande :

```bash
python3 scripts/rhyad.py import 002
```

Le script :

- lit `inbox/validated/<CODE>.md` ;
- identifie le code, la référence, le titre, la révision, le statut et la famille documentaire depuis le Markdown ou `config/document_registry.yaml` lorsque l'information y existe ;
- convertit les titres Markdown en chapitres YAML ;
- convertit les listes Markdown en `bullets` YAML ;
- convertit les tableaux Markdown simples en `tables` YAML ;
- écrit ou remplace le YAML source dans `config/documents/` ;
- exécute `python3 scripts/main.py <CODE>` ;
- exécute `python3 -m unittest discover` ;
- vérifie les fichiers DOCX/PDF produits ;
- déplace le Markdown traité dans `inbox/processed/` ;
- déplace le Markdown rejeté dans `inbox/rejected/` avec un fichier `.log` en cas d'erreur ;
- journalise l'import dans `logs/import.log` ;
- exécute `git add .` puis `git commit -m "Integrate validated <CODE>"`.

Exemples :

```bash
python3 scripts/rhyad.py import 003
python3 scripts/rhyad.py import F01
python3 scripts/rhyad.py import DB01
```

Le Markdown validé est la source d'entrée. Le script ne rédige pas de contenu : si une information obligatoire est absente, il utilise le référentiel officiel lorsque c'est possible ou affiche une erreur explicite.

Les commandes historiques restent disponibles :

```bash
python3 scripts/import_validated.py 002
python3 scripts/main.py 002
python3 -m unittest discover
```

## Analyse d'impacts documentaires

Le moteur d'analyse d'impacts lit exclusivement les relations déclarées dans `knowledge/traceability.yaml`. Aucune relation documentaire n'est codée en dur.

La commande :

```bash
python3 scripts/rhyad.py impact D-014
```

affiche :

- l'objet analysé ;
- les documents impactés ;
- le nombre d'impacts ;
- l'origine des relations.

Exemples :

```bash
python3 scripts/rhyad.py impact D-014
python3 scripts/rhyad.py impact CEVA-RHYAD-300-DB03
```

L'API interne `get_impacts()` est disponible dans `engine/core/impact_engine.py`. Elle prépare les futures commandes de propagation comme `rhyad meeting` et `rhyad update`, sans modifier les documents existants.

Le tableau de bord projet est disponible avec :

```bash
python3 scripts/rhyad.py dashboard
```

Il affiche le projet, le client, l'état Git, les documents générés ou en attente, les volumes du Knowledge Core, le résultat des tests et la dernière génération détectée dans `output/`.

## Suggestions de traçabilité

Les liens de traçabilité ne doivent pas être inventés. Aucune relation de traçabilité n’est inscrite dans `knowledge/traceability.yaml` sans preuve documentaire explicite et validation.

Le mode suggestion analyse uniquement les références documentaires explicites trouvées dans :

- les YAML existants de `config/documents/` ;
- les contenus Markdown présents dans `inbox/validated/` ;
- les codes déclarés dans `config/document_registry.yaml` ;
- le Knowledge Core déjà alimenté.

Créer les propositions :

```bash
python3 scripts/rhyad.py trace suggest
```

Le résultat est écrit dans :

```text
knowledge/traceability_suggestions.yaml
```

Chaque proposition contient une preuve : fichier source, emplacement, référence détectée et texte d'origine. Le fichier validé `knowledge/traceability.yaml` n'est jamais modifié par cette commande.

La commande de validation future est réservée :

```bash
python3 scripts/rhyad.py trace approve
```

À ce stade, elle n'approuve rien automatiquement et rappelle qu'une validation manuelle est requise.

Lancer les tests :

```bash
python3 -m unittest discover
```

## Configuration

`config/project.yaml` contient les métadonnées projet, la révision, le statut, la confidentialité, les auteurs, les approbateurs, le logo CEVA et les chemins de sortie racine.

`config/rhyad_repository.yaml` contient la nomenclature officielle et permet au générateur de router les livrables dans la bonne famille.

`config/document_registry.yaml` contient la codification officielle des documents générables, leur révision de sortie, leur famille et leur source YAML.

`knowledge/` contient le Knowledge Core RHYAD. Il deviendra progressivement la source unique de vérité pour les données projet validées.
