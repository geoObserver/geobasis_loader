from typing import Optional
from .models import CatalogIndex, Catalog, TopicEntry
from .catalog_exceptions import CatalogAlreadyExistsError, EntryAlreadyExistsError


class CatalogRepository:    
    def __init__(self):
        self.catalog_indices: dict[str, CatalogIndex] = {}
        self.catalogs: dict[str, Catalog] = {}
        self._entries: dict[str, TopicEntry] = {}
    
    def add_entry(self, entry: TopicEntry) -> None:
        if entry.id in self._entries:
            raise EntryAlreadyExistsError(entry.id)
        
        self._entries[entry.id] = entry

    def _add_entries_from_catalog(self, catalog: Catalog) -> None:
        for entry in catalog.entries.values():
            self.add_entry(entry)
    
    def add_catalog(self, catalog: Catalog) -> None:
        if catalog.id in self.catalogs:
            raise CatalogAlreadyExistsError(catalog.id)
        
        self.catalogs[catalog.id] = catalog
        self._add_entries_from_catalog(catalog)
    
    def add_catalog_index(self, catalog_index: CatalogIndex) -> None:
        if catalog_index.id in self.catalog_indices:
            raise CatalogAlreadyExistsError(catalog_index.id)
        
        self.catalog_indices[catalog_index.id] = catalog_index
    
    def get_entry(self, entry_id: str) -> Optional[TopicEntry]:
        return self._entries.get(entry_id)

    def get_catalog(self, catalog_id: str) -> Optional[Catalog]:
        return self.catalogs.get(catalog_id)
