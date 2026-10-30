from dataclasses import dataclass
from typing import Union
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from ..property_manager import PropertyManager
from ...catalog.catalog_manager import CatalogManager
from ...catalog.models import Region, TopicEntry
from ....core.utils import signal_utils


@dataclass(slots=True, frozen=True)
class FavoriteNode:
    entry: TopicEntry
    
    @property
    def id(self) -> str:
        return self.entry.id
    
    @property
    def title(self) -> str:
        return self.entry.title
    
    @property
    def tooltip(self) -> str:
        return f"{self.title} laden"
    
    @property
    def icon(self) -> QIcon:
        return self.entry.get_icon()

class FavoriteViewModel(QObject):
    favorite_nodes_updated = pyqtSignal(list)
    
    def __init__(self, catalog_manager: CatalogManager, property_manager: PropertyManager):
        super().__init__()
        self._catalog_manager = catalog_manager
        self._property_manager = property_manager
        
        self._favorite_node_dict: dict[str, FavoriteNode] = {}
        self._unreslved_favorites: set[str] = set()
        
        self._catalog_manager.catalog_added.connect(self._on_catalog_added)
        self._property_manager.favorite_changed.connect(self._on_favorites_changed)
    
    def dispose(self):
        self._favorite_node_dict.clear()
        self._unreslved_favorites.clear()
        signal_utils.disconnect_signal(self._catalog_manager.catalog_added, self._on_catalog_added)
        signal_utils.disconnect_all_signals(self)
    
    def _sort_favorites(self):
        self._favorite_node_dict = dict(sorted(self._favorite_node_dict.items(), key=lambda item: item[1].title.lower()))
    
    def build_favorites(self):
        self._favorite_node_dict.clear()
        self._unreslved_favorites.clear()
        
        for favorite_id in self._property_manager.get_favorites():
            entry = self._catalog_manager.get_entry(favorite_id)
            if entry:
                node = FavoriteNode(
                    entry=entry
                )
                self._favorite_node_dict[node.id] = node
            else:
                self._unreslved_favorites.add(favorite_id)
        
        self._sort_favorites()
        self.favorite_nodes_updated.emit(self.get_favorite_nodes())
    
    def _on_catalog_added(self, catalog):
        if not self._unreslved_favorites or not catalog:
            return
        missing_favorites_count = len(self._unreslved_favorites)
        for favorite_id in list(self._unreslved_favorites):     # Copy the set to avoid modification during iteration
            if not favorite_id in catalog.entries:
                continue
            
            entry = catalog.entries[favorite_id]
            if entry:
                node = FavoriteNode(
                    entry=entry
                )
                self._favorite_node_dict[favorite_id] = node
                self._unreslved_favorites.remove(favorite_id)
        
        if len(self._unreslved_favorites) < missing_favorites_count:
            self._sort_favorites()
            self.favorite_nodes_updated.emit(self.get_favorite_nodes())
    
    def _on_favorites_changed(self, changes: dict[str, bool]):
        updates = False
        for favorite_id, is_favorite in changes.items():
            if is_favorite and favorite_id not in self._favorite_node_dict:
                entry = self._catalog_manager.get_entry(favorite_id)
                if entry:
                    node = FavoriteNode(
                        entry=entry
                    )
                    self._favorite_node_dict[favorite_id] = node
                    updates = True
                else:
                    self._unreslved_favorites.add(favorite_id)
            else:
                if not is_favorite and favorite_id in self._favorite_node_dict:
                    self._favorite_node_dict.pop(favorite_id, None)
                    updates = True
        
        if updates:
            self._sort_favorites()
            self.favorite_nodes_updated.emit(self.get_favorite_nodes())

    def get_favorite_nodes(self) -> list[FavoriteNode]:
        return list(self._favorite_node_dict.values())

    def get_missing_count(self) -> int:
        return len(self._unreslved_favorites)