# Templates Excel - Donnees Techniques

Ce dossier contient les supports Excel de collecte CEVA pour les Donnees Techniques du projet CEVA RHYAD.

## DT-Master

Le fichier `CEVA-RHYAD-200-DT-Master.xlsx` est le classeur maitre de collecte.

Il centralise les donnees techniques des fonctions F01 a F15 dans un support unique :

- `00_Index` : suivi des fonctions, references DT, responsables, statuts et dates de mise a jour.
- `00_General` : informations generales du classeur et circuit de redaction, verification et approbation.
- `F01` a `F15` : onglets de collecte par fonction projet.

Chaque onglet fonction reprend la structure standard :

- donnees generales ;
- donnees techniques ;
- capacites ;
- interfaces ;
- utilites ;
- GMP / QHSE ;
- equipements ;
- hypotheses ;
- documents associes ;
- commentaires libres.

Les cellules jaunes sont destinees a la saisie CEVA. Les cellules de structure sont protegees pour limiter les modifications accidentelles du modele.

## Fichiers DT individuels

Les fichiers DT individuels restent les documents de reference par fonction ou par lot de donnees techniques.

Leur usage recommande est le suivant :

- utiliser le DT-Master pour la collecte consolidee et le suivi global ;
- extraire ou reporter les donnees validees dans les fichiers DT individuels concernes ;
- conserver une coherence stricte entre la reference DT du master et celle du document individuel ;
- utiliser les statuts pour distinguer les donnees ouvertes, a confirmer, validees ou non applicables.

## Methode de remplissage CEVA

CEVA renseigne prioritairement les cellules jaunes :

1. Completer `00_General` avec la version, la date, le redacteur, le verificateur, l'approbateur et le statut.
2. Mettre a jour `00_Index` pour chaque fonction : statut de completude, responsable CEVA et date de derniere mise a jour.
3. Completer chaque onglet Fxx en partant des donnees generales, puis des tableaux techniques.
4. Utiliser les listes deroulantes pour normaliser les statuts, niveaux, qualifications et responsabilites de fourniture.
5. Renseigner les sources et documents associes pour assurer la tracabilite des donnees.
6. Documenter les hypotheses et commentaires libres lorsque la donnee n'est pas encore stabilisee.

## Conversion future Excel vers YAML

Le principe cible est de convertir les donnees structurees du DT-Master vers les fichiers YAML du referentiel projet.

La conversion future devra :

- lire chaque onglet Fxx comme source de donnees techniques ;
- identifier les sections standard par leurs titres et en-tetes ;
- convertir les lignes renseignees en blocs YAML structures ;
- ignorer les lignes vides ;
- conserver les references DT, statuts, sources, hypotheses et documents associes ;
- produire des YAML compatibles avec l'arborescence `config/documents/technical_data`.

Tant que cette conversion n'est pas automatisee, le classeur Excel reste un support de collecte et de consolidation, et les YAML restent le referentiel technique exploitable par le depot.
