from typing import Optional
from qgis.PyQt.QtWidgets import QMenu, QAction
from ..features.catalog import models as catalog_types
from ..app import TopicActions


class TopicContextMenu(QMenu):
    def __init__(self, entry: catalog_types.TopicEntry, topic_actions: TopicActions, parent=None):
        super().__init__(parent)
        if not entry or not isinstance(
            entry,
            catalog_types.TopicEntry
        ):
            return
        
        self.entry = entry
        self.topic_actions = topic_actions
        
        if isinstance(entry, catalog_types.Topic) and entry.service_type == catalog_types.ServiceType.WEB:
            text = "Webseite öffnen"
            func = lambda: self.topic_actions.open_web_site(entry.uri)
        else:
            text = "Zur Karte hinzufügen"
            func = lambda: self.topic_actions.load(entry)
        load_action = QAction(text, self)
        load_action.setObjectName(f"load-topic")
        load_action.triggered.connect(func)
        self.addAction(load_action)
        self.addSeparator()
        
        if self.topic_actions.get_favorite(self.entry):
            favorite_action = QAction("Von Favoriten entfernen", self)
        else:
            favorite_action = QAction("Zu Favoriten hinzufügen", self)
        favorite_action.triggered.connect(self._change_favorite)
        self.addAction(favorite_action)
        self.addSeparator()
        
        # if not (isinstance(self.entry, catalog_types.Topic) and self.entry.service_type == catalog_types.ServiceType.WEB):
        #     presets = registry.preset_manager.get_user_presets()
            
        #     add_to_preset_menu = QMenu("Zu Preset hinzufügen", self)
        #     remove_from_preset_menu = QMenu("Von Preset entfernen", self)
        #     if not presets:
        #         no_preset_action = QAction("(Keine)", self)
        #         no_preset_action.setEnabled(False)
        #         add_to_preset_menu.addAction(no_preset_action)
        #         remove_from_preset_menu.addAction(no_preset_action)
            
        #     for preset in presets:
        #         activated = self.entry in preset
                
        #         add_action = QAction(preset.title, self)
        #         add_action.setObjectName(f"add-preset-{preset.id}")
        #         add_action.triggered.connect(lambda checked, p=preset: self._add_to_preset(p.id))
        #         add_action.setEnabled(not activated)
        #         add_to_preset_menu.addAction(add_action)
            
        #         remove_action = QAction(preset.title, self)
        #         remove_action.setObjectName(f"remove-preset-{preset.id}")
        #         remove_action.triggered.connect(lambda checked, p=preset: self._remove_from_preset(p.id))
        #         remove_action.setEnabled(activated)
        #         remove_from_preset_menu.addAction(remove_action)

        #     self.addMenu(add_to_preset_menu)
        #     self.addMenu(remove_from_preset_menu)
        #     self.addSeparator()
        
        if self.topic_actions.get_visibility(self.entry):
            visibility_action = QAction("Thema ausblenden", self)
        else:
            visibility_action = QAction("Thema einblenden", self)
        visibility_action.triggered.connect(self._change_visibility)
        self.addAction(visibility_action)
        
        if self.topic_actions.get_enabled(self.entry):
            enabled_action = QAction("Thema deaktivieren", self)
        else:
            enabled_action = QAction("Thema aktivieren", self)
        enabled_action.triggered.connect(self._change_enabled)
        self.addAction(enabled_action)
    
    def _change_favorite(self) -> None:
        new_value = not self.topic_actions.get_favorite(self.entry)
        self.topic_actions.set_favorite(self.entry, new_value)
    
    def _change_visibility(self) -> None:
        new_value = not self.topic_actions.get_visibility(self.entry)
        self.topic_actions.set_visibility(self.entry, new_value)
    
    def _change_enabled(self) -> None:
        new_value = not self.topic_actions.get_enabled(self.entry)
        self.topic_actions.set_enabled(self.entry, new_value)
    
    # def _add_to_preset(self, preset_id) -> None:
    #     preset = registry.preset_manager.user_presets.get(preset_id)
    #     if not preset:
    #         logger.error(f"Preset mit ID '{preset_id}' nicht gefunden. Thema kann nicht hinzugefügt werden.")
    #         return
        
    #     if self.topic in preset:
    #         logger.warning(f"Thema '{self.topic.name}' bereits in Preset '{preset.title}'.")
    #         return
        
    #     preset.add_entry(name=self.topic.name, path=self.topic.path, visible=True, position=0)
    #     registry.preset_manager.save_user_presets()
    #     events.emit_presets_updated()
    
    # def _remove_from_preset(self, preset_id) -> None:
    #     preset = registry.preset_manager.user_presets.get(preset_id)
    #     if not preset:
    #         logger.error(f"Preset mit ID '{preset_id}' nicht gefunden. Thema kann nicht entfernt werden.")
    #         return
        
    #     if self.topic not in preset:
    #         logger.warning(f"Thema '{self.topic.name}' nicht im Preset '{preset.title}'.")
    #         return
        
    #     preset.remove_entry(path=self.topic.path)
    #     registry.preset_manager.save_user_presets()
    #     events.emit_presets_updated()

class TopicContextMenuFactory:
    def __init__(self, topic_actions: TopicActions):
        self._topic_actions = topic_actions

    def create(self, entry: catalog_types.TopicEntry, parent=None) -> TopicContextMenu:
        return TopicContextMenu(entry, self._topic_actions, parent)