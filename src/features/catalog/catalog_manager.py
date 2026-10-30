from functools import singledispatchmethod
from typing import Optional
from qgis.PyQt.QtCore import pyqtSignal, QObject
from .catalog_repository import CatalogRepository
from .catalog_infrastructure import CatalogDataFetcher
from ...core.settings import PluginSettings
from .models import CatalogIndex, Catalog, TopicEntry, DataSource
from ...core.utils import custom_logger, signal_utils

logger = custom_logger.get_logger(__name__)

class CatalogManager(QObject):
    """Manage catalog data and related operations."""
    current_catalog_changed = pyqtSignal(Catalog)
    catalog_added = pyqtSignal(Catalog)
    catalog_indices_updated = pyqtSignal()
    
    def __init__(self, repository: Optional[CatalogRepository] = None, fetcher: Optional[CatalogDataFetcher] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._settings = PluginSettings()
        self._current_catalog: Optional[Catalog] = None
        self.repo = repository if repository else CatalogRepository()
        self.fetcher = fetcher if fetcher else CatalogDataFetcher()
        
        self.fetcher.catalog_fetched.connect(self._on_catalog_fetched)
        self.fetcher.catalog_index_fetched.connect(self._on_catalog_index_fetched)
    
    def dispose(self) -> None:
        signal_utils.disconnect_signal(self.fetcher.catalog_fetched, self._on_catalog_fetched)
        signal_utils.disconnect_signal(self.fetcher.catalog_index_fetched, self._on_catalog_index_fetched)
        signal_utils.disconnect_all_signals(self)
        self.fetcher.dispose()
    
    @singledispatchmethod
    def set_current_catalog(self, catalog) -> None:
        raise NotImplementedError(f"Can't set current catalog for type {type(catalog)}.")

    @set_current_catalog.register
    def _(self, catalog_id: str) -> None:
        catalog = self.repo.get_catalog(catalog_id)
        if catalog is None:
            logger.error(f"Catalog with ID {catalog_id} not found.")
        self.set_current_catalog(catalog)

    @set_current_catalog.register
    def _(self, catalog: Catalog) -> None:
        if self._current_catalog and self._current_catalog.id == catalog.id:
            return  # No change needed
        
        id = catalog.id
        if id not in self.repo.catalogs:
            logger.error(f"Catalog with ID {id} not found in repository.")
        self._current_catalog = catalog
        self._settings.current_catalog = catalog.id
        # TODO: Version missing. Is it necessary?
        logger.info(f'Katalog gewechselt zu: {catalog.title}', extra={"show_banner": True})
        self.current_catalog_changed.emit(catalog)
    
    def get_current_catalog(self) -> Optional[Catalog]:
        return self._current_catalog
    
    def get_entry(self, entry_id: str) -> Optional[TopicEntry]:
        return self.repo.get_entry(entry_id)
    
    def get_indices(self) -> list[CatalogIndex]:
        return list(self.repo.catalog_indices.values())

    def get_all_catalogs(self) -> list[Catalog]:
        return list(self.repo.catalogs.values())
    
    def fetch_data(self, data_sources: Optional[list[DataSource]] = None) -> None:
        """
        Fetch data from the specified data sources.
        If no data sources are provided, fetch from all previous set data sources.

        Args:
            data_sources (Optional[list[DataSource]], optional): The data sources to fetch from. Defaults to None.
        """
        self.fetcher.fetch_data(data_sources)
    
    # Functions for the infrastructure signals here so they arent in the main.py file
    def _on_catalog_fetched(self, catalog: Catalog) -> None:
        try:
            self.repo.add_catalog(catalog)
        except Exception as e:
            logger.error(f"Failed to add catalog {catalog.id}: {type(e).__name__}, {e}")
        
        current_catalog_id = self._settings.current_catalog
        if current_catalog_id == catalog.id:
            self.set_current_catalog(catalog)
        
        self.catalog_added.emit(catalog)

    def _on_catalog_index_fetched(self, catalog_index: CatalogIndex) -> None:
        try:
            self.repo.add_catalog_index(catalog_index)
            self.catalog_indices_updated.emit()
        except Exception as e:
            logger.error(f"Failed to add catalog index {catalog_index.id}: {type(e).__name__}, {e}")