import re
from qgis.PyQt.QtCore import QObject
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.core import QgsSettings
from qgis.gui import QgisInterface
from .core.search import SearchFilter
from . import config
from .utils import custom_logger
from .ui import menus, icons
from .models import catalog_types
from .services import registry

logger = custom_logger.get_logger(__file__)

class GeoBasis_Loader(QObject):  
    search_filter = None

# =========================================================================
    def __init__(self, iface: QgisInterface, parent=None) -> None:
        super().__init__(parent)
        self.iface = iface
        self._qgs_settings = QgsSettings()
        self.toolbar = None
        self.toolbar_main_menu_action = None
        custom_logger.setup_logging()
        registry.property_manager.load_all()
        registry.preset_manager.load_all()
        registry.catalog_manager.get_overview(callback=self.initGui)

        # ------- Letzten Katalog laden --------------------------------------------
        registry.catalog_manager.get_current_catalog(callback=self.set_services)
        
        plugin_menu = self.iface.pluginMenu()
        if plugin_menu:
            self.main_menu = menus.MainMenu(plugin_menu)
            plugin_menu.addMenu(self.main_menu)
        else:
            logger.critical("Konnte Plugin-Menü nicht finden. Menü konnte nicht hinzugefügt werden.")
            self.main_menu = menus.MainMenu(None)

        main_window = self.iface.mainWindow()
        if main_window:
            existing_toolbar = main_window.findChild(QToolBar, config.TOOLBAR_NAME)
            if existing_toolbar:
                self.toolbar = existing_toolbar
            else:
                self.toolbar = self.iface.addToolBar(config.TOOLBAR_NAME)
                if self.toolbar:
                    self.toolbar.setObjectName(config.TOOLBAR_NAME)

            if self.toolbar:
                action_icon = icons.get_icon(icons.IconKey.TOOLBAR_MAIN_MENU_ICON)
                self.toolbar_main_menu_action = QAction(action_icon, config.PLUGIN_NAME_AND_VERSION, main_window)
                self.toolbar_main_menu_action.setObjectName("toolbar-geobasis_loader-main_menu")
                self.toolbar_main_menu_action.triggered.connect(self._show_main_menu)
                self.toolbar.addAction(self.toolbar_main_menu_action)
        
        self.search_filter = SearchFilter()
        self.iface.registerLocatorFilter(self.search_filter)
        
    def initGui(self) -> None:
        if self.main_menu:
            self.main_menu.clear()
            self.main_menu.create_menu()
    
#===================================================================================

    def unload(self):
        self.iface.invalidateLocatorResults()
        self.iface.deregisterLocatorFilter(self.search_filter)
        self.search_filter = None
        if self.main_menu:
            plugin_menu = self.iface.pluginMenu()
            main_window = self.iface.mainWindow()
            if self.toolbar and main_window:
                if self.toolbar_main_menu_action:
                    self.toolbar.removeAction(self.toolbar_main_menu_action)
                    self.toolbar_main_menu_action = None
                
                if len(self.toolbar.actions()) == 0:
                    main_window.removeToolBar(self.toolbar) # type: ignore
                    self.toolbar = None
            if plugin_menu:
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

    def _show_main_menu(self) -> None:
        if not self.main_menu:
            logger.warning("Kein Hauptmenü verfügbar.")
            return

        if self.toolbar and self.toolbar_main_menu_action:
            button = self.toolbar.widgetForAction(self.toolbar_main_menu_action)
            if button:
                pos = button.mapToGlobal(button.rect().bottomLeft())
                self.main_menu.popup(pos)
                return

        self.main_menu.popup(QCursor.pos())
