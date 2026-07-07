# RHYAD Document Engine

Générateur documentaire YAML pour le projet RHYAD.

Le dépôt produit des livrables DOCX/PDF avec la charte CEVA, le logo, le cartouche documentaire, la page de garde, le tableau `Document Control`, le pied de page et la table des matières Word.

## Séparation Documentaire

Les documents `CEVA-RHYAD-xxx` sont les documents projet destinés au client. Ils décrivent la méthode, la gouvernance et les livrables du projet sans exposer l'architecture interne du logiciel RHYAD ni ses outils de développement.

La documentation `RHYAD-SYS` est strictement interne à RHYAD. Elle est placée dans `docs/internal/` et couvre les sujets système, les conventions de développement et les automatisations du moteur documentaire.

Les deux référentiels sont indépendants : un document client `CEVA-RHYAD-xxx` ne référence pas la documentation interne `RHYAD-SYS`.

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
- CEVA-RHYAD-200-F01-DT01 à CEVA-RHYAD-200-F15-DT01

300 — Design Basis
- CEVA-RHYAD-300-DB001 Process
- CEVA-RHYAD-300-DB002 Architecture
- CEVA-RHYAD-300-DB003 CVC / HVAC
- CEVA-RHYAD-300-DB004 Utilités
- CEVA-RHYAD-300-DB005 Électricité
- CEVA-RHYAD-300-DB006 IT / OT
- CEVA-RHYAD-300-DB007 Maintenance
- CEVA-RHYAD-300-DB008 Sécurité / Sûreté
- CEVA-RHYAD-300-DB009 Logistique
- CEVA-RHYAD-300-DB010 Instrumentation & Automatisme

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
- LibreOffice installé via `soffice` ou `libreoffice` dans le `PATH`, ou via `/Applications/LibreOffice.app` sur macOS
- `ffmpeg` disponible dans le `PATH` pour le Meeting Manager audio, ou fallback `imageio-ffmpeg` installé via `requirements.txt`
- `ffprobe` disponible dans le `PATH` si possible, pour optimiser la détection de durée des réunions longues

Installation :

```bash
python3 -m pip install -r requirements.txt
```

Pour la transcription locale des réunions, installer ensuite un backend au choix :

```bash
python3 -m pip install faster-whisper
# ou
python3 -m pip install openai-whisper
```

Installation système `ffmpeg` / `ffprobe` recommandée :

```bash
# macOS avec Homebrew
brew install ffmpeg

# Debian / Ubuntu
sudo apt-get install ffmpeg

# Vérification
ffmpeg -version
ffprobe -version
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
rhyad paste 003
rhyad validate
rhyad doctor
rhyad impact D-014
rhyad figures list
rhyad figures check
rhyad meetings import chemin/reunion.zip
rhyad meetings transcribe chemin/reunion.m4a
rhyad ui
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
python3 scripts/rhyad.py paste 003
python3 scripts/rhyad.py validate
python3 scripts/rhyad.py doctor
python3 scripts/rhyad.py impact D-014
python3 scripts/rhyad.py figures list
python3 scripts/rhyad.py figures check
python3 scripts/rhyad.py meetings import chemin/reunion.zip
python3 scripts/rhyad.py meetings transcribe chemin/reunion.m4a
python3 scripts/rhyad.py ui
python3 scripts/rhyad.py trace suggest
python3 scripts/rhyad.py trace approve
python3 scripts/rhyad.py dashboard
```

## RHYAD Meeting Manager Alpha 0.1

Le module Meeting Manager importe un fichier audio local `.m4a`, `.mp3` ou `.wav`, le normalise avec `ffmpeg`, segmente les fichiers longs, puis lance une transcription française via le backend configuré.

Configuration :

```yaml
# config/meeting_manager.yaml
transcription:
  backend: faster-whisper
  model_name: tiny
  language: fr
  device: auto
  compute_type: int8
  segment_seconds: 900
```

Commande :

```bash
python3 scripts/rhyad.py meetings import /chemin/local/reunion.zip
python3 scripts/rhyad.py meetings transcribe /chemin/local/reunion.m4a
```

La commande `meetings import` accepte un audio direct ou un `.zip`. Si un zip est fourni, RHYAD le décompresse, détecte le premier fichier `.m4a`, `.mp3` ou `.wav`, puis le copie dans `data/meetings/audio/`.

Sorties locales :

```text
data/meetings/audio/
data/meetings/transcripts/<meeting_id>/transcript.txt
data/meetings/transcripts/<meeting_id>/transcript.json
data/meetings/outputs/<meeting_id>/meeting_summary_draft.md
data/meetings/outputs/meeting_manager.log
```

