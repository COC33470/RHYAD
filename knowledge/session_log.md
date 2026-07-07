# RHYAD — Journal des séances

## Objet

Ce fichier constitue le journal opérationnel des séances de travail RHYAD.

Il permet de conserver la trace synthétique :
- des décisions prises ;
- des documents créés ou modifiés ;
- des points ouverts ;
- des prochaines étapes.

Ce fichier complète la mémoire permanente du projet sans remplacer :
- le Registre des Décisions ;
- le Registre des Risques ;
- le Plan Directeur Documentaire ;
- les documents sources YAML.

---

## Session 2026-07-05

### Décisions validées

- Mise en place du dossier `knowledge/` comme mémoire permanente du projet.
- Validation de la séparation des rôles :
  - ChatGPT = Lead Engineer / AMO / Document Controller.
  - Codex = intégration dépôt, modifications, génération livrables, Git.
- Validation du principe : GitHub est la source unique de vérité.
- Validation du principe : Codex intervient en priorité en fin de séance pour limiter la consommation de quota.
- Validation du principe : aucun document validé ne doit être reconstruit depuis la mémoire conversationnelle.
- Validation de la codification officielle Design Basis : `CEVA-RHYAD-300-DB000` réservé aux Principes Généraux de Conception, puis `CEVA-RHYAD-300-DB001` à `CEVA-RHYAD-300-DB010`.

### Fichiers créés

- `knowledge/architecture.md`
- `knowledge/decisions.md`
- `knowledge/hypotheses.md`
- `knowledge/risks.md`
- `knowledge/interfaces.md`
- `knowledge/project_state.md`
- `knowledge/design_drivers.md`
- `knowledge/open_points.md`
- `knowledge/chatgpt_context.md`

### Points ouverts

- Harmonisation des références DT vers `CEVA-RHYAD-200-Fxx-DT01` réalisée pour F01 à F15.
- Harmonisation des références Design Basis vers `CEVA-RHYAD-300-DB001` à `CEVA-RHYAD-300-DB010` réalisée.
- Contrôler les livrables DT générés.
- Initialiser `CEVA-RHYAD-200-DT000`.
- Initialiser les familles 300, 400 et 500.

### Prochaine séance recommandée

- Revue documentaire des DT.
- Stabilisation des références documentaires.
- Démarrage du chapitre 300 — Design Basis.

---
