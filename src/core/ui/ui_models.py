from dataclasses import dataclass, field
from typing import Optional
from ..models import BasicCatalogEntry, BasicCatalogTopicEntry
from ..types import CatalogEntryType
from .. import icons

@dataclass
class BasicTopicEntryUiModel:
    entry: BasicCatalogEntry
    child_nodes: list["BasicTopicEntryUiModel"] = field(default_factory=list)
    
    @property
    def id(self) -> str:
        return self.entry.id
    
    @property
    def title(self) -> str:
        return self.entry.title

    @property
    def tooltip(self) -> str:
        try:
            return self.entry.get_summary()
        except NotImplementedError:
            return self.entry.title
    
    @property
    def additional_node(self) -> Optional["BasicTopicEntryUiModel"]:
        if self.entry.entry_type == CatalogEntryType.TOPIC_GROUP:
            return BasicTopicEntryUiModel(
                entry=self.entry
            )
        return None
    
    def get_icon(self) -> icons.icon_infrastructure.QIcon:
        """Returns the appropriate icon for the topic entry."""

        if len(self.child_nodes) > 0:
            return icons.get_icon(icons.IconKey.FOLDER_CLOSED)
        
        entry_type = self.entry.entry_type
        if entry_type == CatalogEntryType.TOPIC:
            if isinstance(self.entry, BasicCatalogTopicEntry):
                return icons.get_icon(self.entry.service_type)
            else:
                return icons.get_icon(icons.IconKey.GROUP_ADD)
        elif entry_type == CatalogEntryType.TOPIC_GROUP:
            return icons.get_icon(icons.IconKey.GROUP_ADD)
        elif entry_type == CatalogEntryType.TOPIC_COMBINATION:
            return icons.get_icon(icons.IconKey.COMBINATION_ADD)
        else:
            return icons.get_icon(icons.IconKey.FOLDER_CLOSED)