import pathlib
from typing import Optional
from qgis.core import QgsProject
from ..models.preset_types import Preset
from ..operations import bookmark_ops
from .. import config
from ..utils import custom_logger, helpers

logger = custom_logger.get_logger(__name__)

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
                name: str = child.customProperty("gbl_name", "Thema")
                path: Optional[str] = child.customProperty("gbl_path", None)
                crs: Optional[str] = child.customProperty("gbl_crs", None)
                if path is not None and (not path.startswith(parent_path) or parent_path == ""):
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
            if entry["path"] not in preset:
                preset.add_entry(name=entry["name"], path=entry["path"], crs=entry.get("crs") if save_layer_crs else None)
        
        return preset
    
    def remove_user_preset(self, id: str) -> None:
        if not isinstance(id, str):
            logger.critical(f"Ungültiger Typ für Preset-ID: {type(id)}")
            return
        
        preset = self.user_presets.pop(id, None)
        if preset and preset.spatial_bookmark_id:
            bookmark_ops.remove_gbl_spatial_bookmark(preset.spatial_bookmark_id)

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
        except FileNotFoundError:
            return {}               # Kein Fehler, wenn die Datei nicht existiert - Es gibt einfach keine Presets
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