import uuid
from datetime import datetime
from typing import Optional, TypedDict
from dataclasses import dataclass, field
from qgis.core import QgsBookmark, QgsApplication
from ..models import catalog_types
from ..utils import custom_logger

logger = custom_logger.get_logger(__name__)

@dataclass
class Preset:
    class BaseEntry(TypedDict):
        name: str
        path: str
        visible: bool
    
    class Entry(BaseEntry, total=False):
        crs: str
        # FIXME: Use id instead of path as key
        subtopic_visible: dict[str, bool]
    
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

    def get_index_of_entry(self, path: str) -> Optional[int]:
        for index, entry in enumerate(self.entries):
            if entry["path"] == path:
                return index
        return None
    
    def add_entry(self, name: str, path: str, visible: bool, subtopics_visible: Optional[dict[str, bool]] = None, crs: Optional[str] = None, position: Optional[int] = None) -> None:
        entry: Preset.Entry = {"name": name, "path": path, "visible": visible}
        if crs is not None:
            entry["crs"] = crs

        if subtopics_visible is not None:
            entry["subtopic_visible"] = subtopics_visible

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
                description += f"- {entry['name']} (CRS: {entry['crs']})"
            else:
                description += f"- {entry['name']}"
            if not entry.get("visible", True):
                description += " [unsichtbar]"
            description += "\n"
        return description.strip()
    
    def complete_description(self) -> str:
        description = self.title + "\n"
        description += self.description + "\n\n" if self.description else ""
        description += self.topic_description()
        return description

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