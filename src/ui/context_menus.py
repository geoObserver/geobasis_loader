from typing import get_args
from qgis.PyQt.QtWidgets import QMenu, QAction, QMessageBox
from qgis.utils import iface
from ..core import events
from ..models import catalog_types
from ..services import registry
from .dialogs import PresetDialog
from .. import config
from ..utils import custom_logger

logger = custom_logger.get_logger(__name__)

class PresetContextMenu(QMenu):
    def __init__(self, preset_id, parent=None):
        super().__init__(parent)
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            return
        
        self.preset = preset
        
        delete_action = QAction("Preset löschen", self)
        delete_action.triggered.connect(self._delete_user_preset)
        rename_action = QAction("Preset ändern", self)
        rename_action.triggered.connect(self._rename_user_preset)
        self.addAction(rename_action)
        self.addAction(delete_action)
    
    def _delete_user_preset(self) -> None:
        parent = iface.mainWindow() if iface is not None and hasattr(iface, 'mainWindow') else None
        
        confirm = QMessageBox.question(
            parent,
            "Preset löschen",
            f"Preset '{self.preset.title}' löschen?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        registry.preset_manager.remove_user_preset(self.preset.id)
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()
    
    def _rename_user_preset(self) -> None:
        if not self.preset:
            logger.error(f"Preset '{self.preset.title}' nicht gefunden. Ändern nicht möglich.")
            return
        
        parent = iface.mainWindow() if iface is not None and hasattr(iface, 'mainWindow') else None
        
        preset_dialog = PresetDialog(
            self.preset.title, 
            self.preset.description, 
            save_crs_checkbox_visible=False, 
            parent=parent
        )
        if preset_dialog.exec() != PresetDialog.DialogCode.Accepted:
            return
        
        self.preset.title = preset_dialog.preset_title
        self.preset.description = preset_dialog.preset_description
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()

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
        
        if topic.properties.favorite:
            favorite_action = QAction("Von Favoriten entfernen", self)
        else:
            favorite_action = QAction("Zu Favoriten hinzufügen", self)
        favorite_action.triggered.connect(self._change_favorite)
        self.addAction(favorite_action)
        
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