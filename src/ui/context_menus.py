from qgis.PyQt.QtWidgets import QMenu, QAction, QMessageBox
from qgis.utils import iface
from ..core import events
from ..models import catalog_types
from ..operations import bookmark_ops, topic_ops, preset_ops
from ..services import registry
from .dialogs import PresetDialog
from . import icons
from .. import config
from ..utils import custom_logger, helpers

logger = custom_logger.get_logger(__name__)

class PresetContextMenu(QMenu):
    def __init__(self, preset_id, parent=None):
        super().__init__(parent)
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            return
        
        self.preset = preset
        
        load_preset_action = QAction("Preset laden", self)
        load_preset_action.triggered.connect(lambda: preset_ops.add_preset_to_project(self.preset))
        self.addAction(load_preset_action)
        self.addSeparator()

        if preset.spatial_bookmark_id:
            apply_bookmark_action = QAction("Räumliches Lesezeichen anwenden", self)
            apply_bookmark_action.setIcon(icons.get_icon(icons.IconKey.SPATIAL_BOOKMARK_ZOOM))
            apply_bookmark_action.triggered.connect(self._apply_spatial_bookmark)
            remove_bookmark_action = QAction("Räumliches Lesezeichen entfernen", self)
            remove_bookmark_action.setIcon(icons.get_icon(icons.IconKey.DELETE))
            remove_bookmark_action.triggered.connect(self._remove_spatial_bookmark)
            self.addAction(apply_bookmark_action)
            self.addAction(remove_bookmark_action)
        else:
            new_bookmark_action = QAction("Räumliches Lesezeichen erstellen", self)
            new_bookmark_action.setIcon(icons.get_icon(icons.IconKey.SPATIAL_BOOKMARK_NEW))
            new_bookmark_action.triggered.connect(self._create_spatial_bookmark)
            self.addAction(new_bookmark_action)
        
        self.addSeparator()
        
        delete_action = QAction("Preset löschen", self)
        delete_action.triggered.connect(self._delete_user_preset)
        rename_action = QAction("Preset ändern", self)
        rename_action.triggered.connect(self._rename_user_preset)
        self.addAction(rename_action)
        self.addAction(delete_action)
    
    def _delete_user_preset(self) -> None:
        preset_ops.delete_user_preset(self.preset, self.parentWidget())
    
    def _rename_user_preset(self) -> None:
        preset_ops.change_user_preset(self.preset, self.parentWidget())
    
    def _apply_spatial_bookmark(self) -> None:
        preset_ops.apply_spatial_bookmark_from_preset(self.preset)
    
    def _create_spatial_bookmark(self) -> None:
        preset_ops.create_spatial_bookmark_from_preset(self.preset)
    
    def _remove_spatial_bookmark(self) -> None:
        preset_ops.remove_spatial_bookmark_from_preset(self.preset)

