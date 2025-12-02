Introduction
Le projet OLD est un plugin QGis destinés à automatiser le calcul des obligations légales de débroussaillement autour des bâtiments et des infrastructures.
Il s’appuie sur des données cadastrales, forestières et urbanistiques necessitant le plugin cadaastre de QGis : https://docs.3liz.org/QgisCadastrePlugin/extension-qgis/installation/
L’objectif est de déterminer, pour chaque bâtiment, la zone à débroussailler à 50 m et 100 m autour des bâtis d'une zone d'étude.

Objectifs

Identifier les zones à débroussailler.
Générer automatiquement les couches spatiales correspondantes.


Données cadastrales : MAJIC et EDIGEO, importées dans PostgreSQL ou SQLite via l'extension cadastre de QGIS.


Couche Forêt        : Table BD Forêt v2 (2006-2019) ; Peut être trouve dans le flux WFS suivant : https://data.geopf.fr/wfs/ows
Couche Zone d'étude : Couche temporaire à créé sur le projet.

⚠️ Ne pas oublier de charger le cadastre de la commune concernée.

PS: Un projet modèle comportant la couche BD Forêt v2 (2006-2019) et une couche "Zone d'étude" est dans le projet Github, il peut etre ajouté à project_template pour facilité l'utilisation.


Auteurs :
Paul DALLES
Coopérative Provence Forêt
Contact : paul.dalles@provenceforet.fr
