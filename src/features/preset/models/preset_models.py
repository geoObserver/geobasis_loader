import uuid
from datetime import datetime
from typing import Optional, Generator
from dataclasses import dataclass
from ...catalog import models as catalog_types
from ....core.utils import data_utils


@dataclass
class PresetEntry:
    title: str
    id: str
    visible: bool
    crs: Optional[str] = None
    subtopic_visible: Optional[dict[str, bool]] = None


class Preset:    
    def __init__(
        self,
        id: str,
        title: Optional[str] = None,
        description: Optional[str] = None, 
        modified: Optional[datetime] = None, 
        entries: Optional[list[PresetEntry]] = None, 
        spatial_bookmark_id: Optional[str] = None
    ):
        self._id = id
        self._title = title or "Preset"
        self._description = description
        self._modified = modified if modified else datetime.now()
        self._entries = {entry.id: entry for entry in entries} if entries else {}
        self._spatial_bookmark_id = spatial_bookmark_id
    
    def __contains__(self, item) -> bool:
        if isinstance(item, (catalog_types.Topic, catalog_types.TopicGroup, catalog_types.TopicCombination)):
            item = item.id
        
        if not isinstance(item, str):
            return False
        
        return item in self._entries
    
    def __iter__(self) -> Generator[PresetEntry, None, None]:
        yield from self._entries.values()
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def modified(self) -> datetime:
        return self._modified
    
    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self._modified = datetime.now()
    
    @property
    def description(self) -> Optional[str]:
        return self._description
    
    @description.setter
    def description(self, value: Optional[str]) -> None:
        self._description = value
        self._modified = datetime.now()
    
    @property
    def spatial_bookmark_id(self) -> Optional[str]:
        return self._spatial_bookmark_id
    
    @spatial_bookmark_id.setter
    def spatial_bookmark_id(self, value: Optional[str]) -> None:
        self._spatial_bookmark_id = value
        self._modified = datetime.now()
    
    def get_entry(self, id: str) -> Optional[PresetEntry]:
        return self._entries.get(id)

    def get_index_of_entry(self, id: str) -> Optional[int]:
        return data_utils.get_index_of_entry_in_dict(self._entries, id)
    
    def add_entry(
        self, 
        title: str, 
        id: str,
        visible: bool, 
        subtopics_visible: Optional[dict[str, bool]] = None, 
        crs: Optional[str] = None, 
        position: Optional[int] = None
    ) -> None:
        entry: PresetEntry = PresetEntry(title=title, id=id, visible=visible, subtopic_visible=subtopics_visible, crs=crs)
        self._entries[id] = entry
        if position is not None:
            self.change_order(id, position)
        
        self._modified = datetime.now()
    
    def remove_entry(self, id: str) -> None:
        self._entries.pop(id, None)
        self._modified = datetime.now()

    def change_order(self, id: str, new_position: int) -> None:
        data_utils.change_dict_order(self._entries, id, new_position)
        self._modified = datetime.now()
    
    def entries_description(self) -> str:
        if not self._entries:
            return "Keine Themen"
        
        description = f"Enthaltene Themen ({len(self._entries)} Themen):\n"
        for entry in self._entries.values():
            description += f"- {entry.title}"
            if entry.crs is not None:
                description += f" (CRS: {entry.crs})"
            if not entry.visible:
                description += " [unsichtbar]"
            description += "\n"
        return description.strip()
    
    def complete_description(self) -> str:
        description = self._title + "\n"
        description += self._description + "\n\n" if self._description else ""
        description += self.entries_description()
        return description
    
    # def to_dict(self) -> dict:
    #     return {
    #         "id": self.id,
    #         "title": self.title,
    #         "description": self.description,
    #         # FIXME: A bit convoluted; Better with utc and replace or even better datetime.UTC but only 3.11+
    #         "modified": self.modified.isoformat(timespec="seconds") + "Z",
    #         "spatial_bookmark_id": self.spatial_bookmark_id,
    #         "entries": self.entries,
    #     }
    
    # @classmethod
    # def from_dict(cls, data: dict) -> "Preset":
    #     modified_str = data.get("modified")
    #     modified = datetime.fromisoformat(modified_str.removesuffix("Z")) if modified_str else datetime.now()
    #     spatial_bookmark_id = data.get("spatial_bookmark_id")
    #     if spatial_bookmark_id:
    #         manager = QgsApplication.bookmarkManager()
    #         if manager is not None:
    #             bookmark = manager.bookmarkById(spatial_bookmark_id)
    #             if bookmark.id() != spatial_bookmark_id:
    #                 logger.warning(f"Räumliches Lesezeichen mit ID {spatial_bookmark_id} nicht gefunden. Verknüpfung wird entfernt.")
    #                 spatial_bookmark_id = None
    #         else:
    #             logger.error("QGIS Bookmark Manager nicht verfügbar. Räumliche Lesezeichen können nicht überprüft werden.")
        
    #     return cls(
    #         id=data.get("id", str(uuid.uuid4())),
    #         title=data.get("title", "Preset"),
    #         description=data.get("description"),
    #         modified=modified,
    #         entries=data.get("entries", []),
    #         spatial_bookmark_id=spatial_bookmark_id
    #     )