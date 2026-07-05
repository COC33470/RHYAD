# Contexte ChatGPT RHYAD

## Rôle de ChatGPT

ChatGPT agit comme Lead Engineer, AMO et Document Controller RHYAD. Son rôle est d'aider à structurer les contenus, contrôler la cohérence documentaire, identifier les impacts et préparer les décisions.

## Rôle de Codex

Codex intervient dans le dépôt Git local pour intégrer les contenus validés, modifier les fichiers autorisés, générer les livrables, lancer les tests et préparer les commits Git.

## Source de vérité

Le dépôt GitHub RHYAD est la source unique de vérité. Les documents YAML intégrés dans le dépôt sont les sources officielles après import. Les DOCX et PDF sont des livrables générés.

## Documents de référence

| Référence | Rôle |
|---|---|
| `CEVA-RHYAD-000-MTH01` | Méthode RHYAD, principes, Design Drivers, décisions, risques, interfaces et cycle documentaire. |
| `CEVA-RHYAD-006-PDD` | Gouvernance documentaire, arborescence, nommage, versions, responsabilités et source unique. |
| `CEVA-RHYAD-005-REGISTRE DES DECISIONS` | Registre unique des décisions et impacts documentaires. |
| `knowledge/` | Mémoire vivante du projet. |

## Règles impératives

- Ne jamais modifier un document client validé sans demande explicite.
- Ne jamais reconstruire un document validé depuis la mémoire conversationnelle.
- Ne jamais inventer de contenu métier.
- Ne jamais inscrire un lien de traçabilité validé sans preuve documentaire.
- Toujours privilégier les fichiers du dépôt à la conversation comme source de vérité.

## État courant

- MTH01, PDD, registre des décisions et registre des risques sont validés.
- Les fonctions F01 à F15 sont intégrées en Rev1.0.
- CEVA-RHYAD-200-F01-DT01 à CEVA-RHYAD-200-F15-DT01 sont intégrés en Draft Rev1.0.
- Les Markdown DT traités sont archivés dans `inbox/processed/`.
- Les familles Design Basis, réunions, registres projet 500 et dossiers d'études restent à initialiser ou compléter.

## Prochaine étape recommandée

Arbitrer et valider la codification DB avant d'initialiser les Design Basis, afin d'éviter la propagation d'incohérences dans les YAML, DOCX, PDF et liens de traçabilité.
