from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union
from enum import Enum
from ....core import icons
from ....core.types import CatalogEntryServiceType as ServiceType


class EntryType(str, Enum):
    TOPIC = "topic"
    TOPIC_GROUP = "group"
    TOPIC_COMBINATION = "combination"

class CatalogSource(str, Enum):
    LOCAL = "local"
    SERVER = "server"

@dataclass(frozen=True)
class TopicEntry:
    id: str
    title: str
    crs: frozenset[str]
    description: Optional[str] = None
    deprecated: bool = False
    deprecated_message: Optional[str] = None
    keywords: frozenset[str] = field(default_factory=frozenset)
    separator_after: bool = False
    internal_key: Optional[str] = None  # Internal key for catalog index, not part of the public API
    
    @property
    def entry_type(self) -> EntryType:
        raise NotImplementedError("Subclasses must implement the entry_type property.")
    
    def get_icon(self) -> icons.icon_infrastructure.QIcon:
        raise NotImplementedError("Subclasses must implement the get_icon method.")


@dataclass(frozen=True)
class Topic(TopicEntry):
    """A data class to represent a topic (layer) with various attributes."""
    
    uri: str = ""
    service_uri: Optional[str] = None
    server_uri: Optional[str] = None
    uri_pattern: Optional[str] = None
    layer_id: Optional[str] = None
    service_type: ServiceType = ServiceType.WMS
    
    opacity: float = 1.0
    min_scale: Optional[float] = None
    max_scale: Optional[float] = None
    fill_color: Union[str, list[int]] = field(default_factory=lambda: [220, 220, 220])
    stroke_color: Union[str, list[int]] = 'black'
    stroke_width: float = 0.3
    
    @property
    def entry_type(self) -> EntryType:
        return EntryType.TOPIC
    
    def is_vector(self) -> bool:
        return self.service_type in (ServiceType.APIF, ServiceType.WFS, ServiceType.VECTORTILES, ServiceType.ARCGIS_FEATURE_SERVER)
    
    def is_web(self) -> bool:
        return self.service_type == ServiceType.WEB
    
    def get_icon(self) -> icons.icon_infrastructure.QIcon:
        """Returns the appropriate icon for the topic based on its service type."""
        return icons.get_icon(self.service_type)

    
@dataclass(frozen=True)
class TopicGroup(TopicEntry):
    """A data class to represent a group of topics with various attributes. A group of topics is a collection of topics (layers)."""
    
    subtopics: list[Topic] = field(default_factory=list)
    # Custom properties for the group, not part of the public JSON
    subtopic_dict: dict[str, Topic] = field(default_factory=dict, init=False, repr=False)
    
    def __iter__(self):
        yield from self.subtopics
    
    def __len__(self):
        return len(self.subtopics)
    
    def __bool__(self):
        return True
    
    @property
    def entry_type(self) -> EntryType:
        return EntryType.TOPIC_GROUP
    
    def get_subtopic(self, id: str) -> Optional[Topic]:
        return self.subtopic_dict.get(id)
    
    def get_subtopics(self) -> list[Topic]:
        return list(self.subtopics)
    
    def get_icon(self) -> icons.icon_infrastructure.QIcon:
        """Returns the appropriate icon for the topic group."""
        return icons.get_icon(icons.IconKey.FOLDER_CLOSED)


@dataclass(frozen=True)
class TopicCombination(TopicEntry):
    """A data class to represent a combination of topics with various attributes. A combination of topics references existing topics (layers)."""
    
    references: frozenset[str] = field(default_factory=frozenset)
    # Custom properties for the combination, not part of the public JSON
    reference_dict: dict[str, Union[Topic, TopicGroup]] = field(default_factory=dict, init=False, repr=False)
    
    def __iter__(self):
        yield from self.references
    
    def __len__(self):
        return len(self.references)
    
    def __bool__(self):
        return True
    
    @property
    def entry_type(self) -> EntryType:
        return EntryType.TOPIC_COMBINATION
    
    def get_references(self) -> frozenset[str]:
        return self.references
    
    def get_referenced_topic(self, id: str) -> Optional[Union[Topic, TopicGroup]]:
        return self.reference_dict.get(id)
    
    def get_referenced_topics(self) -> list[Union[Topic, TopicGroup]]:
        return list(self.reference_dict.values())
    
    def get_icon(self) -> icons.icon_infrastructure.QIcon:
        """Returns the appropriate icon for the topic combination."""
        return icons.get_icon(icons.IconKey.COMBINATION_ADD)


