from ..features.catalog import TopicLoader
from ..features.catalog import models as catalog_types
from ..features.property import PropertyManager


class TopicActions:
    def __init__(self, topic_loader: TopicLoader, property_manager: PropertyManager):
        self._topic_loader = topic_loader
        self._property_manager = property_manager

    def open_web_site(self, url: str):
        self._topic_loader.open_web_site(url)

    def load(self, entry: catalog_types.TopicEntry):
        if isinstance(entry, catalog_types.Topic) and entry.service_type == catalog_types.ServiceType.WEB:
            self._topic_loader.open_web_site(entry.uri)
        else:
            self._topic_loader.add_topic(entry)

    def get_favorite(self, entry: catalog_types.TopicEntry) -> bool:
        return self._property_manager.is_favorite(entry.id)
    
    def get_visibility(self, entry: catalog_types.TopicEntry) -> bool:
        return self._property_manager.is_visible(entry.id)
    
    def get_enabled(self, entry: catalog_types.TopicEntry) -> bool:
        return self._property_manager.is_enabled(entry.id)
    
    def set_favorite(self, entry: catalog_types.TopicEntry, favorite: bool):
        self._property_manager.set_favorite(entry.id, favorite)
    
    def set_visibility(self, entry: catalog_types.TopicEntry, visible: bool):
        self._property_manager.set_visibility(entry.id, visible)
    
    def set_enabled(self, entry: catalog_types.TopicEntry, enabled: bool):
        self._property_manager.set_enabled(entry.id, enabled)

    # def add_to_preset(self, entry, preset_id):
    #     preset = registry.preset_manager.get_preset_by_id(preset_id)
    #     if preset:
    #         preset.add_entry(entry)

    # def remove_from_preset(self, entry, preset_id):
    #     preset = registry.preset_manager.get_preset_by_id(preset_id)
    #     if preset:
    #         preset.remove_entry(entry)