# Compte rendu CEVA-RHYAD prérempli - transcript_cleaned

## Statut de génération

- Préremplissage automatique Meeting Manager Alpha 0.4.
- Méthode : raisonnement métier AMO / ingénierie à partir de la transcription nettoyée et du résumé disponible.
- Les formulations sont reformulées pour usage projet ; les données faibles sont marquées pour validation chef de projet.

## 1. Informations réunion

| Champ CEVA-RHYAD | Valeur préremplie | Confiance |
| --- | --- | --- |
| Projet | CEVA Riyadh Campus Project | medium |
| Date réunion | À confirmer | medium |
| Objet | Réunion de cadrage terrain, programme, modules et appel d'offres | medium |
| Participants identifiés | Thomas, Bertrand, Jean, Vincent, Tiffany, Christophe | medium |

## 2. Synthèse exécutive

Projet exploitable pour préremplissage RHYAD, avec arbitrages critiques à sécuriser sur terrain, continuité électrique, froid critique, modules/flux et réglementation.

## 3. Sujets traités

| ID | Sujet | Contexte | Problématique | Confiance | Validation |
| --- | --- | --- | --- | --- | --- |
| programme_fonctionnel | Structuration du programme fonctionnel RHYAD | La réunion confirme que le programme fonctionnel doit organiser les besoins par fonctions métier, puis alimenter les contraintes de conception et les DT. | Le référentiel doit éviter les informations dispersées entre fonctions, DT et documents de réunion. | high |  |
| site_ksa | Contraintes du site en Arabie Saoudite | La réunion aborde l'adaptation du projet au contexte local saoudien, incluant climat, réseau électrique, terrain et construction locale. | Les contraintes site ne sont pas entièrement stabilisées et conditionnent architecture, bâtiment, utilités et planning. | high |  |
| electricite_ups | Continuité électrique et protection UPS | La réunion évoque la stabilité du réseau électrique, les microcoupures et la protection des équipements critiques. | La stratégie de continuité électrique doit être clarifiée pour éviter un impact sur contrôle, froid et process. | high |  |
| froid_souches | Conservation des souches et master seeds | La réunion aborde les souches, les master seeds et les besoins de conservation sous froid. | La conservation des souches doit être sécurisée avant de dimensionner stockage, froid et continuité électrique. | high |  |
| modules_flux_bsl2 | Architecture modulaire, sas et flux BSL2 | La réunion traite l'intégration des modules, des sas, des couloirs et des flux matières, déchets et personnel. | L'organisation modulaire doit démontrer la séparation des flux et la maîtrise des interfaces process, architecture et biosécurité. | high |  |
| terrain_planning_tender | Terrain, planning et appel d'offres | La réunion indique que le terrain et le calendrier conditionnent la préparation de l'appel d'offres. | Le terrain n'est pas totalement sécurisé, ce qui peut retarder le dossier technique et l'appel d'offres constructeur. | high |  |
| reglementation_urs | Réglementation, autorités et URS | La réunion fait apparaître un besoin de clarification réglementaire et de cohérence avec l'URS. | Les exigences réglementaires applicables aux autovaccins doivent être clarifiées avant la consolidation des livrables techniques. | high |  |

## 4. Décisions

