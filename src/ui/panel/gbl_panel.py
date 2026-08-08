from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.gui import QgsDockWidget
from . import catalog_tab, settings_tab, favorites_tab, presets_tab
from .. import icons
from ... import config

GBL_PANEL_DOCK = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "gbl_panel.ui")[0]

class GblPanel(QgsDockWidget, GBL_PANEL_DOCK):
    def __init__(self, parent = None):
        QgsDockWidget.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(config.PLUGIN_NAME_AND_VERSION)
        
        # Type hints for UI elements
        self.tabWidget: QtWidgets.QTabWidget = self.tabWidget
        
        # Add tabs
        self.catalog_tab = catalog_tab.CatalogTab(self.tabWidget)
        self.favorites_tab = favorites_tab.FavoritesTab(self.tabWidget)
        self.presets_tab = presets_tab.PresetsTab(self.tabWidget)
        self.settings_tab = settings_tab.SettingsTab(self.tabWidget)
        self.tabWidget.addTab(self.catalog_tab, icons.get_icon(icons.IconKey.CATALOG_GLOBE_ICON), "Katalog")
        self.tabWidget.addTab(self.favorites_tab, icons.get_icon(icons.IconKey.FAVORITE_STAR), "Favoriten")
        self.tabWidget.addTab(self.presets_tab, icons.get_icon(icons.IconKey.PRESET_USER), "Presets")
        self.tabWidget.addTab(self.settings_tab, icons.get_icon(icons.IconKey.SETTINGS), "Einstellungen")
        
        # Connect slots
        self.tabWidget.currentChanged.connect(self._on_tab_changed)
    
    def _on_tab_changed(self, index: int) -> None:
        # Basically Lazy loading of the tabs
        if not self.catalog_tab.initialized:
            return
        
        current_tab = self.tabWidget.widget(index)
        if current_tab == self.favorites_tab and not self.favorites_tab.initialized:
            self.favorites_tab.build_favorites_tree()
        elif current_tab == self.presets_tab and not self.presets_tab.initialized:
            self.presets_tab.build_presets_tree()
    