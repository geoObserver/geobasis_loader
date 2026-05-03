import uuid
import pathlib
import json
from functools import singledispatch
from datetime import datetime
from typing import Optional, TypedDict, NotRequired
from dataclasses import dataclass, field, asdict
from qgis.core import QgsProject
from .. import config 
from ..utils import custom_logger
from . import handlers

logger = custom_logger.get_logger(__file__)

@dataclass
class Preset:
    class Entry(TypedDict):
        path: str
        # FIXME: Only available for 3.11+; Is this enough?
        crs: NotRequired[str]
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Preset"
    description: Optional[str] = None
    modified: datetime = datetime.now()
    entries: list[Entry] = field(default_factory=list)
    
    def get_entry(self, path: str) -> Optional[Entry]:
        return next((entry for entry in self.entries if entry["path"] == path), None)
    
    def add_entry(self, path: str, crs: Optional[str], position: Optional[int] = None) -> None:
        entry: Preset.Entry = {"path": path}
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
                path = child.customProperty("gbl_path", None)
                crs = child.customProperty("gbl_crs", None)
                if path is not None and path not in parent_path:
                    entry = Preset.Entry(path=path)
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
            preset.add_entry(path=entry["path"], crs=entry.get("crs") if save_layer_crs else None)
        
        return preset
    
    def remove_user_preset(self, id: str) -> None:
        if not isinstance(id, str):
            logger.critical(f"Ungültiger Typ für Preset-ID: {type(id)}")
            return
        
        self.user_presets.pop(id, None)
    
    @singledispatch
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
        for entry in preset.entries:
            path = entry["path"]
            crs = entry.get("crs")
            handlers.add_topic(path, crs)
    
    def get_user_presets(self) -> list[Preset]:
        return list(self.user_presets.values())

    def get_curated_presets(self) -> list[Preset]:
        return list(self.curated_presets.values())
    
    def load_preset_file(self, file_path: pathlib.Path) -> dict[str, Preset]:
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                preset_file: dict = json.load(file)
            format_version = preset_file.get("format_version", 0.0)
            presets_data = preset_file.get("presets", [])
            presets = {}
            if format_version == 7.0:
                for preset_data in presets_data:
                    preset = Preset(**preset_data)
                    presets[preset.id] = preset
            else:
                logger.critical(f"Ungültige Format-Version der Presets '{file_path}'; Lesen nicht möglich")
            
            return presets
        except json.JSONDecodeError as e:
            logger.critical(f"Ungültiges JSON in Datei '{file_path}': {e}")
            return {}
        except OSError as e:
            logger.critical(f"Fehler beim Lesen der Datei '{file_path}': {e}")
            return {}
        
    def load_all(self) -> None:
        self.user_presets = self.load_preset_file(self.USER_PRESETS_PATH)
        self.curated_presets = self.load_preset_file(self.CURATED_PRESETS_PATH)
    
    def save_user_presets(self) -> None:
        data = {
            "format_version": config.PRESET_FORMAT_VERSION,
            "presets": [asdict(preset) for preset in self.user_presets.values()]
        }
        
        config.PRESETS_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
        
        try:
            with open(self.USER_PRESETS_PATH, "w", encoding="utf-8", newline="\n") as file:
                json.dump(data, file, indent=2)
        except OSError as e:
            logger.critical(f"Fehler beim Schreiben der Datei {self.USER_PRESETS_PATH}: {e}")
        except TypeError as e:
            logger.critical(f"Nicht-serialisierbares Objekt für {self.USER_PRESETS_PATH}: {e}")

singleton = PresetManager()