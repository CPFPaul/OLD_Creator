
# OLD Creator

## Introduction

Le projet OLD est un plugin QGIS destiné à automatiser le calcul des obligations légales de débroussaillement autour des bâtiments et des infrastructures.
Il s'appuie sur des données cadastrales, forestières et urbanistiques nécessitant le [plugin cadastre](https://docs.3liz.org/QgisCadastrePlugin/extension-qgis/installation/) de QGIS.

L'objectif est de déterminer, pour chaque bâtiment, la zone à débroussailler à 50 m et 100 m autour des bâtis d'une zone d'étude.

## Objectifs

- Identifier les zones à débroussailler.

- Générer automatiquement les couches spatiales correspondantes.


#### Couches nécessaires :

* Données cadastrales : **MAJIC** et **EDIGEO**, importées dans <ins>PostgreSQL</ins> ou <ins>SQLite</ins> via l'[extension cadastre de QGIS](https://docs.3liz.org/QgisCadastrePlugin/extension-qgis/installation/).

* Couche Forêt : Table **BD Forêt v2 (2006-2019)** ; Peut-être trouvé dans le flux WFS suivant : https://data.geopf.fr/wfs/ows

* Couche ***Zone d'étude*** : Couche temporaire à créé sur le projet.

⚠️ Ne pas oublier de charger le cadastre de la commune concernée.

_PS: Un projet modèle comportant la couche **BD Forêt v2 (2006-2019)** et une couche **"Zone d'étude"** est dans le projet Github, il peut etre ajouté à project_template pour facilité l'utilisation._


## Auteurs :
Paul DALLES - Technicien forestier

**Coopérative Provence Forêt**

<ins>Contact</ins> : paul.dalles@provenceforet.fr
