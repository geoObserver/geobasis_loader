from typing import Optional
from qgis.gui import QgisInterface
from . import catalog_module
from . import property_module
from . import search_module
from . import shared_ui
from .core.utils import custom_logger

logger = custom_logger.get_logger(__name__)


class GeoBasis_Loader:
    def __init__(self, iface: QgisInterface) -> None:
        # Variables
        self.iface = iface
        self.main_menu: Optional[shared_ui.MainMenu] = None
        
        
        # # Initialization
        custom_logger.setup_logging()
        self.data_source_manager = catalog_module.DataSourceManager()
        self.catalog_manager = catalog_module.CatalogManager()
        self.property_manager = property_module.PropertyManager()
        self.search_index = search_module.SearchIndex(self.catalog_manager)
        self.topic_loader = catalog_module.TopicLoader(self.property_manager)
        self.catalog_tree_view_model = catalog_module.ui.CatalogTreeViewModel(self.catalog_manager, self.property_manager)
        self.favorites_view_model = property_module.ui.FavoriteViewModel(self.catalog_manager, self.property_manager)
        
        self.search_filter = search_module.SearchFilter(self.search_index, self.topic_loader)
        self.iface.registerLocatorFilter(self.search_filter)

        # UI components
        
    def initGui(self) -> None:
        plugin_menu = self.iface.pluginMenu()
        if not self.catalog_tree_view_model:
            logger.critical("CatalogTreeViewModel is not initialized. Cannot build the tree view.")
            return
        
        if not self.catalog_manager:
            logger.critical("CatalogManager is not initialized. Cannot build the main menu.")
            return
        
        if not self.property_manager:
            logger.critical("PropertyManager is not initialized. Cannot build the main menu.")
            return
        
        if plugin_menu:
            self.main_menu = shared_ui.MainMenu(self.topic_loader, self.catalog_tree_view_model, parent=plugin_menu)
            plugin_menu.addMenu(self.main_menu)
        else:
            logger.critical("Konnte Plugin-Menü nicht finden. Menü konnte nicht hinzugefügt werden.")
            self.main_menu = shared_ui.MainMenu(self.topic_loader, self.catalog_tree_view_model, parent=None)

        # Fetch data from data sources
        self.property_manager.load_all()
        data_sources = self.data_source_manager.get_all_data_sources()
        self.catalog_manager.fetch_data(data_sources)
        
    def unload(self):
        custom_logger.remove_logging()
        self.iface.invalidateLocatorResults()
        self.iface.deregisterLocatorFilter(self.search_filter)
        self.search_filter = None
        
        if self.main_menu:
            self.main_menu.dispose()
            self.main_menu = None

        self.dispose_objects()
    
    def dispose_objects(self) -> None:
        if self.catalog_tree_view_model:
            self.catalog_tree_view_model.dispose()
            self.catalog_tree_view_model = None
        
        if self.favorites_view_model:
            self.favorites_view_model.dispose()
            self.favorites_view_model = None
        
        if self.catalog_manager:
            self.catalog_manager.dispose()
            self.catalog_manager = None
        
        if self.property_manager:
            self.property_manager.dispose()
            self.property_manager = None
        
        # self.data_source_manager.dispose()
        # self.data_source_manager = None