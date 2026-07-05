# CEVA-RHYAD-200-F13-DT01

# Systèmes d'Information, Automatismes et Cybersécurité --- Données Techniques d'Entrée

**Version :** Rev1.0\
**Statut :** Draft\
**Référence :** CEVA-RHYAD-200-F13-DT01

------------------------------------------------------------------------

# Objet

Le présent document a pour objet de recenser l'ensemble des données
techniques nécessaires à la conception des systèmes d'information (IT),
des systèmes industriels (OT), des automatismes et des dispositifs de
cybersécurité du Campus CEVA.

Il couvre les infrastructures numériques, les systèmes de supervision,
les réseaux, les automatismes industriels et les mesures de protection
des données et des installations critiques.

# Documents associés

## Programme Fonctionnel

-   CEVA-RHYAD-100-F13

## Design Basis

-   CEVA-RHYAD-300-DB005 --- Électricité
-   CEVA-RHYAD-300-DB006 --- IT / OT
-   CEVA-RHYAD-300-DB008 --- Sécurité / Sûreté
-   CEVA-RHYAD-300-DB010 --- Instrumentation & Automatisme

# 1. Architecture générale des systèmes

  Domaine                        Exigence   Commentaires CEVA
  ------------------------------ ---------- -------------------
  Réseau IT                                 
  Réseau OT                                 
  Réseau invités                            
  Téléphonie                                
  Wi-Fi                                     
  Interconnexion des bâtiments              

# 2. Architecture IT / OT

  Élément           Description   Niveau de criticité   Commentaires
  ----------------- ------------- --------------------- --------------
  ERP                                                   
  MES                                                   
  LIMS                                                  
  SCADA                                                 
  Historian                                             
  PLC / Automates                                       
  BMS / GTB                                             
  GMAO                                                  

# 3. Réseaux

  Réseau             Disponibilité requise   Redondance   Commentaires
  ------------------ ----------------------- ------------ --------------
  Backbone                                                
  Fibre optique                                           
  Réseau OT                                               
  Réseau IT                                               
  Wi-Fi industriel                                        

# 4. Infrastructures critiques numériques

  -----------------------------------------------------------------------------
  Infrastructure   Niveau de       Redondance     Mode dégradé   Commentaires
                   disponibilité                                 
  ---------------- --------------- -------------- -------------- --------------
  Data Center                                                    

  Serveurs OT                                                    

  Serveurs IT                                                    

  Baies réseau                                                   

  Sauvegardes                                                    

  SCADA                                                          

  Historian                                                      
  -----------------------------------------------------------------------------

# 5. Cybersécurité

  Sujet                    Exigence   Référence   Commentaires
  ------------------------ ---------- ----------- --------------
  Segmentation IT / OT                            
  Pare-feu                                        
  Gestion des identités                           
  MFA                                             
  Gestion des privilèges                          
  Journalisation                                  
  Détection d'intrusion                           
  Antivirus / EDR                                 
  Chiffrement                                     

# 6. Protection des données

  Donnée                    Niveau de sensibilité   Protection requise   Commentaires
  ------------------------- ----------------------- -------------------- --------------
  Données de production                                                  
  Recettes de fabrication                                                
  Données QC                                                             
  Données vétérinaires                                                   
  Documentation GMP                                                      
  Plans et maquettes                                                     

# 7. Espionnage industriel et protection des actifs numériques

  Risque                                 Mesures de protection   Responsable   Commentaires
  -------------------------------------- ----------------------- ------------- --------------
  Vol de données                                                               
  Intrusion réseau                                                             
  Sabotage informatique                                                        
  Ransomware                                                                   
  Fuite d'informations confidentielles                                         

> Décision RHYAD validée : la protection contre l'espionnage industriel
> est une exigence de conception du Campus et devra être prise en compte
> dès les phases de programmation.

# 8. Continuité d'activité

  -----------------------------------------------------------------------
  Élément           Temps maximal     Solution prévue   Commentaires
                    d'interruption                      
  ----------------- ----------------- ----------------- -----------------
  ERP                                                   

  MES                                                   

  SCADA                                                 

  LIMS                                                  

  Réseau OT                                             

  Réseau IT                                             
  -----------------------------------------------------------------------

# 9. Interfaces

  Fonction   Nature de l'interface   Commentaires
  ---------- ----------------------- --------------
  F04        Production              
  F08        Contrôle Qualité        
  F09        Utilités                
  F10        Maintenance             
  F12        Sûreté                  
  F15        Gouvernance             

# 10. Conformité

  Référentiel             Applicable   Commentaires
  ----------------------- ------------ --------------
  Standards Groupe CEVA                
  IEC 62443                            
  GMP / BPF                            
  Exigences locales                    

# 11. Données de dimensionnement

  Élément   Valeur   Hypothèse   Validation
  --------- -------- ----------- ------------

# 12. Hypothèses de conception

  N°   Hypothèse   Impact   Référence CEVA-RHYAD-500-REG04
  ---- ----------- -------- --------------------------------

# 13. Décisions prises

  N°   Décision   Date   Référence CEVA-RHYAD-500-REG02
  ---- ---------- ------ --------------------------------

# 14. Actions

  ----------------------------------------------------------------------------------
  N°             Action         Responsable    Échéance       Référence
                                                              CEVA-RHYAD-500-REG01
  -------------- -------------- -------------- -------------- ----------------------

  ----------------------------------------------------------------------------------

------------------------------------------------------------------------

## Remarques RHYAD

Le projet RHYAD s'appuiera sur les standards IT/OT du Groupe CEVA, qui
constitueront la base de conception des systèmes numériques.

Ce projet étant le premier site CEVA en Arabie Saoudite, les solutions
retenues devront être examinées de manière critique afin de vérifier
leur adéquation avec :

-   les infrastructures télécom locales ;
-   les contraintes réglementaires saoudiennes ;
-   les délais d'approvisionnement ;
-   la disponibilité des compétences locales ;
-   les risques géopolitiques et logistiques identifiés dans l'ACAP.

Une réunion spécifique IT/OT sera organisée avec la Direction IT de CEVA
après la première réunion de programmation. Elle permettra de recueillir
les standards Groupe, d'identifier les adaptations nécessaires et
d'enregistrer les actions dans le registre projet.

## Recommandation RHYAD

Le DB-006 --- IT / OT devra comporter une architecture de référence
distinguant clairement :

-   le réseau IT d'entreprise ;
-   le réseau OT industriel ;
-   les zones démilitarisées (DMZ) ;
-   les systèmes critiques ;
-   les accès distants ;
-   les interfaces avec les équipements de production.

Cette architecture devra respecter les principes de segmentation et de
défense en profondeur, tout en restant compatible avec les standards
CEVA et les exigences de cybersécurité industrielle, notamment IEC
62443.

------------------------------------------------------------------------

# Fin du document