| ID | Décision | Contexte | Valideur | Date | Impact documentaire | Confiance | Validation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D-001 | Le programme fonctionnel doit rester la structure de référence pour organiser les besoins métier F01 à F15. | Structuration du programme fonctionnel RHYAD | À confirmer | À confirmer | CEVA-RHYAD-002-PF, CEVA-RHYAD-100-F01..F15, CEVA-RHYAD-200-F01..F15-DT01 | high |  |
| D-002 | Les contraintes de site en Arabie Saoudite doivent être consolidées avant le gel des choix d'implantation. | Contraintes du site en Arabie Saoudite | À confirmer | À confirmer | CEVA-RHYAD-002-PF, DB002 Architecture, DB003 Bâtiment | high |  |
| D-003 | La stratégie UPS et continuité électrique doit être arbitrée avant le gel des DT utilités et des principes de sûreté de fonctionnement. | Continuité électrique et protection UPS | À confirmer | À confirmer | CEVA-RHYAD-200-F09-DT01, DB004 Utilités, DB010 Sécurité, CEVA-RHYAD-400-R05 | high |  |
| D-004 | Le choix des master seeds devra être validé avant le lancement des études détaillées. | Conservation des souches et master seeds | À confirmer | À confirmer | CEVA-RHYAD-100-F02, CEVA-RHYAD-200-F02-DT01, DB006 Production, DB007 Qualité | high |  |
| D-005 | L'organisation des sas, couloirs et flux doit être validée comme donnée d'entrée du programme et des Design Basis. | Architecture modulaire, sas et flux BSL2 | À confirmer | À confirmer | CEVA-RHYAD-002-PF, CEVA-RHYAD-100-F06, CEVA-RHYAD-100-F11, DB001 Process, DB002 Architecture, DB008 Biosécurité | high |  |
| D-006 | Le choix du terrain doit être stabilisé avant de figer les données techniques transmises pour l'appel d'offres constructeur. | Terrain, planning et appel d'offres | À confirmer | À confirmer | CEVA-RHYAD-400-R05, CEVA-RHYAD-004-REGISTRE_DES_RISQUES, DB003 Bâtiment | high |  |
| D-007 | La position réglementaire et les exigences URS doivent être confirmées avant d'engager les choix détaillés qualité et biosécurité. | Réglementation, autorités et URS | À confirmer | À confirmer | CEVA-RHYAD-002-PF, DB007 Qualité, DB008 Biosécurité, CEVA-RHYAD-004-REGISTRE_DES_RISQUES | high |  |

## 5. Actions

| ID | Action | Responsable | Échéance | Priorité | Statut | Sujet source | Confiance | Validation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-001 | Consolider le programme fonctionnel par fonctions F01 à F15 afin de relier chaque besoin aux DT correspondantes. | À confirmer | À confirmer | Moyenne | À qualifier | Structuration du programme fonctionnel RHYAD | high |  |
| A-002 | Identifier les informations manquantes par fonction avant de les transmettre aux bureaux d'études. | À confirmer | À confirmer | Moyenne | À qualifier | Structuration du programme fonctionnel RHYAD | high |  |
| A-003 | Consolider l'analyse de contexte Arabie Saoudite afin d'identifier les contraintes climatiques, réglementaires et d'accès au site. | À confirmer | À confirmer | Haute | À qualifier | Contraintes du site en Arabie Saoudite | high |  |
| A-004 | Vérifier les contraintes locales de raccordement, d'autorisation et de construction avant l'appel d'offres constructeur. | À confirmer | À confirmer | Haute | À qualifier | Contraintes du site en Arabie Saoudite | high |  |
| A-005 | Identifier le fournisseur d'électricité local afin de confirmer les contraintes d'alimentation électrique du site. | À confirmer | À confirmer | Haute | À qualifier | Continuité électrique et protection UPS | high |  |
| A-006 | Qualifier le besoin UPS pour les fonctions critiques, notamment contrôle, congélateurs, automatisme et équipements process. | À confirmer | À confirmer | Haute | À qualifier | Continuité électrique et protection UPS | high |  |
| A-007 | Définir les scénarios de microcoupures et les durées admissibles par famille d'équipements. | À confirmer | À confirmer | Haute | À qualifier | Continuité électrique et protection UPS | high |  |
| A-008 | Définir la stratégie de conservation des souches et master seeds, incluant température, redondance et surveillance. | À confirmer | À confirmer | Haute | À qualifier | Conservation des souches et master seeds | high |  |
| A-009 | Identifier les volumes et familles de souches à stocker afin de dimensionner congélateurs et stockage froid. | À confirmer | À confirmer | Haute | À qualifier | Conservation des souches et master seeds | high |  |
| A-010 | Cartographier les flux matières, personnel, déchets et équipements pour vérifier les croisements et interfaces entre modules. | À confirmer | À confirmer | Haute | À qualifier | Architecture modulaire, sas et flux BSL2 | high |  |
| A-011 | Clarifier si les sas et couloirs critiques sont intégrés dans les modules ou traités comme ouvrages séparés. | À confirmer | À confirmer | Haute | À qualifier | Architecture modulaire, sas et flux BSL2 | high |  |
| A-012 | Obtenir la confirmation du terrain cible afin de sécuriser les hypothèses de surface, accès, raccordements et permis. | À confirmer | À confirmer | Haute | À qualifier | Terrain, planning et appel d'offres | high |  |
| A-013 | Préparer le dossier technique d'appel d'offres en distinguant les données confirmées et les hypothèses dépendantes du terrain. | À confirmer | À confirmer | Haute | À qualifier | Terrain, planning et appel d'offres | high |  |
| A-014 | Organiser une clarification réglementaire avec les autorités ou référents CEVA afin de confirmer les exigences applicables aux autovaccins. | À confirmer | À confirmer | Haute | À qualifier | Réglementation, autorités et URS | high |  |
| A-015 | Aligner l'URS, le programme fonctionnel et les DT sur le niveau GMP réellement applicable. | À confirmer | À confirmer | Haute | À qualifier | Réglementation, autorités et URS | high |  |