`meeting_summary_draft.md` prépare l’extraction IA des décisions, actions, échéances, risques et documents évoqués. Le backend `openai` est réservé dans la configuration pour une intégration API ultérieure.

Les scripts historiques restent disponibles. Générer le Programme Fonctionnel :

```bash
python3 scripts/main.py 002
```

Générer la fonction F01 :

```bash
python3 scripts/main.py F01
```

## Interface RHYAD

L'interface terminal RHYAD fournit une entrée métier unique pour piloter le projet sans manipuler directement les commandes techniques.

Lancer l'interface :

```bash
python3 scripts/rhyad.py ui
```

Menus disponibles :

- Tableau de bord
- Documents
- Réunions
- Décisions
- Actions
- Risques
- Design Basis
- Données Techniques
- Générer les livrables
- Synchroniser le projet
- Administration

Les opérations restent réalisées par les fonctions existantes de RHYAD, mais l'utilisateur les déclenche depuis des menus métier.

Dans le menu `Documents`, l'option `Nouveau document` affiche les documents connus mais non encore initialisés. Après sélection, RHYAD prépare le document, ouvre le workflow de collage du contenu validé, puis réutilise la chaîne automatisée pour produire les livrables, lancer les tests et gérer la validation Git.

L'option `Générer un document` n'affiche que les documents déjà initialisés.

## Production documentaire automatisée

La chaîne automatisée permet de produire un document validé à partir d'un unique fichier Markdown.

L'utilisateur dépose le contenu validé dans `inbox/validated/` :

```text
inbox/validated/002.md
inbox/validated/F01.md
inbox/validated/CEVA-RHYAD-300-DB001.md
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
python3 scripts/rhyad.py import CEVA-RHYAD-300-DB001
```

Le Markdown validé est la source d'entrée. Le script ne rédige pas de contenu : si une information obligatoire est absente, il utilise le référentiel officiel lorsque c'est possible ou affiche une erreur explicite.

### RHYAD Paste

La commande `paste` permet d'importer un contenu validé directement depuis le presse-papiers, sans créer manuellement le fichier Markdown.

Exemple :

```bash
python3 scripts/rhyad.py paste 003
```

La CLI affiche le document cible, puis attend le collage du contenu validé. Terminer la saisie avec `Ctrl+D` sur macOS/Linux, ou `Ctrl+Z` puis Entrée sur Windows.

La commande écrit automatiquement `inbox/validated/003.md`, puis réutilise le pipeline existant :

- conversion Markdown vers YAML RHYAD ;
- génération DOCX ;
- génération PDF ;
- exécution des tests ;
- commit Git ;
- archivage du Markdown traité.

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
python3 scripts/rhyad.py impact CEVA-RHYAD-300-DB003
```

L'API interne `get_impacts()` est disponible dans `engine/core/impact_engine.py`. Elle prépare les futures commandes de propagation comme `rhyad meeting` et `rhyad update`, sans modifier les documents existants.

Le tableau de bord projet est disponible avec :

```bash
python3 scripts/rhyad.py dashboard
```

Il affiche le projet, le client, l'état Git, les documents générés ou en attente, les volumes du Knowledge Core, le résultat des tests et la dernière génération détectée dans `output/`.

## Gestion des figures

Les figures, schémas et graphiques sont déclarés dans `config/figures_registry.yaml`. Le registre conserve l'identifiant, le titre, la famille documentaire, le fichier image, la légende, la source, le statut et les documents utilisateurs.

Les images sont stockées dans :

```text
assets/figures/000/
assets/figures/100/
assets/figures/200/
assets/figures/300/
assets/figures/400/
assets/figures/500/
assets/figures/600/
assets/figures/shared/
```

Formats image supportés pour insertion DOCX :

- PNG
- JPG
- JPEG

Les formats SVG, PDF, Mermaid et Draw.io sont réservés pour une extension future.

Exemple d'entrée de registre :

```yaml
figures:
  - id: FIG-000-001
    title: Exemple de figure
    family: "000"
    file: assets/figures/000/example.png
    caption: Exemple de légende
    source: RHYAD
    status: Draft
    used_in: []
```

Exemple d'utilisation dans un YAML documentaire :

```yaml
chapters:
  - title: "1. Schéma de principe"
    text: "Le schéma de principe est présenté ci-dessous."
    figures:
      - id: FIG-000-001
```

Lister les figures :

```bash
python3 scripts/rhyad.py figures list
```

Vérifier le registre :

```bash
python3 scripts/rhyad.py figures check
```

Si une image déclarée est absente, la génération du document continue et affiche un warning clair.

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
