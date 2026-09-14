from qgis.PyQt.QtCore import QObject, Qt
from qgis.gui import QgisInterface


class GeoBasis_Loader(QObject):
    def __init__(self, iface: QgisInterface, parent=None) -> None:
        super().__init__(parent)
        self.iface = iface
        
    def initGui(self) -> None:
        pass
    
#===================================================================================

    def unload(self):
        pass
