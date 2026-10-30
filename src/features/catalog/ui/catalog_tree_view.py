from typing import Generator, Optional, Union
from dataclasses import dataclass, field
import weakref
from qgis.PyQt import QtCore
from qgis.PyQt.QtGui import QIcon
from ....core import icons
from ..models import Region, TopicEntry, Topic, TopicGroup, TopicCombination, Catalog, CatalogIndex
from ..catalog_manager import CatalogManager
from ...property.property_manager import PropertyManager
from ....core.utils import signal_utils

@dataclass(slots=True)
class EntryNode:
    entry: Union[Region, TopicEntry]
    is_enabled: bool
    is_visible: bool
    is_favorite: bool
    child_nodes: list["EntryNode"] = field(default_factory=list)
    # opened: bool = field(default=False)
    
    def __iter__(self):
        yield from self.child_nodes
    
    @property
    def additional_node(self) -> Optional["EntryNode"]:
        if isinstance(self.entry, TopicGroup):
            return EntryNode(
                entry=self.entry,
                is_enabled=self.is_enabled,
                is_visible=self.is_visible,
                is_favorite=self.is_favorite
            )
        return None
    
    @property
    def id(self) -> str:
        return self.entry.id
    
    @property
    def is_web(self) -> bool:
        return isinstance(self.entry, Topic) and self.entry.is_web()
    
    @property
    def separator(self) -> bool:
        return self.entry.separator_after
    
    @property
    def title(self) -> str:
        return self.entry.title

    @property
    def tooltip(self) -> str:
        if isinstance(self.entry, Topic):
            if self.entry.is_web():
                return f"{self.entry.title} öffnen"
            else:
                return f"{self.entry.title} laden"
        elif isinstance(self.entry, TopicGroup):
            return f"{self.entry.title} [Gruppe, {len(self.entry.get_subtopics())} Themen]"
        elif isinstance(self.entry, TopicCombination):
            return f"{self.entry.title} [Kombination, {len(self.entry.references)} Themen]"
        else:
            return self.entry.title
    
    def get_icon(self) -> QIcon:
        if self.child_nodes:
            # if self.opened:
            #     return icons.get_icon(icons.IconKey.FOLDER_OPEN)
            return icons.get_icon(icons.IconKey.FOLDER_CLOSED)
        else:
            return self.entry.get_icon()

@dataclass(slots=True)
class IndexEntryNode:
    id: str
    title: str

@dataclass(slots=True)
class IndexNode:
    index: CatalogIndex
    catalogs: list[IndexEntryNode] = field(default_factory=list)
    
    def __iter__(self):
        yield from self.catalogs

class CatalogTreeViewModel(QtCore.QObject):
    tree_rebuilt = QtCore.pyqtSignal()
    indices_rebuilt = QtCore.pyqtSignal()
    node_visibility_updated = QtCore.pyqtSignal(dict)
    node_enabled_updated = QtCore.pyqtSignal(dict)
    node_favorite_updated = QtCore.pyqtSignal(dict)
    
    def __init__(self, catalog_manager: CatalogManager, property_manager: PropertyManager, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent)
        self.catalog_manager = catalog_manager
        self.property_manager = property_manager
        
        self.index_nodes: list[IndexNode] = []
        self.root_nodes: list[EntryNode] = []
        self._node_dict: dict[str, EntryNode] = {}
        
        self.catalog_manager.current_catalog_changed.connect(self.build_tree)
        self.catalog_manager.catalog_indices_updated.connect(self.build_index)
        self.property_manager.favorite_changed.connect(self._on_favorite_changed)
        self.property_manager.visibility_changed.connect(self._on_visibility_changed)
        self.property_manager.enabled_changed.connect(self._on_enabled_changed)
    
    def _create_node(self, entry: Union[Region, TopicEntry], parent: Optional[EntryNode] = None) -> EntryNode:
        node = EntryNode(
            entry=entry,
            is_enabled=self.property_manager.is_enabled(entry.id),
            is_visible=self.property_manager.is_visible(entry.id),
            is_favorite=self.property_manager.is_favorite(entry.id)
        )
        if parent:
            parent.child_nodes.append(node)
        self._node_dict[entry.id] = node
        return node

    def clear_tree(self) -> None:
        self.root_nodes.clear()
        self._node_dict.clear()
        self.tree_rebuilt.emit()
    
    def dispose(self) -> None:
        signal_utils.disconnect_signal(self.catalog_manager.current_catalog_changed, self.build_tree)
        signal_utils.disconnect_signal(self.property_manager.favorite_changed, self._on_favorite_changed)
        signal_utils.disconnect_signal(self.property_manager.visibility_changed, self._on_visibility_changed)
        signal_utils.disconnect_signal(self.property_manager.enabled_changed, self._on_enabled_changed)
        signal_utils.disconnect_all_signals(self)
        self.index_nodes.clear()
        self.clear_tree()
        self.deleteLater()

    def build_tree(self, catalog: Catalog) -> None:
        self.root_nodes.clear()
        self._node_dict.clear()
        if catalog is None:
            return
        
        for region in catalog:
            region_node = self._create_node(entry=region)
            self.root_nodes.append(region_node)
            for topic in region:
                topic_node = self._create_node(entry=topic, parent=region_node)
                
                if not isinstance(topic, TopicGroup):
                    continue
                
                # self._create_node(entry=topic, parent=topic_node)
                
                for subtopic in topic:
                    self._create_node(entry=subtopic, parent=topic_node)

        self.tree_rebuilt.emit()
    
    def build_index(self) -> None:
        self.index_nodes.clear()
        for index in self.catalog_manager.get_indices():
            nodes = []
            for catalog in index.catalogs:
                index_entry_node = IndexEntryNode(id=catalog.id, title=catalog.title)
                nodes.append(index_entry_node)
            index_node = IndexNode(index=index, catalogs=nodes)
            self.index_nodes.append(index_node)
        self.indices_rebuilt.emit()
    
    def _on_property_changed(self, changes: dict[str, bool]) -> Generator[tuple[EntryNode, bool], None, None]:
        for entry_id, value in changes.items():
            node = self._node_dict.get(entry_id)
            if node:
                yield node, value
    
    def _on_visibility_changed(self, changes: dict[str, bool]) -> None:
        updates = {}
        for node, is_visible in self._on_property_changed(changes):
            if node.is_visible != is_visible:
                updates[node.id] = is_visible
                node.is_visible = is_visible
        
        if updates:
            self.node_visibility_updated.emit(updates)

    def _on_enabled_changed(self, changes: dict[str, bool]) -> None:
        updates = {}
        for node, is_enabled in self._on_property_changed(changes):
            if node.is_enabled != is_enabled:
                updates[node.id] = is_enabled
                node.is_enabled = is_enabled
        
        if updates:
            self.node_enabled_updated.emit(updates)

    def _on_favorite_changed(self, changes: dict[str, bool]) -> None:
        updates = {}
        for node, is_favorite in self._on_property_changed(changes):
            if node.is_favorite != is_favorite:
                updates[node.id] = is_favorite
                node.is_favorite = is_favorite

        if updates:
            self.node_favorite_updated.emit(updates)
