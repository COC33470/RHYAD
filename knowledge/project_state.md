# État courant du projet RHYAD

## État documentaire

| Famille | État |
|---|---|
| 000 | Documents de gouvernance principaux initialisés. `MTH01`, `004`, `005`, `006` sont validés en Rev1.0. `001`, `001A`, `002` restent en Working Draft Rev0.1. |
| 100 | Fonctions F01 à F15 intégrées et validées en Rev1.0. |
| 200 | CEVA-RHYAD-200-F01-DT01 à CEVA-RHYAD-200-F15-DT01 intégrés en YAML Draft Rev1.0. |
| 300 | Design Basis non initialisés en YAML. Codification officielle validée : `CEVA-RHYAD-300-DB000`, puis `CEVA-RHYAD-300-DB001` à `CEVA-RHYAD-300-DB010`. |
| 400 | Réunions non initialisées en YAML. |
| 500 | Registres projet à compléter selon le registre documentaire. Les registres 004 et 005 existent en famille 000 comme documents de gouvernance validés. |
| 600 | Dossiers d'études non initialisés. |

## État technique

- Le dépôt Git constitue la source documentaire officielle du projet.
- Les YAML intégrés sont les sources de génération.
- Les DOCX/PDF sont des livrables générés.
- Le pipeline Markdown vers YAML/DOCX/PDF est opérationnel.
- Le support des tableaux Markdown alignés a été ajouté pour les DT.

## État des imports DT

Les fichiers source DT F02 à F15 ont été intégrés et déplacés vers `inbox/processed/`.

## Points à surveiller

- Ne pas modifier un document client validé sans demande explicite.
- Ne pas reconstruire un document validé depuis la mémoire conversationnelle.
- Maintenir la codification DT officielle `CEVA-RHYAD-200-Fxx-DT01`.
- Maintenir la codification DB officielle avant industrialisation des imports restants.
