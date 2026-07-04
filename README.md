# RHYAD Document Engine

Générateur documentaire YAML pour le projet RHYAD. Le flux actuel reste volontairement simple :

```text
config/documents/<CODE>.yaml -> DOCX -> PDF
```

Le moteur générique lit un fichier document YAML, applique le style CEVA, ajoute les métadonnées projet issues de `config/project.yaml`, puis exporte le DOCX en PDF avec LibreOffice.

## Prérequis

- Python 3.10 ou supérieur
- LibreOffice installé et disponible via `soffice` ou `libreoffice` dans le `PATH`

Installation des dépendances Python :

```bash
python3 -m pip install -r requirements.txt
```

## Configuration

La configuration projet est centralisée dans `config/project.yaml` :

- `project.code` sert au préfixe des fichiers générés, par exemple `RHYAD-F01.docx`.
- `document.revision`, `document.status` et `document.confidentiality` sont ajoutés aux métadonnées du document.
- `branding.logo_ceva` est optionnel. Si le fichier existe, il est inséré dans la page de titre ; sinon la génération continue.
- `output.docx` et `output.pdf` définissent les dossiers de sortie.

Chaque document est défini dans `config/documents/<CODE>.yaml` avec :

- `reference`
- `title`
- `subtitle` optionnel
- `chapters`, liste non vide de chapitres avec `title`, puis `text` et/ou `bullets`

## Génération

Pour générer la procédure F01 :

```bash
python3 scripts/main.py F01
```

Sorties attendues :

```text
output/docx/RHYAD-F01.docx
output/pdf/RHYAD-F01.pdf
```

Si LibreOffice est absent ou échoue, le script affiche une erreur explicite et retourne un code d'échec.

## Tests

Les tests minimaux utilisent `unittest`, sans framework supplémentaire :

```bash
python3 -m unittest discover
```

Ils vérifient la validation YAML, la génération DOCX, l'utilisation de `project.yaml` et la robustesse du wrapper PDF sans lancer LibreOffice.

## Dépendances

- `python-docx` : génération DOCX
- `pyyaml` : lecture des configurations YAML
- `reportlab`, `openpyxl`, `pillow` : réservées aux futurs exports ou enrichissements documentaires ; elles ne sont pas nécessaires au flux F01 actuel
