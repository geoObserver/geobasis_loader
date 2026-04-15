from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional, Union
from enum import Enum
from .property_manager import Properties


class TopicType(str, Enum):
    WMS = "ogc_wms"
    WFS = "ogc_wfs"
    WCS = "ogc_wcs"
    APIF = "ogc_api_features"
    VECTORTILES = "ogc_vectortiles"
    WEB = "web"

TopicLike = Union["Topic", "TopicGroup", "TopicCombination"]

def _present_kwargs(data: dict, key_map: dict[str, str]) -> dict:
    """Map JSON keys to dataclass kwargs, but only if the key exists and is not None."""
    kwargs = {}
    for source_key, target_key in key_map.items():
        if data.get(source_key, None) is not None:
            kwargs[target_key] = data[source_key]
    return kwargs

@dataclass
class BasicEntry:
    name: str = "topic unknown"
    separator: bool = False
    path: str = ""
    
    @cached_property
    def properties(self) -> Properties:
        return Properties(self.path)

@dataclass
class Topic(BasicEntry):
    """A data class to represent a topic (layer) with various attributes."""
    
    topic_type: TopicType = TopicType.WMS
    valid_epsg_codes: frozenset[str] = field(default_factory=frozenset)
    keywords: list[str] = field(default_factory=list)
    uri: str = "n.n."
    
    opacity: float = 1.0
    min_scale: Optional[float] = None
    max_scale: Optional[float] = None
    fill_color: Union[str, list[int]] = field(default_factory=lambda: [220, 220, 220])
    stroke_color: Union[str, list[int]] = 'black'
    stroke_width: float = 0.3
    
    # FIXME: Different class for feature services would be cleaner
    def is_vector(self) -> bool:
        return self.topic_type in (TopicType.APIF, TopicType.WFS)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Topic":
        data = data or {}
        key_mapping = {
            "name": "name",
            "type": "topic_type",
            "valid_epsg": "valid_epsg_codes",
            "keywords": "keywords",
            "uri": "uri",
            "opacity": "opacity",
            "minScale": "min_scale",
            "maxScale": "max_scale",
            "fillColor": "fill_color",
            "strokeColor": "stroke_color",
            "strokeWidth": "stroke_width",
            "seperator": "separator"
        }
        kwargs = _present_kwargs(data, key_mapping)
        instance = cls(**kwargs)
        instance.valid_epsg_codes = frozenset(instance.valid_epsg_codes)
        return instance
    
    def to_dict(self) -> dict:
        data = {
            "name": self.name,
            "type": self.topic_type,
            "valid_epsg_codes": self.valid_epsg_codes,
            "keywords": self.keywords,
            "uri": self.uri,
            "opacity": self.opacity,
            "min_scale": self.min_scale,
            "max_scale": self.max_scale,
            "separator": self.separator,
        }
        if self.is_vector():
            data["fill_color"] = self.fill_color
            data["stroke_color"] = self.stroke_color
            data["stroke_width"] = self.stroke_width
        
        return data
    
@dataclass
class TopicGroup(BasicEntry):
    """A data class to represent a group of topics with various attributes. A group of topics is a collection of topics (layers)."""
    
    # Overwrite default values for better understanding
    name: str = "topic group unknown"
    # FIXME: Also allow nested combinations and groups
    subtopics: dict[str, Topic] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)
    
    def get_subtopic(self, key: str) -> Optional[Topic]:
        return self.subtopics.get(key, None)
    
    def get_subtopics(self) -> list[Topic]:
        return list(self.subtopics.values())
    
    @classmethod
    def from_dict(cls, data: dict) -> "TopicGroup":
        data = data or {}
        subtopic_dicts: dict = data.get("layers", {})
        subtopics = {}
        for subtopic_key, subtopic_dict in subtopic_dicts.items():
            subtopic = Topic.from_dict(subtopic_dict)
            subtopics[subtopic_key] = subtopic
        
        data["subtopics"] = subtopics
        key_mapping = {
            "name": "name",
            "keywords": "keywords",
            "subtopics": "subtopics",
            "seperator": "separator"
        }
        kwargs = _present_kwargs(data, key_mapping)
        return cls(**kwargs)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "keywords": self.keywords,
            "subtopics": {k: subtopic.to_dict() for k, subtopic in self.subtopics.items()},
            "separator": self.separator,
        }
    