class PresetEntryContextMenu(QMenu):
    def __init__(self, preset_id, entry_path, parent=None):
        super().__init__(parent)
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            return
        
        entry = preset.get_entry(entry_path)
        if not entry:
            return
        
        self.preset = preset
        self.entry = entry
        
        load_entry_action = QAction("Eintrag laden", self)
        load_entry_action.triggered.connect(self._load_entry)
        self.addAction(load_entry_action)
        
        text = "Beim Laden ausblenden" if entry.get("visible", True) else "Beim Laden einblenden"
        change_visibility_action = QAction(text, self)
        change_visibility_action.triggered.connect(self._change_entry_visibility)
        self.addAction(change_visibility_action)
        
        current_index = preset.get_index_of_entry(entry_path)
        if current_index is not None and current_index > 0:
            move_up_action = QAction("Eintrag nach oben verschieben", self)
            move_up_action.triggered.connect(self._move_entry_up)
            self.addAction(move_up_action)
        
        if current_index is not None and current_index < len(preset.entries) - 1:
            move_down_action = QAction("Eintrag nach unten verschieben", self)
            move_down_action.triggered.connect(self._move_entry_down)
            self.addAction(move_down_action)
        self.addSeparator()
        
        presets = registry.preset_manager.get_user_presets()
        add_to_preset_menu = QMenu("Zu Preset hinzufügen", self)
        if not presets:
            no_preset_action = QAction("(Keine)", self)
            no_preset_action.setEnabled(False)
            add_to_preset_menu.addAction(no_preset_action)
        
        for preset in presets:
            activated = self.entry["path"] in preset
            
            add_action = QAction(preset.title, self)
            add_action.setObjectName(f"add-preset-{preset.id}")
            add_action.triggered.connect(lambda checked, p=preset: self._add_to_preset(p.id))
            add_action.setEnabled(not activated)
            add_to_preset_menu.addAction(add_action)

        self.addMenu(add_to_preset_menu)
        
        remove_action = QAction("Eintrag entfernen", self)
        remove_action.triggered.connect(self._remove_entry_from_preset)
        self.addAction(remove_action)
    
    def _load_entry(self) -> None:
        preset_ops.load_entry_from_preset(self.preset, self.entry["path"])
    
    def _change_entry_visibility(self) -> None:
        new_state = not self.entry.get("visible", True)
        preset_ops.change_entry_visibility_in_preset(self.preset, self.entry["path"], new_state)
    
    def _move_entry_up(self) -> None:
        new_index = preset_ops.get_new_index(self.preset, self.entry["path"], -1)
        preset_ops.move_entry_in_preset(self.preset, self.entry["path"], new_index)
    
    def _move_entry_down(self) -> None:
        new_index = preset_ops.get_new_index(self.preset, self.entry["path"], 1)
        preset_ops.move_entry_in_preset(self.preset, self.entry["path"], new_index)
    
    # FIXME: Method twice implemented, see TopicsContextMenu
    def _add_to_preset(self, preset_id) -> None:
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            logger.error(f"Preset mit ID '{preset_id}' nicht gefunden. Thema kann nicht hinzugefügt werden.")
            return

        if self.entry["path"] in preset:
            logger.warning(f"Thema '{self.entry['name']}' bereits in Preset '{preset.title}'.")
            return

        preset.add_entry(name=self.entry['name'], path=self.entry['path'], visible=True, position=0)
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()
    
    def _remove_entry_from_preset(self) -> None:
        preset_ops.remove_entry_from_preset(self.preset, self.entry["path"])

class PresetEntrySubtopicContextMenu(QMenu):
    def __init__(self, preset_id, entry_path, subtopic_path, parent=None):
        super().__init__(parent)
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            return
        
        entry = preset.get_entry(entry_path)
        if not entry:
            return
        
        self.preset = preset
        self.entry = entry
        self.subtopic_path = subtopic_path
        
        load_entry_action = QAction("Ebene laden", self)
        load_entry_action.triggered.connect(self._load_entry)
        self.addAction(load_entry_action)
        
        text = "Beim Laden ausblenden" if entry.get("subtopic_visible", {}).get(subtopic_path, True) else "Beim Laden einblenden"
        change_visibility_action = QAction(text, self)
        change_visibility_action.triggered.connect(self._change_subtopic_visibility)
        self.addAction(change_visibility_action)
    
    def _load_entry(self) -> None:
        preset_ops.load_subtopic_from_preset(self.preset, self.entry["path"], self.subtopic_path)
    
    def _change_subtopic_visibility(self) -> None:
        new_state = not self.entry.get("subtopic_visible", {}).get(self.subtopic_path, True)
        preset_ops.change_subtopic_visibility_in_preset(self.preset, self.entry["path"], self.subtopic_path, new_state)

class FavoritesContextMenu(QMenu):
    def __init__(self, topic_path, parent=None):
        super().__init__(parent)
        catalog = registry.catalog_manager.get_current_catalog()
        if not catalog or not isinstance(catalog, catalog_types.Catalog):
            return
        
        topic = catalog.get_entry(topic_path)
        if not topic or not isinstance(
            topic,
            (catalog_types.Topic, catalog_types.TopicGroup, catalog_types.TopicCombination),
        ):
            return
        
        self.topic = topic
        
        delete_action = QAction("Favorit entfernen", self)
        delete_action.triggered.connect(self._delete_favorite)
        self.addAction(delete_action)
    
    def _delete_favorite(self) -> None:
        # parent = iface.mainWindow() if iface is not None and hasattr(iface, 'mainWindow') else None
        
        # confirm = QMessageBox.question(
        #     parent,
        #     "Favorit entfernen",
        #     f"'{self.topic.name}' von Favoriten entfernen?",
        # )
        # if confirm != QMessageBox.StandardButton.Yes:
        #     return

        registry.property_manager.set_favorite(self.topic.path, False)
        registry.property_manager.save(config.QgsSettingsKeys.PROPERTY_FAVORITE)
        events.emit_favorites_updated()

