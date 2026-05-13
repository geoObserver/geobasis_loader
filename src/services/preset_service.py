import uuid
import pathlib
import json
from functools import singledispatchmethod
from datetime import datetime
from typing import Optional, TypedDict
from dataclasses import dataclass, field
from qgis.core import QgsProject
from .. import config 
from ..utils import custom_logger, helpers

try:
    from typing import NotRequired
except ImportError:
    NotRequired = object  # type: ignore[assignment]

logger = custom_logger.get_logger(__name__)

@dataclass
class Preset:
    class Entry(TypedDict):
        name: str
        path: str
        # FIXME: Only available for 3.11+; Is this enough?
        crs: NotRequired[str]
    
    # FIXME: Catalog ID?
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Preset"
    description: Optional[str] = None
    modified: datetime = datetime.now()
    entries: list[Entry] = field(default_factory=list)
    
    def get_entry(self, path: str) -> Optional[Entry]:
        return next((entry for entry in self.entries if entry["path"] == path), None)
    
    def add_entry(self, name: str, path: str, crs: Optional[str], position: Optional[int] = None) -> None:
        entry: Preset.Entry = {"name": name, "path": path}
        if crs is not None:
            entry["crs"] = crs
        
        if position is not None:
            self.entries.insert(position, entry)
        else:
            self.entries.append(entry)
        
        self.modified = datetime.now()
    
    def remove_entry(self, path: str) -> None:
        self.entries = [entry for entry in self.entries if entry["path"] != path]
        self.modified = datetime.now()

    def change_order(self, path: str, new_position: int) -> None:
        entry_index = next((i for i, entry in enumerate(self.entries) if entry["path"] == path), None)
        if entry_index is not None:
            entry = self.entries.pop(entry_index)
            self.entries.insert(new_position, entry)
            self.modified = datetime.now()
    
    def topic_description(self) -> str:
        if not self.entries:
            return "Keine Themen"
        
        description = "Enthaltene Themen:\n"
        for entry in self.entries:
            if "crs" in entry:
                description += f"- {entry['name']} (CRS: {entry['crs']})\n"
            else:
                description += f"- {entry['name']}\n"
        
        return description.strip()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            # FIXME: A bit convoluted; Better with utc and replace or even better datetime.UTC but only 3.11+
            "modified": self.modified.isoformat(timespec="seconds") + "Z",
            "entries": self.entries,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Preset":
        modified_str = data.get("modified")
        modified = datetime.fromisoformat(modified_str.removesuffix("Z")) if modified_str else datetime.now()
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "Preset"),
            description=data.get("description"),
            modified=modified,
            entries=data.get("entries", [])
        )

class PresetManager:
    USER_PRESETS_PATH = config.PRESETS_DIR / "user_presets.json"
    CURATED_PRESETS_PATH = config.PRESETS_DIR / "curated_presets.json"
    
    def __init__(self) -> None:
        self.user_presets: dict[str, Preset] = {}
        self.curated_presets: dict[str, Preset] = {}
    
    def create_empty_user_preset(self, title: str, description: Optional[str] = None) -> Preset:
        preset = Preset(title=title, description=description)
        self.user_presets[preset.id] = preset
        return preset
    
    def create_user_preset_from_project(self, title: str, description: Optional[str] = None, save_layer_crs: bool = False) -> Optional[Preset]:
        entries = []
        def _traverse_layer_tree(node, parent_path=""):
            for child in node.children():
                name = child.customProperty("gbl_name", "Thema")
                path = child.customProperty("gbl_path", None)
                crs = child.customProperty("gbl_crs", None)
                if path is not None and path not in parent_path:
                    entry = Preset.Entry(name=name, path=path)
                    if crs is not None:
                        entry["crs"] = crs
                    entries.append(entry)
                    
                _traverse_layer_tree(child, parent_path=path if path is not None else "")
        
        project = QgsProject.instance()
        if project is None:
            return

        layer_tree_root = project.layerTreeRoot()
        if layer_tree_root is None:
            return
        
        _traverse_layer_tree(layer_tree_root)
        
        preset = self.create_empty_user_preset(title, description)
        for entry in entries:
            preset.add_entry(name=entry["name"], path=entry["path"], crs=entry.get("crs") if save_layer_crs else None)
        
        return preset
    
    def remove_user_preset(self, id: str) -> None:
        if not isinstance(id, str):
            logger.critical(f"Ungültiger Typ für Preset-ID: {type(id)}")
            return
        
        self.user_presets.pop(id, None)
    
    @singledispatchmethod
    def add_preset_to_project(self, preset) -> None:
        logger.critical(f"Nicht unterstützter Typ für Preset: {type(preset)}")
    
    @add_preset_to_project.register(str)
    def _(self, preset_id: str) -> None:
        preset = self.user_presets.get(preset_id)
        if not preset:
            preset = self.curated_presets.get(preset_id)
            
        if not preset:
            logger.critical(f"Preset nicht gefunden: {preset_id}")
            return
        
        self.add_preset_to_project(preset)
    
    @add_preset_to_project.register(Preset)
    def _(self, preset: Preset) -> None:
        from ..operations import topic_ops as handlers
        for entry in preset.entries:
            path = entry["path"]
            crs = entry.get("crs")
            handlers.add_topic(path, crs)
    
    def get_user_presets(self) -> list[Preset]:
        return list(self.user_presets.values())

    def get_curated_presets(self) -> list[Preset]:
        return list(self.curated_presets.values())
    
    def load_all(self) -> None:
        self.user_presets = self.load_preset_file(self.USER_PRESETS_PATH)
        self.curated_presets = self.load_preset_file(self.CURATED_PRESETS_PATH)
    
    def load_preset_file(self, file_path: pathlib.Path) -> dict[str, Preset]:
        try:
            preset_file = helpers.read_json(file_path)
            if not isinstance(preset_file, dict):
                logger.critical(f"Ungültiges Format in Preset-Datei {file_path}: Erwartet wird ein JSON-Objekt")
                return {}
        except Exception as e:
            logger.critical(f"Fehler beim Laden der Zusammenstellungen aus {file_path}: {e}")
            return {}
        
        format_version = preset_file.get("format_version", 0.0)
        presets_data = preset_file.get("presets", [])
        presets = {}
        if format_version == 7.0:
            for preset_data in presets_data:
                preset = Preset.from_dict(preset_data)
                presets[preset.id] = preset
        
        return presets
    
    def save_user_presets(self) -> None:
        data = {
            "format_version": config.PRESET_FORMAT_VERSION,
            "presets": [preset.to_dict() for preset in self.user_presets.values()]
        }
        
        try:
            helpers.write_json(data, self.USER_PRESETS_PATH)
        except Exception as e:
            logger.critical(f"Fehler beim Speichern der Zusammenstellungen: {e}")

singleton = PresetManager()