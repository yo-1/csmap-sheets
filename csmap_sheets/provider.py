from pathlib import Path
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider
from .algorithm import CSMapAlgorithm


class CSMapProvider(QgsProcessingProvider):
    def id(self):
        return "csmapsheets"

    def name(self):
        return "CS Map Sheets"

    def longName(self):
        return "CS Map Sheets — 国土基本図図郭出力"

    def icon(self):
        return QIcon(str(Path(__file__).with_name("icon.svg")))

    def loadAlgorithms(self):
        self.addAlgorithm(CSMapAlgorithm())
