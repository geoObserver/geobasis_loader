from dataclasses import dataclass
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from ..models.preset_models import Preset, PresetEntry
from ..preset_manager import PresetManager
from ....core.utils import signal_utils
from ....core import icons


@dataclass
class PresetEntryNode:
    entry: PresetEntry
    
    @property
    def id(self) -> str:
        return self.entry.id
    
    @property
    def title(self) -> str:
        return self.entry.title

@dataclass
class PresetNode:
    preset: Preset
    entries: list[PresetEntryNode]
    
    def __iter__(self):
        yield from self.entries
    
    @property
    def id(self) -> str:
        return self.preset.id
    
    @property
    def title(self) -> str:
        return self.preset.title
    
    @property
    def description(self) -> str:
        return self.preset.description or ""
    
    @property
    def complete_description(self) -> str:
        return self.preset.complete_description()
    
    @property
    def icon(self) -> QIcon:
        return icons.get_icon(icons.IconKey.PRESET_USER)

class PresetViewModel(QObject):
    tree_updated = pyqtSignal()
    tree_node_added = pyqtSignal(PresetNode)
    tree_node_removed = pyqtSignal(str)
    
    def __init__(self, preset_manager: PresetManager):
        super().__init__()
        self._preset_manager = preset_manager
        
        self._root_nodes_dict: dict[str, PresetNode] = {}
        
        # Signals
        self._preset_manager.presets_updated.connect(self.build_tree)
        self._preset_manager.preset_added.connect(self._on_preset_added)
        self._preset_manager.preset_removed.connect(self._on_preset_removed)
    
    @property
    def preset_nodes(self) -> list[PresetNode]:
        return list(self._root_nodes_dict.values())
    
    def _clear_nodes(self) -> None:
        self._root_nodes_dict.clear()
        self.tree_updated.emit()
    
    def dispose(self) -> None:
        self._clear_nodes()
        signal_utils.disconnect_all_signals(self)
        self.deleteLater()
    
    def build_tree(self) -> None:
        self._clear_nodes()
        for preset in self._preset_manager.get_user_presets():
            entry_nodes = [PresetEntryNode(entry=entry) for entry in preset]
            preset_node = PresetNode(preset=preset, entries=entry_nodes)
            self._root_nodes_dict[preset.id] = preset_node
        
        self.tree_updated.emit()
    
    def _on_preset_added(self, preset: Preset) -> None:
        entry_nodes = [PresetEntryNode(entry=entry) for entry in preset]
        preset_node = PresetNode(preset=preset, entries=entry_nodes)
        self._root_nodes_dict[preset.id] = preset_node
        self.tree_node_added.emit(preset_node)
    
    def _on_preset_removed(self, preset_id: str) -> None:
        if preset_id in self._root_nodes_dict:
            _ = self._root_nodes_dict.pop(preset_id)
            self.tree_node_removed.emit(preset_id)