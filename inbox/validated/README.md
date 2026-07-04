# Import de contenu validé

Déposer ici les contenus validés au format Markdown avant import.

Exemple :

```text
inbox/validated/002.md
```

Commande :

```bash
python3 scripts/import_validated.py 002
```

Format recommandé :

```markdown
reference: "002"
title: "Programme Fonctionnel"
subtitle: "Sous-titre validé"
revision: "Rev.0.1"
status: "Working Draft"

# 1. Objet

Texte validé.

# 2. Liste

- Élément validé
- Autre élément validé

# 3. Tableau

| Référence | Document |
|---|---|
| RHYAD-001 | Charte Projet |
```

Règles :

- Le Markdown déposé est la source de vérité.
- Les titres Markdown deviennent des chapitres YAML.
- Les listes Markdown deviennent des `bullets`.
- Les tableaux Markdown simples deviennent des `tables`.
- Le script ne supprime jamais les fichiers de ce dossier.
- Si une métadonnée n’est pas présente, le script utilise le code demandé ou le titre du référentiel officiel lorsque c’est possible.
