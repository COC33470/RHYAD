# Architecture documentaire RHYAD

## Rôle

Ce fichier décrit la mémoire documentaire permanente du projet RHYAD. Il ne remplace pas les documents client validés et ne modifie pas la codification officielle.

## Architecture documentaire officielle

L'arborescence officielle est définie dans `config/rhyad_repository.yaml`. Les documents générables sont déclarés dans `config/document_registry.yaml`.

| Famille | Rôle |
|---|---|
| 000 | Documents de gouvernance projet : méthode, charte, ACAP, programme fonctionnel, glossaire, registres et Plan Directeur Documentaire. |
| 100 | Fonctions du Programme Fonctionnel F01 à F15. |
| 200 | Données Techniques nécessaires aux études et aux Design Basis. |
| 300 | Design Basis par discipline. |
| 400 | Réunions, ateliers et comptes rendus projet. |
| 500 | Registres dynamiques : actions, décisions, risques, hypothèses et interfaces. |
| 600 | Dossiers d'études : APS, APD, PRO, DCE, EXE, VISA, DOE. |

## Codification officielle

Les références officielles sont portées par `config/document_registry.yaml` pour les documents initialisés et par `config/rhyad_repository.yaml` pour l'arborescence de référence.

Exemples actuellement utilisés :

| Famille | Exemple |
|---|---|
| 000 | `CEVA-RHYAD-006-PDD` |
| 100 | `CEVA-RHYAD-100-F01` |
| 200 | `CEVA-RHYAD-200-F01-DT01` |
| 300 | `CEVA-RHYAD-300-DB001` à `CEVA-RHYAD-300-DB010` à harmoniser avec le référentiel `DB-001` à `DB-010`. |
| 500 | `CEVA-RHYAD-500-REG01` à `CEVA-RHYAD-500-REG05`. |

## Documents client et documentation interne

Les documents `CEVA-RHYAD-xxx` sont destinés au client et ne doivent pas exposer l'architecture interne du logiciel RHYAD.

La documentation interne RHYAD est séparée dans `docs/internal/`, notamment `docs/internal/RHYAD-SYS-001.md`. Elle peut décrire le moteur documentaire, les scripts, la CLI, Git, les conventions de développement et les automatisations.

## Sources et livrables

Les YAML du dépôt sont les sources documentaires officielles après intégration. Les Markdown d'entrée, DOCX et PDF sont des livrables ou artefacts de production et ne doivent pas être considérés comme la mémoire officielle après génération.
