# Mémoire des interfaces RHYAD

## Références

- Méthode : `CEVA-RHYAD-000-MTH01`.
- Plan documentaire : `CEVA-RHYAD-006-PDD`.
- Source structurée future : `knowledge/interfaces.yaml`.

## Interfaces entre fonctions F01 à F15

Les fonctions F01 à F15 constituent les chapitres indépendants du Programme Fonctionnel. Les interfaces principales doivent être identifiées par documents liés, données d'entrée, données de sortie, disciplines concernées et impacts documentaires.

Interfaces fonctionnelles typiques déjà visibles dans les documents :

- F01 avec F02, F04, F09, F11 pour les flux de réception et expédition ;
- F06 avec les fonctions de production, logistique et architecture pour la gestion des flux ;
- F09 avec les fonctions consommatrices d'utilités ;
- F10 avec les fonctions nécessitant maintenance et exploitation technique ;
- F12 et F13 pour les interactions sûreté, accès, IT / OT et cybersécurité ;
- F15 avec les fonctions concernées par l'évolutivité et les réserves.

## Interfaces entre DT et DB

Les DT collectent les données nécessaires aux études. Les Design Basis traduisent les principes de conception par discipline.

| Source | Destination |
|---|---|
| CEVA-RHYAD-200-Fxx-DT01 | DB Process |
| CEVA-RHYAD-200-Fxx-DT01 | DB Architecture |
| CEVA-RHYAD-200-Fxx-DT01 | DB CVC / HVAC |
| CEVA-RHYAD-200-Fxx-DT01 | DB Utilités |
| CEVA-RHYAD-200-Fxx-DT01 | DB Électricité |
| CEVA-RHYAD-200-Fxx-DT01 | DB IT / OT |
| CEVA-RHYAD-200-Fxx-DT01 | DB Logistique |

## Interfaces critiques par discipline

- Process / Architecture.
- Process / CVC.
- CVC / Utilités.
- Utilités / Électricité.
- Électricité / IT-OT.
- Sécurité-Sûreté / IT-OT.
- Maintenance / Architecture.
- Architecture / Logistique.

## Règle de mémoire

Une interface doit rester traçable jusqu'aux documents concernés, aux décisions associées et, si nécessaire, aux risques et actions.