## 6. Risques

| ID | Risque | Cause | Impact | Probabilité | Gravité | Criticité | Responsable | Plan d'action | Confiance | Statut |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | Les besoins fonctionnels peuvent rester incomplets ou dispersés entre plusieurs documents. | Les fonctions métier et les DT ne sont pas encore totalement alimentées par des données confirmées. | Risque d'incohérence de programmation et de reprise documentaire en phase études. | Moyenne | Moyenne | Modérée | AMO RHYAD | Mettre à jour les fonctions et DT uniquement avec les informations source validées. | high | À qualifier |
| R-002 | Les contraintes locales du site peuvent remettre en cause les hypothèses de conception. | Terrain et conditions locales encore à confirmer. | Risque de reprise des choix bâtiment, architecture et utilités. | Moyenne | Élevée | Élevée | AMO RHYAD / CEVA | Formaliser les contraintes site dans le programme et les futures Design Basis. | high | À qualifier |
| R-003 | Les microcoupures peuvent perturber les équipements critiques et les systèmes de contrôle. | Qualité d'alimentation électrique locale à confirmer. | Risque de perte de continuité process, défaut qualité ou arrêt d'équipements critiques. | Moyenne | Élevée | Élevée | Électricité / Utilités | Réaliser une analyse de continuité électrique et dimensionner les protections UPS nécessaires. | high | À qualifier |
| R-004 | Une perte de froid peut compromettre la conservation des souches et master seeds. | Besoins de conservation et autonomie froid encore à confirmer. | Risque qualité majeur et risque de perte de matière biologique critique. | Moyenne | Élevée | Élevée | Qualité / Production | Définir les exigences froid, alarme, redondance et secours électrique pour les stockages critiques. | high | À qualifier |
| R-005 | Une mauvaise organisation des flux peut créer des croisements incompatibles avec les exigences biosécurité et GMP. | Interfaces modules, sas et couloirs encore à clarifier. | Risque de reprise layout, surface et principes de confinement. | Moyenne | Élevée | Élevée | Process / Architecture / Biosécurité | Produire une cartographie des flux et une matrice d'interfaces module par module. | high | À qualifier |
| R-006 | L'absence de terrain confirmé peut bloquer le planning et retarder l'appel d'offres. | Choix du terrain et données locales encore à confirmer. | Risque de décalage du calendrier études, consultation et construction. | Élevée | Élevée | Critique | CEVA / AMO RHYAD | Mettre le terrain en point bloquant du dashboard et suivre une échéance de confirmation. | high | À qualifier |
| R-007 | Une interprétation réglementaire incomplète peut imposer une reprise du programme ou du layout. | Niveau GMP et attentes autorités encore à confirmer. | Risque de non-conformité, reprise URS et décalage planning. | Moyenne | Élevée | Élevée | Qualité / Réglementaire | Tracer les points réglementaires ouverts et obtenir validation CEVA avant gel documentaire. | high | À qualifier |

## 7. Points ouverts

