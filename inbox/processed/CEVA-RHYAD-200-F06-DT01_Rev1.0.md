# CEVA-RHYAD-200-F06-DT01

# Gestion des Flux --- Données Techniques d'Entrée

**Version :** Rev1.0\
**Statut :** Draft\
**Référence :** CEVA-RHYAD-200-F06-DT01

------------------------------------------------------------------------

# Objet

Le présent document a pour objet de définir l'ensemble des données
techniques nécessaires à la conception des flux internes du Campus CEVA.

Il couvre les flux de personnel, de matières, de produits, de déchets,
d'équipements et de maintenance afin de garantir la sécurité biologique,
la conformité GMP/BPF et l'efficacité opérationnelle.

------------------------------------------------------------------------

# Documents associés

## Programme Fonctionnel

-   CEVA-RHYAD-100-F06 --- Gestion des Flux

## Design Basis

-   CEVA-RHYAD-300-DB001 --- Process
-   CEVA-RHYAD-300-DB002 --- Architecture
-   CEVA-RHYAD-300-DB003 --- CVC / HVAC
-   CEVA-RHYAD-300-DB009 --- Logistique

# 1. Flux de personnel

  -------------------------------------------------------------------------------------
  Catégorie   Effectif   Fréquence   Point      Point de   Contraintes   Commentaires
                                     d'entrée   sortie     GMP           
  ----------- ---------- ----------- ---------- ---------- ------------- --------------

  -------------------------------------------------------------------------------------

# 2. Flux de matières premières

  ----------------------------------------------------------------------------
  Matière     Origine     Destination   Mode de     Fréquence   Commentaires
                                        transport               
  ----------- ----------- ------------- ----------- ----------- --------------

  ----------------------------------------------------------------------------

# 3. Flux des produits intermédiaires

  --------------------------------------------------------------------------
  Produit        Origine        Destination    Conditions de  Commentaires
                                               transport      
  -------------- -------------- -------------- -------------- --------------

  --------------------------------------------------------------------------

# 4. Flux des produits finis

  -----------------------------------------------------------------------------
  Produit     Origine     Destination   Conditions   Fréquence   Commentaires
  ----------- ----------- ------------- ------------ ----------- --------------

  -----------------------------------------------------------------------------

# 5. Flux des consommables

  Consommable   Origine   Destination   Stock tampon   Commentaires
  ------------- --------- ------------- -------------- --------------

# 6. Flux des déchets

  -------------------------------------------------------------------------------
  Déchet      Catégorie   Origine     Destination   Mode           Commentaires
                                                    d'évacuation   
  ----------- ----------- ----------- ------------- -------------- --------------

  -------------------------------------------------------------------------------

# 7. Flux des équipements

  Équipement   Origine   Destination   Nettoyage requis   Commentaires
  ------------ --------- ------------- ------------------ --------------

# 8. Flux de maintenance

  --------------------------------------------------------------------------
  Intervention   Local concerné Fréquence      Impact         Commentaires
                                               production     
  -------------- -------------- -------------- -------------- --------------

  --------------------------------------------------------------------------

# 9. Moyens de manutention

  Moyen                 Utilisation   Zone   Particularités   Commentaires
  --------------------- ------------- ------ ---------------- --------------
  Transpalette                                                
  Chariot                                                     
  AGV (si applicable)                                         
  Autre                                                       

# 10. Interfaces

  Fonction   Nature de l'interface   Commentaires
  ---------- ----------------------- --------------
  F01        Réception               
  F02        Stockage                
  F03        Préparation             
  F04        Production              
  F05        Conditionnement         
  F07        Lavage                  
  F08        Contrôle Qualité        
  F11        Déchets                 

# 11. Contraintes GMP/BPF

  Sujet                                    Exigence   Commentaires
  ---------------------------------------- ---------- --------------
  Séparation des flux                                 
  Flux propres / sales                                
  Flux personnel / matières                           
  Sas                                                 
  Circuits à sens unique                              
  Prévention des contaminations croisées              

# 12. Données de dimensionnement

  Élément   Valeur   Hypothèse   Validation
  --------- -------- ----------- ------------

# 13. Hypothèses de conception

  N°   Hypothèse   Impact   Référence CEVA-RHYAD-500-REG04
  ---- ----------- -------- --------------------------------

# 14. Décisions prises

  N°   Décision   Date   Référence CEVA-RHYAD-500-REG02
  ---- ---------- ------ --------------------------------

# 15. Actions

  ----------------------------------------------------------------------------------
  N°             Action         Responsable    Échéance       Référence
                                                              CEVA-RHYAD-500-REG01
  -------------- -------------- -------------- -------------- ----------------------

  ----------------------------------------------------------------------------------

------------------------------------------------------------------------

## Remarques RHYAD

-   Séparation stricte des flux propres, sales et biologiques.
-   Absence de croisements entre les flux de personnel, de matières, de
    produits et de déchets.
-   Interfaces avec les zones classées GMP.
-   Prise en compte de l'évolution de capacité de 100--300 L vers 1000
    L.
-   Intégration des contraintes logistiques propres au Royaume d'Arabie
    Saoudite.
-   Les schémas de circulation alimenteront les DB Process,
    Architecture, CVC/HVAC et Logistique ainsi que les études APS/APD.

------------------------------------------------------------------------

# Fin du document
