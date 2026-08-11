from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.core import QgsSettings, QgsApplication
from qgis.gui import QgisInterface
from . import config
from .utils import custom_logger
from .ui import menus, icons, panel, search_filter
from .services import registry
from .operations import bookmark_ops
from .core import search_index

logger = custom_logger.get_logger(__name__)

class GeoBasis_Loader(QObject):  
    search_filter = None

# =========================================================================
    def __init__(self, iface: QgisInterface, parent=None) -> None:
        super().__init__(parent)
        self.iface = iface
        self._qgs_settings = QgsSettings()
        self.main_menu = None
        self.toolbar = None
        self.toolbar_main_menu_action = None
        self.toolbar_gbl_panel_action = None
        self.gbl_panel = None
        custom_logger.setup_logging()
        registry.property_manager.load_all()
        registry.preset_manager.load_all()
        registry.catalog_manager.get_overview(callback=self.initGui)

        # ------- Letzten Katalog laden --------------------------------------------
        registry.catalog_manager.fetch_and_set_current_catalog()
        
        plugin_menu = self.iface.pluginMenu()
        if plugin_menu:
            self.main_menu = menus.MainMenu(plugin_menu)
            plugin_menu.addMenu(self.main_menu)
        else:
            logger.critical("Konnte Plugin-Menü nicht finden. Menü konnte nicht hinzugefügt werden.")
            self.main_menu = menus.MainMenu(None)
        
        self.gbl_panel = panel.GblPanel(parent=self.iface.mainWindow())

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
                # Main menu action
                action_icon = icons.get_icon(icons.IconKey.TOOLBAR_MAIN_MENU_ICON)
                self.toolbar_main_menu_action = QAction(action_icon, config.PLUGIN_NAME_AND_VERSION, main_window)
                self.toolbar_main_menu_action.setObjectName("toolbar-geobasis_loader-main_menu")
                self.toolbar_main_menu_action.triggered.connect(self._show_main_menu)
                self.toolbar.addAction(self.toolbar_main_menu_action)
                
                # GBL panel action
                action_icon = icons.get_icon(icons.IconKey.TOOLBAR_GBL_PANEL_ICON)
                self.toolbar_gbl_panel_action = QAction(action_icon, "Katalogbrowser öffnen/schließen", main_window)
                self.toolbar_gbl_panel_action.setObjectName("toolbar-geobasis_loader-gbl_panel")
                self.toolbar_gbl_panel_action.setCheckable(True)
                self.gbl_panel.setToggleVisibilityAction(self.toolbar_gbl_panel_action)
                self.toolbar.addAction(self.toolbar_gbl_panel_action)
        
            self.search_filter = search_filter.SearchFilter()
            self.iface.registerLocatorFilter(self.search_filter)
        
        manager = QgsApplication.bookmarkManager()
        if manager is not None:
            manager.bookmarkRemoved.connect(bookmark_ops._remove_gbl_spatial_bookmark_from_presets)
            
        # Apply user settings
        gbl_panel_visible = self._qgs_settings.value(config.QgsSettingsKeys.SHOW_GBL_PANEL, False, type=bool)
        if self.gbl_panel:
            self.gbl_panel.setUserVisible(gbl_panel_visible)
        
    def initGui(self) -> None:
        if self.main_menu:
            self.main_menu.clear()
            self.main_menu.create_menu()
        
        if self.gbl_panel:
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.gbl_panel)
            self.gbl_panel.closedStateChanged.connect(self._on_gbl_panel_closed_state_changed)
    
#===================================================================================

    def unload(self):
        registry.catalog_manager.clear_network_handlers(force=True)
        search_index.clear()
        self.iface.invalidateLocatorResults()
        self.iface.deregisterLocatorFilter(self.search_filter)
        self.search_filter = None
        
        if self.gbl_panel:
            self.gbl_panel.setUserVisible(False)
            self.iface.removeDockWidget(self.gbl_panel)
            self.gbl_panel.setParent(None)
            self.gbl_panel.deleteLater()
            self.gbl_panel = None
        
        manager = QgsApplication.bookmarkManager()
        if manager is not None:
            try:
                manager.bookmarkRemoved.disconnect(bookmark_ops._remove_gbl_spatial_bookmark_from_presets)
            except (TypeError, RuntimeError):
                # Slot was never connected (manager unavailable at init) or the
                # C++ object is gone; nothing to disconnect on unload.
                pass
        if self.main_menu:
            plugin_menu = self.iface.pluginMenu()
            main_window = self.iface.mainWindow()
            if self.toolbar and main_window:
                if self.toolbar_main_menu_action:
                    self.toolbar.removeAction(self.toolbar_main_menu_action)
                    self.toolbar_main_menu_action = None
                
                if self.toolbar_gbl_panel_action:
                    self.toolbar.removeAction(self.toolbar_gbl_panel_action)
                    self.toolbar_gbl_panel_action = None
                
                if len(self.toolbar.actions()) == 0:
                    main_window.removeToolBar(self.toolbar) # type: ignore
                    self.toolbar = None
            if plugin_menu:
                plugin_menu.removeAction(self.main_menu.menuAction())
            self.main_menu = None
        custom_logger.remove_logging()

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
    
    def _on_gbl_panel_closed_state_changed(self, was_closed: bool) -> None:
        self._qgs_settings.setValue(config.QgsSettingsKeys.SHOW_GBL_PANEL, not was_closed)
    