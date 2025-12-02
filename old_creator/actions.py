from qgis.core import *
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import QVariant
from qgis import processing

# --------------------------------------------------
# OUTIL : récupérer une couche par son nom
# --------------------------------------------------
def get_layer(nom):
    layers = QgsProject.instance().mapLayersByName(nom)
    if not layers:
        raise Exception(f"❌ Couche introuvable : {nom}")
    return layers[0]

# --------------------------------------------------
# 1️⃣ DÉFINITION ZONE DE TRAVAIL
# --------------------------------------------------
from qgis.core import QgsProject
import processing
from qgis.PyQt.QtWidgets import QMessageBox

def definition_zone_travail(iface):

    zone = get_layer("Zone d'étude")
    bati = get_layer("Bâti")
    foret = get_layer("BD Forêt v2 (2006-2019)")
    parcelles = get_layer("Parcelles")  # pour récupérer le propriétaire

    if zone.featureCount() == 0:
        QMessageBox.warning(None, "Erreur", "❌ La couche 'Zone d'étude' ne contient aucun polygone.")
        return

    # --- Extraction BÂTI ---
    bati_zone = processing.run("native:extractbylocation", {
        "INPUT": bati,
        "PREDICATE": [0],  # intersect
        "INTERSECT": zone,
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- Copier le propriétaire depuis les parcelles ---
    bati_zone = processing.run("native:joinattributesbylocation", {
        "INPUT": bati_zone,
        "JOIN": parcelles,
        "PREDICATE": [0],
        "JOIN_FIELDS": ["proprietaire"],
        "METHOD": 0,
        "DISCARD_NONMATCHING": False,
        "PREFIX": "",
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- Fusionner les bâti par propriétaire ---
    bati_zone_fusion = processing.run("native:dissolve", {
        "INPUT": bati_zone,
        "FIELD": ["proprietaire"],
        "OUTPUT": "memory:"
    })["OUTPUT"]

    bati_zone_fusion.setName("Bâti zone")
    QgsProject.instance().addMapLayer(bati_zone_fusion)

    # --- Extraction FORÊT ---
    foret_zone = processing.run("native:extractbylocation", {
        "INPUT": foret,
        "PREDICATE": [0],
        "INTERSECT": zone,
        "OUTPUT": "memory:"
    })["OUTPUT"]

    foret_zone.setName("Forêt zone")
    QgsProject.instance().addMapLayer(foret_zone)

    QMessageBox.information(None, "OK", "✅ Zone de travail définie.\nCouches 'Bâti zone' (fusionnée) et 'Forêt zone' créées.")

# --------------------------------------------------
# 2️⃣ ANALYSE OLD COMPLÈTE ET JURIDIQUEMENT PROPRE
# --------------------------------------------------
def analyse_old(iface):
    bati = get_layer("Bâti zone")
    foret = get_layer("Forêt zone")
    parcelles = get_layer("Parcelles")

    # --- 1) Buffer forêt 200 m ---
    foret_buffer = processing.run("native:buffer", {
        "INPUT": foret,
        "DISTANCE": 200,
        "SEGMENTS": 10,
        "DISSOLVE": True,
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- 2) Bâtis proches forêt ---
    bati_proche = processing.run("native:extractbylocation", {
        "INPUT": bati,
        "PREDICATE": [0],
        "INTERSECT": foret_buffer,
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- 3) Jointure propriétaire ---
    bati_join = processing.run("native:joinattributesbylocation", {
        "INPUT": bati_proche,
        "JOIN": parcelles,
        "PREDICATE": [0],
        "JOIN_FIELDS": ["proprietaire"],
        "METHOD": 0,
        "DISCARD_NONMATCHING": True,
        "PREFIX": "",
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- 4) Buffers 50 m et 100 m ---
    buffers = []
    for dist in (50, 100):
        buf = processing.run("native:buffer", {
            "INPUT": bati_join,
            "DISTANCE": dist,
            "SEGMENTS": 10,
            "DISSOLVE": False,
            "OUTPUT": "memory:"
        })["OUTPUT"]

        buf_zone = processing.run("native:fieldcalculator", {
            "INPUT": buf,
            "FIELD_NAME": "zone",
            "FIELD_TYPE": 1,
            "FIELD_LENGTH": 10,
            "FIELD_PRECISION": 0,
            "FORMULA": str(dist),
            "OUTPUT": "memory:"
        })["OUTPUT"]

        buffers.append(buf_zone)

    # --- 5) Fusion 50 + 100 ---
    merged = processing.run("native:mergevectorlayers", {
        "LAYERS": buffers,
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- 6) Découpe des chevauchements inter-propriétaires ---
    decoupe = processing.run("native:intersection", {
        "INPUT": merged,
        "OVERLAY": merged,
        "INPUT_FIELDS": ["proprietaire", "zone"],
        "OVERLAY_FIELDS": ["proprietaire", "zone"],
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- 7) Dissolve final propre ---
    dissolved = processing.run("native:dissolve", {
        "INPUT": decoupe,
        "FIELD": ["proprietaire", "zone"],
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # --- 8) Export SHAPEFILE ---
    crs = dissolved.crs()
    path, _ = QFileDialog.getSaveFileName(
        None,
        "Enregistrer la couche OLD",
        "",
        "Shapefile (*.shp)"
    )
    if not path:
        QMessageBox.information(None, "Annulé", "❌ Enregistrement annulé.")
        return

    QgsVectorFileWriter.writeAsVectorFormat(
        dissolved,
        path,
        "UTF-8",
        crs,
        "ESRI Shapefile"
    )
    QgsProject.instance().addMapLayer(QgsVectorLayer(path, "Zones_OLD", "ogr"))
    QMessageBox.information(None, "✅ Terminé", "Analyse OLD terminée avec succès.")


# --------------------------------------------------
# 3️⃣ NETTOYAGE ET DÉCOUPE FINALE
# --------------------------------------------------
from qgis.core import *
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import QVariant
from qgis import processing

def nettoyage_et_decoupe_old(iface):
    """
    Nettoie et découpe les zones OLD :
    - Coupe les OLD sur la forêt
    - Attribue chaque zone au(x) propriétaire(s) ayant un bâti le plus proche
    - Partage équitable si plusieurs propriétaires sur une zone commune
    - Fusionne les entités par propriétaire et zone
    """

    # Récupération des couches
    old = get_layer("Zones_OLD")
    foret = get_layer("Forêt zone")
    parcelles = get_layer("Parcelles")
    bati = get_layer("Bâti zone")

    # 1️⃣ Intersection OLD / Forêt
    old_foret = processing.run("native:intersection", {
        "INPUT": old,
        "OVERLAY": foret,
        "INPUT_FIELDS": ["zone"],
        "OVERLAY_FIELDS": [],
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # 2️⃣ Couche temporaire pour stocker le propriétaire correct
    old_temp = QgsVectorLayer(f"Polygon?crs={old_foret.crs().authid()}", 
                              "OLD_temp", "memory")
    pr = old_temp.dataProvider()
    pr.addAttributes([
        QgsField("zone", old_foret.fields().field("zone").type()),
        QgsField("proprietaire", QVariant.String)
    ])
    old_temp.updateFields()

    # 3️⃣ Récupération des bâti
    bati_features = list(bati.getFeatures())
    bati_field_names = [f.name() for f in bati.fields()]
    if "proprietaire" in bati_field_names:
        prop_field_name = "proprietaire"
    elif "Proprietaire" in bati_field_names:
        prop_field_name = "Proprietaire"
    else:
        raise Exception("❌ Champ 'proprietaire' introuvable dans Bâti zone")

    # 4️⃣ Attribution des propriétaires basés sur le bâti le plus proche
    distance_calculator = QgsDistanceArea()
    for f in old_foret.getFeatures():
        geom_old = f.geometry()
        zone_val = f["zone"]

        props_avec_bati = set()
        min_dist = None

        for b in bati_features:
            dist = geom_old.distance(b.geometry())
            if dist <= 200:  # zone d'influence
                b_props = b[prop_field_name]
                b_props_list = b_props.split(";") if b_props and ";" in b_props else [b_props]

                if (min_dist is None) or (dist < min_dist):
                    props_avec_bati = set(b_props_list)
                    min_dist = dist
                elif dist == min_dist:
                    props_avec_bati.update(b_props_list)

        if not props_avec_bati:
            props_avec_bati = set(["inconnu"])

        # Création des entités OLD temporaires
        for prop in props_avec_bati:
            new_feat = QgsFeature()
            new_feat.setGeometry(geom_old)
            new_feat.setAttributes([zone_val, prop])
            pr.addFeature(new_feat)

    old_temp.updateExtents()

    # 5️⃣ Partage juridique équitable si chevauchement entre propriétaires
    # On ne considère que les polygones intersectant la forêt
    old_juridique = processing.run("native:union", {
        "INPUT": old_temp,
        "OVERLAY": old_temp,
        "OUTPUT": "memory:"
    })["OUTPUT"]

    # 6️⃣ Attribuer correctement le propriétaire dans les zones communes
    old_final = QgsVectorLayer(f"Polygon?crs={old_juridique.crs().authid()}",
                               "Zones_OLD_finales", "memory")
    pr_final = old_final.dataProvider()
    pr_final.addAttributes([
        QgsField("zone", QVariant.Int),
        QgsField("proprietaire", QVariant.String)
    ])
    old_final.updateFields()

    for f in old_juridique.getFeatures():
        geom = f.geometry()
        zone_val = f["zone"]
        props = f["proprietaire"].split(";") if f["proprietaire"] else ["inconnu"]

        # Si la zone intersecte une parcelle appartenant à un propriétaire, on garde ce propriétaire
        intersecting_props = set()
        for parc in parcelles.getFeatures():
            if geom.intersects(parc.geometry()):
                parc_prop = parc["proprietaire"]
                if parc_prop:
                    intersecting_props.add(parc_prop)

        if intersecting_props:
            props_to_keep = intersecting_props
        else:
            props_to_keep = set(props)

        for prop in props_to_keep:
            new_feat = QgsFeature()
            new_feat.setGeometry(geom)
            new_feat.setAttributes([zone_val, prop])
            pr_final.addFeature(new_feat)

    old_final.updateExtents()

    # 7️⃣ Fusion finale par propriétaire et zone
    old_final_dissolved = processing.run("native:dissolve", {
        "INPUT": old_final,
        "FIELD": ["proprietaire", "zone"],
        "OUTPUT": "memory:"
    })["OUTPUT"]

    old_final_dissolved.setName("Zones_OLD_finales")
    QgsProject.instance().addMapLayer(old_final_dissolved)

    QMessageBox.information(
        None,
        "✅ Nettoyage terminé",
        "Les zones OLD ont été découpées sur la forêt,\n"
        "chaque zone attribuée au(x) propriétaire(s) ayant un bâti le plus proche,\n"
        "les chevauchements ont été partagés juridiquement,\n"
        "et les entités avec le même propriétaire et zone ont été fusionnées."
    )

from qgis.core import QgsProject, QgsFillSymbol, QgsSimpleFillSymbolLayer, QgsSymbolLayerUtils, QgsRendererCategory, QgsCategorizedSymbolRenderer
from qgis.PyQt.QtGui import QColor

def analyse_thematique(iface):
    """
    Modifie la symbologie des couches :
    - Forêt zone : remplissage vert pomme 45% opacité, contour 0.8 px
    - Zones OLD finales : hachures fines pour zone 50m et 100m, hachures opposées
    """

    # 1️⃣ Forêt zone
    try:
        foret = get_layer("Forêt zone")
        symbol = QgsFillSymbol.createSimple({
            'color': '0,255,0,115',  # vert pomme avec alpha 115/255 ~ 45%
            'outline_color': '0,255,0',
            'outline_width': '0.8'
        })
        foret.renderer().setSymbol(symbol)
        foret.triggerRepaint()
    except Exception as e:
        print("⚠️ Erreur Forêt zone :", e)

    # 2️⃣ Zones OLD finales
    try:
        old_final = get_layer("Zones_OLD_finales")

        # Préparer des symboles pour 50m et 100m
        categories = []

        # Zone 50
        symbol_50 = QgsFillSymbol.createSimple({
            'style': 'no',  # pas de remplissage
            'outline_color': '255,0,0',  # rouge
            'outline_width': '0.5'
        })
        symbol_layer_50 = QgsSimpleFillSymbolLayer.create({
            'style': 'forward_diagonal',  # hachure fine
            'color': '255,0,0,0',
            'outline_color': '255,0,0'
        })
        symbol_50.changeSymbolLayer(0, symbol_layer_50)
        categories.append(QgsRendererCategory(50, symbol_50, "50m"))

        # Zone 100
        symbol_100 = QgsFillSymbol.createSimple({
            'style': 'no',  # pas de remplissage
            'outline_color': '0,0,255',  # bleu
            'outline_width': '0.5'
        })
        symbol_layer_100 = QgsSimpleFillSymbolLayer.create({
            'style': 'backward_diagonal',  # hachure croisée
            'color': '0,0,255,0',
            'outline_color': '0,0,255'
        })
        symbol_100.changeSymbolLayer(0, symbol_layer_100)
        categories.append(QgsRendererCategory(100, symbol_100, "100m"))

        renderer = QgsCategorizedSymbolRenderer("zone", categories)
        old_final.setRenderer(renderer)
        old_final.triggerRepaint()

    except Exception as e:
        print("⚠️ Erreur Zones OLD finales :", e)

    iface.messageBar().pushMessage("Analyse thématique", "Symbologie appliquée aux couches", level=0, duration=5)
