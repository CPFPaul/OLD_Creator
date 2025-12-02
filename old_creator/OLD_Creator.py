from qgis.PyQt.QtWidgets import QAction
from qgis.utils import iface

from .actions import (
    definition_zone_travail,
    analyse_old,
    nettoyage_et_decoupe_old,
    analyse_thematique
)


class OldCreator:

    def __init__(self, iface):
        self.iface = iface

    def initGui(self):

        # -------- ACTION 1 : DÉFINITION ZONE DE TRAVAIL --------
        self.action_zone = QAction("1️ - Définition zone de travail", self.iface.mainWindow())
        self.action_zone.triggered.connect(lambda: definition_zone_travail(self.iface))
        self.iface.addPluginToMenu("OLD Creator", self.action_zone)

        # -------- ACTION 2 : ANALYSE OLD --------
        self.action_analyse = QAction("2️ - Analyse OLD", self.iface.mainWindow())
        self.action_analyse.triggered.connect(lambda: analyse_old(self.iface))
        self.iface.addPluginToMenu("OLD Creator", self.action_analyse)

        # -------- ACTION 3 : NETTOYAGE & DÉCOUPE --------
        self.action_nettoyage = QAction("3️ - Nettoyage et découpe OLD", self.iface.mainWindow())
        self.action_nettoyage.triggered.connect(lambda: nettoyage_et_decoupe_old(self.iface))
        self.iface.addPluginToMenu("OLD Creator", self.action_nettoyage)

        # -------- ACTION 4 : ANALYSE THÉMATIQUE --------
        self.action_thematique = QAction("4️ - Analyse thématique", self.iface.mainWindow())
        self.action_thematique.triggered.connect(lambda: analyse_thematique(self.iface))
        self.iface.addPluginToMenu("OLD Creator", self.action_thematique)

    def unload(self):

        self.iface.removePluginMenu("OLD Creator", self.action_zone)
        self.iface.removePluginMenu("OLD Creator", self.action_analyse)
        self.iface.removePluginMenu("OLD Creator", self.action_nettoyage)
        self.iface.removePluginMenu("OLD Creator", self.action_thematique)
