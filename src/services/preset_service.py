from __future__ import annotations  # PEP 563: keep annotations as strings so
# `crs: NotRequired[str]` is never evaluated on Python 3.9 (QGIS 3.40 LTR on
# macOS ships 3.9, where typing.NotRequired does not exist).
import uuid
import pathlib
from functools import singledispatchmethod
from datetime import datetime
from typing import Optional, TypedDict
from dataclasses import dataclass, field
from qgis.core import QgsProject, QgsBookmark, QgsApplication
from ..models import catalog_types
from ..operations import bookmark_ops
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
        # FIXME: Only available for 3.11+
        crs: NotRequired[str]
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Preset"
    description: Optional[str] = None
    modified: datetime = field(default_factory=datetime.now)
    entries: list[Entry] = field(default_factory=list)
    spatial_bookmark_id: Optional[str] = None
    
    def __contains__(self, item) -> bool:
        if isinstance(item, (catalog_types.Topic, catalog_types.TopicGroup, catalog_types.TopicCombination)):
            item = item.path
        
        if not isinstance(item, str):
            logger.error(f"Ungültiger Typ für Preset-Eintrag: {type(item)}. Erwartet wird ein String.")
            return False
        
        return any(entry["path"] == item for entry in self.entries)
    
    def get_entry(self, path: str) -> Optional[Entry]:
        return next((entry for entry in self.entries if entry["path"] == path), None)
    
    def add_entry(self, name: str, path: str, crs: Optional[str] = None, position: Optional[int] = None) -> None:
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
        
        description = f"Enthaltene Themen ({len(self.entries)} Themen):\n"
        for entry in self.entries:
            if "crs" in entry:
                description += f"- {entry['name']} (CRS: {entry['crs']})\n"
            else:
                description += f"- {entry['name']}\n"
        
        return description.strip()
    
    def get_spatial_bookmark(self) -> Optional[QgsBookmark]:
        if not self.spatial_bookmark_id:
            return None
        
        bookmark_manager = QgsApplication.bookmarkManager()
        if not bookmark_manager:
            logger.error("QGIS Bookmark Manager nicht verfügbar. Räumliche Lesezeichen können nicht abgerufen werden.")
            return None
        
        return bookmark_manager.bookmarkById(self.spatial_bookmark_id)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            # FIXME: A bit convoluted; Better with utc and replace or even better datetime.UTC but only 3.11+
            "modified": self.modified.isoformat(timespec="seconds") + "Z",
            "spatial_bookmark_id": self.spatial_bookmark_id,
            "entries": self.entries,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Preset":
        modified_str = data.get("modified")
        modified = datetime.fromisoformat(modified_str.removesuffix("Z")) if modified_str else datetime.now()
        spatial_bookmark_id = data.get("spatial_bookmark_id")
        if spatial_bookmark_id:
            manager = QgsApplication.bookmarkManager()
            if manager is not None:
                bookmark = manager.bookmarkById(spatial_bookmark_id)
                if bookmark.id() != spatial_bookmark_id:
                    logger.warning(f"Räumliches Lesezeichen mit ID {spatial_bookmark_id} nicht gefunden. Verknüpfung wird entfernt.")
                    spatial_bookmark_id = None
            else:
                logger.error("QGIS Bookmark Manager nicht verfügbar. Räumliche Lesezeichen können nicht überprüft werden.")
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "Preset"),
            description=data.get("description"),
            modified=modified,
            entries=data.get("entries", []),
            spatial_bookmark_id=spatial_bookmark_id
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
        def _traverse_layer_tree(node, ancestor_recorded=False):
            for child in node.children():
                name = child.customProperty("gbl_name", "Thema")
                path = child.customProperty("gbl_path", None)
                crs = child.customProperty("gbl_crs", None)
                # Record only the topmost node carrying a gbl_path (e.g. a group)
                # and skip its descendants, so a loaded group becomes a single
                # preset entry that re-creates the whole group on apply.
                child_recorded = ancestor_recorded
                if path is not None and not ancestor_recorded:
                    entry = Preset.Entry(name=name, path=path)
                    if crs is not None:
                        entry["crs"] = crs
                    entries.append(entry)
                    child_recorded = True

                _traverse_layer_tree(child, ancestor_recorded=child_recorded)
        
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
        failures = 0
        # entries are stored top-to-bottom, but add_layer/add_layer_group insert
        # each new layer/group at the top (position 0). Apply in reverse so the
        # resulting layer-tree order matches the order the preset was saved in.
        for entry in reversed(preset.entries):
            path = entry["path"]
            crs = entry.get("crs")
            success = handlers.add_topic(path, crs, False)
            if not success:
                failures += 1
        
        if failures == 0:
            logger.success(f"Preset '{preset.title}' erfolgreich geladen", extra={"show_banner": True})
        else:
            logger.warning(f"Preset '{preset.title}' teilweise geladen: {failures}/{len(preset.entries)} Themen konnten nicht geladen werden", extra={"show_banner": True})

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
        if format_version == config.PRESET_FORMAT_VERSION:
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