| ID | Point ouvert | Arbitrage attendu | Responsable | Échéance cible | Confiance | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| OP-001 | Confirmer les données manquantes par fonction avant intégration définitive dans les DT. | Arbitrage ou confirmation CEVA requis. | À confirmer | À confirmer | high |  |
| OP-002 | Confirmer les contraintes définitives du terrain et du contexte local. | Arbitrage ou confirmation CEVA requis. | À confirmer | À confirmer | high |  |
| OP-003 | Confirmer la qualité du réseau et les exigences UPS par équipement critique. | Arbitrage ou confirmation CEVA requis. | À confirmer | À confirmer | high |  |
| OP-004 | Confirmer température, volumes, redondance et règles qualité applicables aux souches. | Arbitrage ou confirmation CEVA requis. | À confirmer | À confirmer | high |  |
| OP-005 | Arbitrer l'intégration des sas et couloirs dans les modules ou dans la construction locale. | Arbitrage ou confirmation CEVA requis. | À confirmer | À confirmer | high |  |
| OP-006 | Confirmer le terrain, son calendrier de disponibilité et les impacts permis. | Arbitrage ou confirmation CEVA requis. | À confirmer | À confirmer | high |  |
| OP-007 | Confirmer les exigences autorités, SFDA le cas échéant, et le niveau GMP applicable. | Arbitrage ou confirmation CEVA requis. | À confirmer | À confirmer | high |  |

## 8. Impacts documentaires

| ID | Document concerné | Modification à faire | Source métier | Priorité | Confiance | Statut |
| --- | --- | --- | --- | --- | --- | --- |
| I-001 | CEVA-RHYAD-002-PF | Compléter les rubriques fonctionnelles avec les besoins confirmés. | Structuration du programme fonctionnel RHYAD | Haute | high | À qualifier |
| I-002 | CEVA-RHYAD-100-F01..F15 | Compléter les fonctions impactées sans dupliquer les DT. | Structuration du programme fonctionnel RHYAD | Haute | high | À qualifier |
| I-003 | CEVA-RHYAD-200-F01..F15-DT01 | Préremplir les données techniques disponibles et marquer le reste À confirmer. | Structuration du programme fonctionnel RHYAD | Haute | high | À qualifier |
| I-004 | CEVA-RHYAD-002-PF | Ajouter les contraintes de site confirmées. | Contraintes du site en Arabie Saoudite | Haute | high | À qualifier |
| I-005 | DB002 Architecture | Tracer les impacts architecture. | Contraintes du site en Arabie Saoudite | Moyenne | high | À qualifier |
| I-006 | DB003 Bâtiment | Tracer les impacts bâtiment et site. | Contraintes du site en Arabie Saoudite | Haute | high | À qualifier |
| I-007 | CEVA-RHYAD-200-F09-DT01 | Compléter les exigences d'alimentation électrique et UPS. | Continuité électrique et protection UPS | Haute | high | À qualifier |
| I-008 | DB004 Utilités | Tracer l'impact utilités. | Continuité électrique et protection UPS | Haute | high | À qualifier |
| I-009 | DB010 Sécurité | Tracer l'impact continuité / sûreté de fonctionnement. | Continuité électrique et protection UPS | Haute | high | À qualifier |
| I-010 | CEVA-RHYAD-400-R05 | Suivre l'arbitrage UPS dans le dashboard. | Continuité électrique et protection UPS | Haute | high | À qualifier |
| I-011 | CEVA-RHYAD-100-F02 | Compléter les besoins de stockage froid. | Conservation des souches et master seeds | Haute | high | À qualifier |
| I-012 | CEVA-RHYAD-200-F02-DT01 | Préremplir les données techniques de stockage froid. | Conservation des souches et master seeds | Haute | high | À qualifier |
| I-013 | DB006 Production | Tracer l'impact production. | Conservation des souches et master seeds | Moyenne | high | À qualifier |
| I-014 | DB007 Qualité | Tracer l'impact qualité / conservation des souches. | Conservation des souches et master seeds | Haute | high | À qualifier |
| I-015 | CEVA-RHYAD-002-PF | Intégrer les contraintes modules, couloirs et sas. | Architecture modulaire, sas et flux BSL2 | Haute | high | À qualifier |
| I-016 | CEVA-RHYAD-100-F06 | Compléter la fonction gestion des flux. | Architecture modulaire, sas et flux BSL2 | Haute | high | À qualifier |
| I-017 | CEVA-RHYAD-100-F11 | Compléter la fonction déchets / effluents. | Architecture modulaire, sas et flux BSL2 | Moyenne | high | À qualifier |
| I-018 | DB001 Process | Tracer l'impact process. | Architecture modulaire, sas et flux BSL2 | Haute | high | À qualifier |
| I-019 | DB002 Architecture | Tracer l'impact architecture. | Architecture modulaire, sas et flux BSL2 | Haute | high | À qualifier |
| I-020 | DB008 Biosécurité | Tracer l'impact biosécurité. | Architecture modulaire, sas et flux BSL2 | Haute | high | À qualifier |
| I-021 | CEVA-RHYAD-400-R05 | Mettre à jour les jalons terrain et appel d'offres. | Terrain, planning et appel d'offres | Haute | high | À qualifier |
| I-022 | CEVA-RHYAD-004-REGISTRE_DES_RISQUES | Mettre à jour les risques planning / terrain. | Terrain, planning et appel d'offres | Haute | high | À qualifier |
| I-023 | DB003 Bâtiment | Tracer les hypothèses dépendantes du terrain. | Terrain, planning et appel d'offres | Haute | high | À qualifier |
| I-024 | CEVA-RHYAD-002-PF | Compléter les contraintes réglementaires et URS confirmées. | Réglementation, autorités et URS | Haute | high | À qualifier |
| I-025 | DB007 Qualité | Tracer l'impact qualité. | Réglementation, autorités et URS | Haute | high | À qualifier |
| I-026 | DB008 Biosécurité | Tracer l'impact biosécurité. | Réglementation, autorités et URS | Haute | high | À qualifier |
| I-027 | CEVA-RHYAD-004-REGISTRE_DES_RISQUES | Suivre le risque de clarification réglementaire. | Réglementation, autorités et URS | Haute | high | À qualifier |

