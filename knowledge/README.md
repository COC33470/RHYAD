# Knowledge Core RHYAD

Le dossier `knowledge/` constitue le futur référentiel unique de vérité du projet RHYAD.

Les documents YAML existants restent compatibles et continuent de fonctionner. Les contenus documentaires seront progressivement alimentés depuis ce Knowledge Core, afin de respecter le principe : une information = une seule source.

## Fichiers

- `project.yaml` : métadonnées projet issues de `config/project.yaml`, avec client, projet, localisation, révision courante, statut, langues, unités et paramètres globaux.
- `glossary.yaml` : base des acronymes et définitions destinée au futur document RHYAD-003.
- `decisions.yaml` : registre structuré des décisions validées, de leurs impacts et références.
- `risks.yaml` : registre structuré des risques, avec probabilité, impact, mitigation, responsable et statut.
- `assumptions.yaml` : hypothèses de conception, justification, source, impacts et statut.
- `requirements.yaml` : exigences projet, catégories, sources, références et statut.
- `interfaces.yaml` : interfaces entre fonctions, disciplines ou documents.
- `meetings.yaml` : base d'import futur des réunions, actions, décisions et risques associés.
- `traceability.yaml` : relations entre sources et destinations documentaires pour analyser les impacts.

Aucun contenu métier non validé ne doit être ajouté dans ces fichiers.
