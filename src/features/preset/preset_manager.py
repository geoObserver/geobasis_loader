import uuid
from typing import Optional
from qgis.PyQt.QtCore import QObject, pyqtSignal
from .models import Preset
from .preset_repository import PresetRepository
from . import preset_infrastructure
from ...core import config
from ...core.utils import custom_logger, signal_utils

logger = custom_logger.get_logger(__name__)


class PresetManager(QObject):
    presets_updated = pyqtSignal()
    preset_added = pyqtSignal(Preset)
    preset_removed = pyqtSignal(str)
    
    def __init__(self, preset_repository: Optional[PresetRepository] = None):
        super().__init__()
        self.preset_repository = preset_repository or PresetRepository()
        self.bookmark_manager.qgis_bookmark_removed.connect(self._remove_spatial_bookmark_from_presets)
    
    def dispose(self) -> None:
        signal_utils.disconnect_all_signals(self)
        self.bookmark_manager.dispose()
        self.deleteLater()
    
    def _create_empty_preset(self, title: str, description: Optional[str] = None) -> Preset:
        return Preset(id=str(uuid.uuid4()), title=title, description=description)
    
    def create_empty_user_preset(self, title: str, description: Optional[str] = None) -> None:
        preset = self._create_empty_preset(title, description)
        self.preset_repository.add_user_preset(preset)
        self.save_presets()
        self.preset_added.emit(preset)

    def create_user_preset_from_project(self, title: str, description: Optional[str] = None, save_layer_crs: bool = False) -> None:
        # TODO: What if old project still with gbl_path?
        entries = preset_infrastructure.create_preset_entries_from_project()        
        preset = self._create_empty_preset(title, description)
        for entry in entries:
            preset.add_entry(title=entry.title, id=entry.id, visible=entry.visible, crs=entry.crs if save_layer_crs else None, subtopics_visible=entry.subtopic_visible)
        
        self.preset_repository.add_user_preset(preset)
        self.save_presets()
        self.preset_added.emit(preset)
    
    def remove_user_preset(self, preset_id: str) -> None:
        self.preset_repository.remove_user_preset(preset_id)
        self.save_presets()
        self.preset_removed.emit(preset_id)
    
    def get_user_preset(self, preset_id: str) -> Optional[Preset]:
        return self.preset_repository.get_user_preset(preset_id)

    def get_user_presets(self) -> list[Preset]:
        return self.preset_repository.get_user_presets()
    
    def has_valid_spatial_bookmark_reference(self, preset: Preset) -> bool:
        bookmark_id = preset.spatial_bookmark_id
        if not bookmark_id:
            return True  # No bookmark reference, so it's valid
        
        try:
            has_bookmark = self.bookmark_manager.has_spatial_bookmark(bookmark_id)
            if has_bookmark:
                return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Überprüfen des räumlichen Lesezeichens mit ID '{bookmark_id}' für Preset '{preset.title}': {e}")
        return True  # Return True to avoid blocking preset loading due to bookmark check failure
    
    def remove_invalid_spatial_bookmark_reference(self, preset: Preset) -> bool:
        has_bookmark = self.has_valid_spatial_bookmark_reference(preset)
        if not has_bookmark:
            logger.warning(f"Räumliches Lesezeichen mit ID '{preset.spatial_bookmark_id}' für Preset '{preset.title}' existiert nicht. Entferne Referenz.")
            preset.spatial_bookmark_id = None
            return True
        return False
    
    def _remove_spatial_bookmark_from_presets(self, bookmark_id: str) -> None:
        changes = False
        for preset in self.preset_repository.get_user_presets():
            if preset.spatial_bookmark_id == bookmark_id:
                preset.spatial_bookmark_id = None
                changes = True
                logger.success(f"Räumliches Lesezeichen mit ID '{bookmark_id}' aus Preset '{preset.title}' entfernt.")
        
        if changes:
            self.save_presets()
            self.presets_updated.emit()
    
    def load_presets(self) -> None:        
        try:
            presets = preset_infrastructure.load_presets(config.PRESETS_DIR)
            self.preset_repository.set_user_presets(presets)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Nutzer-Presets: {e}")
        
        save_needed = False
        for preset in self.preset_repository.get_user_presets():
            save_needed |= self.remove_invalid_spatial_bookmark_reference(preset)
        
        if save_needed:
            self.save_presets()
        self.presets_updated.emit()

    def save_presets(self) -> None:       
        try:
            presets = self.preset_repository._user_presets
            preset_infrastructure.save_presets(config.PRESETS_DIR, presets)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Nutzer-Presets: {e}")