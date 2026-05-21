from qgis.PyQt.QtWidgets import QMenu, QAction, QMessageBox
from qgis.utils import iface
from ..core import events
from ..models import catalog_types
from ..operations import bookmark_ops
from ..services import registry
from .dialogs import PresetDialog
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
        
        if preset.spatial_bookmark_id:
            apply_bookmark_action = QAction("Räumliches Lesezeichen anwenden", self)
            apply_bookmark_action.triggered.connect(self._apply_spatial_bookmark)
            remove_bookmark_action = QAction("Räumliches Lesezeichen entfernen", self)
            remove_bookmark_action.triggered.connect(self._remove_spatial_bookmark)
            self.addAction(apply_bookmark_action)
            self.addAction(remove_bookmark_action)
        else:
            new_bookmark_action = QAction("Räumliches Lesezeichen erstellen", self)
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
    
    def _apply_spatial_bookmark(self) -> None:
        bookmark = self.preset.get_spatial_bookmark()
        if not bookmark:
            if self.preset.spatial_bookmark_id:
                logger.error(f"Räumliches Lesezeichen für Preset '{self.preset.title}' nicht gefunden. Anwenden nicht möglich.")
            return
        
        helpers.apply_spatial_bookmark(bookmark)
        logger.success(f"Räumliches Lesezeichen für Preset '{self.preset.title}' angewendet.")
    
    def _create_spatial_bookmark(self) -> None:
        id = f"preset-{self.preset.id}"
        name = f"Preset: {self.preset.title}"
        bookmark_id, successful = bookmark_ops.add_gbl_spatial_bookmark(name, id=id)
        if not successful or not bookmark_id:
            logger.error(f"Räumliches Lesezeichen für Preset '{self.preset.title}' konnte nicht erstellt werden.")
            return
        
        self.preset.spatial_bookmark_id = bookmark_id
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()
        logger.success(f"Räumliches Lesezeichen für Preset '{self.preset.title}' erstellt.")
    
    def _remove_spatial_bookmark(self) -> None:
        if not self.preset.spatial_bookmark_id:
            logger.error(f"Preset '{self.preset.title}' hat kein räumliches Lesezeichen. Entfernen nicht möglich.")
            return
        
        success = bookmark_ops.remove_gbl_spatial_bookmark(self.preset.spatial_bookmark_id)
        if not success:
            logger.error(f"Räumliches Lesezeichen für Preset '{self.preset.title}' konnte nicht entfernt werden.")
            return

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
    
    def _add_to_preset(self, preset_id) -> None:
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            logger.error(f"Preset mit ID '{preset_id}' nicht gefunden. Thema kann nicht hinzugefügt werden.")
            return
        
        if self.topic in preset:
            logger.warning(f"Thema '{self.topic.name}' bereits in Preset '{preset.title}'.")
            return
        
        preset.add_entry(name=self.topic.name, path=self.topic.path)
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