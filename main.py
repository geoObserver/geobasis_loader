import re
from typing import Optional
from qgis.PyQt.QtWidgets import QMenu
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QObject
from qgis.core import QgsSettings
from qgis.gui import QgisInterface
from .src.core.search import SearchFilter
from .src import config
from .src.utils import custom_logger
from .src import ui as custom_ui
from .src.models import catalog_types
from .src.services import registry
logger = custom_logger.get_logger(__file__)

STAR_PREFIX = "\u2605 "  # ★

class GeoBasis_Loader(QObject):  
    search_filter = None

# =========================================================================
    def __init__(self, iface: QgisInterface, parent=None) -> None:
        super().__init__(parent)
        self.iface = iface
        self._qgs_settings = QgsSettings()
        custom_logger.setup_logging()
        registry.property_manager.load_all()
        registry.preset_manager.load_all()
        registry.catalog_manager.get_overview(callback=self.initGui)

        # # ------- Letzten Katalog laden --------------------------------------------
        # current_catalog = self._qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        # if current_catalog is not None and "name" in current_catalog:
        #     CatalogManager.get_catalog(current_catalog["titel"], current_catalog["name"], self.set_services)
        
        plugin_menu = self.iface.pluginMenu()
        if plugin_menu:
            self.main_menu = custom_ui.MainMenu(plugin_menu)
            plugin_menu.addMenu(self.main_menu)
        else:
            logger.critical("Konnte Plugin-Menü nicht finden. Menü konnte nicht hinzugefügt werden.")
            self.main_menu = custom_ui.MainMenu(None)
        
        self.search_filter = SearchFilter(self)
        self.iface.registerLocatorFilter(self.search_filter)    
        #self.iface.messageBar().pushMessage(self.myPluginV,f'Sollte Euch das Plugin gefallen,{"&nbsp;"}könnt Ihr es gern mit Eurer Mitarbeit,{"&nbsp;"}einem Voting und ggf.{"&nbsp;"}einem kleinen Betrag unterstützen ...{"&nbsp;"}Danke!!', 3, 8)     
    
    def initGui(self) -> None:
        if self.main_menu:
            self.main_menu.clear()
            self.main_menu.create_menu()
    
#===================================================================================

    def unload(self):
        self.iface.invalidateLocatorResults()
        self.iface.deregisterLocatorFilter(self.search_filter)
        self.search_filter = None
        plugin_menu = self.iface.pluginMenu()
        if self.main_menu and plugin_menu:
            plugin_menu.removeAction(self.main_menu.menuAction())
            self.main_menu = None
        custom_logger.remove_logging()
        
    def set_services(self, services: catalog_types.Catalog):
        current_catalog = self._qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is None or "titel" not in current_catalog:
            logger.warning(f"Momentan ist kein valider Katalog ausgewählt, Bitten wählen Sie einen aus", extra={"show_banner": True})
            return
        
        titel = current_catalog["titel"]
        name = current_catalog["name"]
        version_matches = re.findall(r'v\d+', name)
        version = version_matches[0] if version_matches else "unbekannt"
        logger.success(f'Lese {titel}, Version {version} ...', extra={"show_banner": True})
        
        self.initGui()