## 9. Exigences techniques

| ID | Exigence | Discipline concernée | Contrainte associée | Impact projet | Confiance | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | Chaque fonction du programme doit disposer de ses contraintes, interfaces et données d'entrée traçables. | Programmation fonctionnelle | Une information = une seule source. | Base de préparation des DT et des Design Basis. | high |  |
| REQ-002 | La conception doit intégrer les contraintes climatiques et réglementaires de l'Arabie Saoudite. | Site / Bâtiment | Contexte local non entièrement confirmé. | Conditionne implantation, enveloppe bâtiment, utilités et planning. | high |  |
| REQ-003 | Les équipements critiques doivent être protégés contre les microcoupures selon leur criticité process et qualité. | Électricité / Utilités | Qualité d'alimentation locale à confirmer. | Alimente les DT F09, DB004 Utilités et DB010 Sécurité. | high |  |
| REQ-004 | Les souches et master seeds doivent disposer d'une conservation maîtrisée, surveillée et secourue. | Froid / Qualité / Production | Paramètres de stockage et volumes à confirmer. | Dimensionnement stockage froid, utilités, qualité et continuité électrique. | high |  |
| REQ-005 | Les flux matières, personnel et déchets doivent être séparés et compatibles avec les exigences BSL2/GMP. | Process / Architecture / Biosécurité | Interfaces modules et sas à confirmer. | Conditionne layout, surfaces, portes, sas et circulations. | high |  |
| REQ-006 | Les données terrain doivent être confirmées avant le gel des hypothèses de conception locale. | Planning / Bâtiment | Terrain et permis à confirmer. | Conditionne appel d'offres, surfaces, raccordements et planning. | high |  |
| REQ-007 | Le programme et les DT doivent intégrer uniquement des exigences réglementaires confirmées. | Qualité / Réglementaire | Validation autorités / CEVA à obtenir. | Conditionne qualité, biosécurité, process et documents d'appel d'offres. | high |  |

## 10. Prochaines étapes

- Consolider l'analyse de contexte Arabie Saoudite afin d'identifier les contraintes climatiques, réglementaires et d'accès au site.
- Vérifier les contraintes locales de raccordement, d'autorisation et de construction avant l'appel d'offres constructeur.
- Identifier le fournisseur d'électricité local afin de confirmer les contraintes d'alimentation électrique du site.
- Qualifier le besoin UPS pour les fonctions critiques, notamment contrôle, congélateurs, automatisme et équipements process.
- Définir les scénarios de microcoupures et les durées admissibles par famille d'équipements.
- Définir la stratégie de conservation des souches et master seeds, incluant température, redondance et surveillance.
- Identifier les volumes et familles de souches à stocker afin de dimensionner congélateurs et stockage froid.
- Cartographier les flux matières, personnel, déchets et équipements pour vérifier les croisements et interfaces entre modules.