@dataclass(frozen=True)
class Region:
    """A data class to represent a region with various attributes. A region is a structured collection of topics, groups and combinations."""
    
    id: str
    title: str
    topics: list[TopicEntry] = field(default_factory=list)
    separator_after: bool = False
    # Custom properties for the region, not part of the public JSON
    topic_dict: dict[str, TopicEntry] = field(default_factory=dict, init=False, repr=False)
    
    def __iter__(self):
        yield from self.topics
    
    def __len__(self):
        return len(self.topics)
    
    def __bool__(self):
        return True
    
    def get_topic(self, id: str) -> Optional[TopicEntry]:
        return self.topic_dict.get(id)
    
    def get_topics(self) -> list[TopicEntry]:
        return list(self.topics)
    
    def get_icon(self) -> icons.icon_infrastructure.QIcon:
        """Returns the appropriate icon for the region."""
        return icons.get_icon(icons.IconKey.FOLDER_CLOSED)


@dataclass(frozen=True)
class Catalog:
    """A data class to represent a catalog with various attributes. A catalog is a structured collection of multiple regions."""
    
    id: str
    title: str
    modified: datetime
    format_version: float
    global_crs: frozenset[str]
    author: str
    description: Optional[str] = None
    server_uris: dict[str, str] = field(default_factory=dict)
    uri_patterns: dict[str, str] = field(default_factory=dict)
    regions: list[Region] = field(default_factory=list)
    # Custom properties for the catalog, not part of the public JSON
    entries: dict[str, TopicEntry] = field(default_factory=dict)
    region_dict: dict[str, Region] = field(default_factory=dict, init=False, repr=False)
    
    def __iter__(self):
        yield from self.regions
    
    def __len__(self):
        return len(self.regions)

    def __bool__(self):
        return bool(self.regions)
    
    def get_region(self, id: str) -> Optional[Region]:
        return self.region_dict.get(id)

    def get_regions(self) -> list[Region]:
        return list(self.regions)

    def get_entry(self, id: str) -> Optional[TopicEntry]:
        return self.entries.get(id)
    
    def build_index(self) -> None:
        self.entries.clear()
        combinations = []
        
        for region in self.regions:
            for entry in region.topics:
                self.entries[entry.id] = entry
                region.topic_dict[entry.id] = entry
                
                if isinstance(entry, TopicCombination):
                    combinations.append(entry)
                
                if not isinstance(entry, TopicGroup):
                    continue
                
                for subentry in entry.subtopics:
                    self.entries[subentry.id] = subentry
                    entry.subtopic_dict[subentry.id] = subentry
                    
            self.region_dict[region.id] = region
        
        for combination in combinations:
            for ref_id in combination.references:
                ref_entry = self.entries.get(ref_id)
                if ref_entry is not None:
                    combination.reference_dict[ref_id] = ref_entry


@dataclass(frozen=True)
class CatalogIndexEntry:
    """A data class to represent a catalog index entry with various attributes. A catalog index entry is a structured representation of a single catalog."""
    
    id: str
    title: str
    file: str
    author: Optional[str] = None
    description: Optional[str] = None
    modified: Optional[datetime] = None

@dataclass(frozen=True)
class CatalogIndex:
    """A data class to represent a catalog index with various attributes. A catalog index is a structured collection of multiple catalogs."""
    
    catalog_source: CatalogSource
    modified: datetime
    format_version: float
    catalogs: list[CatalogIndexEntry] = field(default_factory=list)
    
    def __iter__(self):
        yield from self.catalogs
    
    def __len__(self):
        return len(self.catalogs)
    
    def __bool__(self):
        return bool(self.catalogs)
    
    @property
    def id(self) -> str:
        """Returns a unique identifier for the catalog index based on its hash and modified timestamp."""
        return str(hash((self.catalog_source, self.modified, self.format_version, tuple(self.catalogs))))