@dataclass
class TopicCombination(BasicEntry):
    """A data class to represent a combination of topics with various attributes. A combination of topics references existing topics (layers)."""
    
    # Overwrite default values for better understanding
    name: str = "topic combination unknown"
    topic_paths: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TopicCombination":
        data = data or {}
        key_mapping = {
            "name": "name",
            "keywords": "keywords",
            "layers": "topic_paths",
            "seperator": "separator"
        }
        kwargs = _present_kwargs(data, key_mapping)
        return cls(**kwargs)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "keywords": self.keywords,
            "references": self.topic_paths,
            "separator": self.separator,
        }

@dataclass
class Region(BasicEntry):
    """A data class to represent a region with various attributes. A region is a structured collection of topics, groups and combinations."""
    
    name: str = "region unknown"
    topics: dict[str, TopicLike] = field(default_factory=dict)
    
    def get_topic(self, key: str) -> Optional[TopicLike]:
        return self.topics.get(key, None)
    
    def get_topics(self) -> list[TopicLike]:
        return list(self.topics.values())
    
    @classmethod
    def from_dict(cls, data: dict) -> "Region":
        data = data or {}
        topic_dicts: dict = data.get("themen", {})
        topics = {}
        for topic_key, topic_dict in topic_dicts.items():
            if "layers" not in topic_dict:
                topic = Topic.from_dict(topic_dict)
            else:
                layers = topic_dict.get("layers", {})
                if isinstance(layers, dict):
                    topic = TopicGroup.from_dict(topic_dict)
                else:
                    topic = TopicCombination.from_dict(topic_dict)
            topics[topic_key] = topic
        
        data["topics"] = topics
        key_mapping = {
            "menu": "name",
            "topics": "topics",
            "seperator": "separator"
        }
        kwargs = _present_kwargs(data, key_mapping)
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "topics": {k: topic.to_dict() for k, topic in self.topics.items()},
            "separator": self.separator,
        }

@dataclass
class Catalog:
    """A data class to represent a catalog with various attributes. A catalog is a structured collection of multiple regions."""
    
    name: str = "catalog"
    regions: dict[str, Region] = field(default_factory=dict)
    entries: dict[str, TopicLike] = field(default_factory=dict)
    
    def get_region(self, key: str) -> Optional[Region]:
        return self.regions.get(key)

    def get_regions(self) -> list[Region]:
        return list(self.regions.values())
    
    def get_entry(self, key: str) -> Optional[Union[Region, TopicLike]]:
        if "/" not in key:      # If no delimiters -> Only region (or not found)
            return self.get_region(key)
        
        return self.entries.get(key, None)
    
    def build_index(self) -> None:
        self.entries.clear()
        
        for region_key, region in self.regions.items():
            region.path = region_key
            for entry_key, entry in region.topics.items():
                entry.path = f"{region.path}/{entry_key}"
                self.entries[entry.path] = entry
                
                if isinstance(entry, TopicGroup):
                    for subentry_key, subentry in entry.subtopics.items():
                        subentry.path = f"{entry.path}/{subentry_key}"
                        self.entries[subentry.path] = subentry
                # FIXME: Key manipulation, since currently the JSOn doesnt have the full key
                elif isinstance(entry, TopicCombination):
                    full_topic_paths = []
                    for key in entry.topic_paths:
                        full_key = f"{region.path}/{key}"
                        full_topic_paths.append(full_key)
                    entry.topic_paths = full_topic_paths
    
    @classmethod
    def from_dict(cls, data: dict) -> "Catalog":
        data = data or {}
        regions = {}
        for region_key, region_dict in data.items():
            region = Region.from_dict(region_dict)
            regions[region_key] = region
        
        instance = cls(
            regions=regions
        )
        # instance.build_index()
        return instance
    
    def to_dict(self) -> dict:
        return {k: region.to_dict() for k, region in self.regions.items()}