class TopicContextMenu(QMenu):
    def __init__(self, topic_path, parent=None):
        super().__init__(parent)        
        topic = registry.catalog_manager.get_topic_by_path(topic_path)
        if not topic or not isinstance(
            topic, 
            (catalog_types.Topic,
            catalog_types.TopicGroup,
            catalog_types.TopicCombination)
        ):
            return
        
        self.topic = topic
        
        if isinstance(topic, catalog_types.Topic) and topic.topic_type == catalog_types.TopicType.WEB:
            text = "Webseite öffnen"
            func = lambda: topic_ops.open_web_site(topic.uri)
        else:
            text = "Zur Karte hinzufügen"
            func = lambda: topic_ops.add_topic(topic)
        load_action = QAction(text, self)
        load_action.setObjectName(f"load-topic")
        load_action.triggered.connect(func)
        self.addAction(load_action)
        self.addSeparator()
        
        if topic.properties.favorite:
            favorite_action = QAction("Von Favoriten entfernen", self)
        else:
            favorite_action = QAction("Zu Favoriten hinzufügen", self)
        favorite_action.triggered.connect(self._change_favorite)
        self.addAction(favorite_action)
        self.addSeparator()
        
        if not (isinstance(self.topic, catalog_types.Topic) and self.topic.topic_type == catalog_types.TopicType.WEB):
            presets = registry.preset_manager.get_user_presets()
            
            add_to_preset_menu = QMenu("Zu Preset hinzufügen", self)
            remove_from_preset_menu = QMenu("Von Preset entfernen", self)
            if not presets:
                no_preset_action = QAction("(Keine)", self)
                no_preset_action.setEnabled(False)
                add_to_preset_menu.addAction(no_preset_action)
                remove_from_preset_menu.addAction(no_preset_action)
            
            for preset in presets:
                activated = self.topic in preset
                
                add_action = QAction(preset.title, self)
                add_action.setObjectName(f"add-preset-{preset.id}")
                add_action.triggered.connect(lambda checked, p=preset: self._add_to_preset(p.id))
                add_action.setEnabled(not activated)
                add_to_preset_menu.addAction(add_action)
            
                remove_action = QAction(preset.title, self)
                remove_action.setObjectName(f"remove-preset-{preset.id}")
                remove_action.triggered.connect(lambda checked, p=preset: self._remove_from_preset(p.id))
                remove_action.setEnabled(activated)
                remove_from_preset_menu.addAction(remove_action)

            self.addMenu(add_to_preset_menu)
            self.addMenu(remove_from_preset_menu)
            self.addSeparator()
        
        if topic.properties.visible:
            visibility_action = QAction("Thema ausblenden", self)
        else:
            visibility_action = QAction("Thema einblenden", self)
        visibility_action.triggered.connect(self._change_visibility)
        self.addAction(visibility_action)
        
        if topic.properties.enabled:
            enabled_action = QAction("Thema deaktivieren", self)
        else:
            enabled_action = QAction("Thema aktivieren", self)
        enabled_action.triggered.connect(self._change_enabled)
        self.addAction(enabled_action)
    
    def _change_favorite(self) -> None:
        new_value = not self.topic.properties.favorite
        registry.property_manager.set_favorite(self.topic.path, new_value)
        registry.property_manager.save(config.QgsSettingsKeys.PROPERTY_FAVORITE)
        events.emit_favorites_updated()
    
    def _change_visibility(self) -> None:
        new_value = not self.topic.properties.visible
        registry.property_manager.set_visibility(self.topic.path, new_value)
        registry.property_manager.save(config.QgsSettingsKeys.PROPERTY_INVISIBLE)
        events.emit_visibility_updated()
    
    def _change_enabled(self) -> None:
        new_value = not self.topic.properties.enabled
        registry.property_manager.set_enabled(self.topic.path, new_value)
        registry.property_manager.save(config.QgsSettingsKeys.PROPERTY_DISABLED)
        events.emit_enabled_updated()
    
    def _add_to_preset(self, preset_id) -> None:
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            logger.error(f"Preset mit ID '{preset_id}' nicht gefunden. Thema kann nicht hinzugefügt werden.")
            return
        
        if self.topic in preset:
            logger.warning(f"Thema '{self.topic.name}' bereits in Preset '{preset.title}'.")
            return
        
        preset.add_entry(name=self.topic.name, path=self.topic.path, visible=True, position=0)
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()
    
    def _remove_from_preset(self, preset_id) -> None:
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            logger.error(f"Preset mit ID '{preset_id}' nicht gefunden. Thema kann nicht entfernt werden.")
            return
        
        if self.topic not in preset:
            logger.warning(f"Thema '{self.topic.name}' nicht im Preset '{preset.title}'.")
            return
        
        preset.remove_entry(path=self.topic.path)
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()