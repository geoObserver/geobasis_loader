from typing import Optional, Union
from qgis.PyQt.QtWidgets import QMessageBox
from ..core import events
from . import bookmark_ops
from ..services import registry
from ..services import preset_service
from ..ui.dialogs import PresetDialog
from ..utils import custom_logger, helpers

logger = custom_logger.get_logger(__name__)

def _get_preset_by_id(preset_id: Union['preset_service.Preset', str]) -> Optional['preset_service.Preset']:
    if isinstance(preset_id, preset_service.Preset):
        return preset_id
    elif not isinstance(preset_id, str):
        logger.error(f"Ungültiger Typ für Preset-ID: {type(preset_id)}. Erwartet wird 'Preset' oder 'str'.")
        return None

    preset = registry.preset_manager.user_presets.get(preset_id)
    if not preset:
        logger.error(f"Preset mit ID '{preset_id}' nicht gefunden.")
        return None
    return preset

# FIXME: Rename bookamrk after preset renamed
def create_spatial_bookmark_from_preset(preset: Union['preset_service.Preset', str]) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return
    
    id = f"preset-{preset_obj.id}"
    name = f"Preset: {preset_obj.title}"
    bookmark_id, successful = bookmark_ops.add_gbl_spatial_bookmark(name, id=id)
    if not successful or not bookmark_id:
        logger.error(f"Räumliches Lesezeichen für Preset '{preset_obj.title}' konnte nicht erstellt werden.")
        return
    
    preset_obj.spatial_bookmark_id = bookmark_id
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()
    logger.success(f"Räumliches Lesezeichen für Preset '{preset_obj.title}' erstellt.")

def apply_spatial_bookmark_from_preset(preset: Union['preset_service.Preset', str]) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    bookmark = preset_obj.get_spatial_bookmark()
    if not bookmark:
        if preset_obj.spatial_bookmark_id:
            logger.error(f"Räumliches Lesezeichen für Preset '{preset_obj.title}' nicht gefunden. Anwenden nicht möglich.")
        return
    
    helpers.apply_spatial_bookmark(bookmark)
    logger.success(f"Räumliches Lesezeichen für Preset '{preset_obj.title}' angewendet.")

def remove_spatial_bookmark_from_preset(preset: Union['preset_service.Preset', str]) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    if not preset_obj.spatial_bookmark_id:
        logger.error(f"Preset '{preset_obj.title}' hat kein räumliches Lesezeichen. Entfernen nicht möglich.")
        return

    success = bookmark_ops.remove_gbl_spatial_bookmark(preset_obj.spatial_bookmark_id)
    if not success:
        logger.error(f"Räumliches Lesezeichen für Preset '{preset_obj.title}' konnte nicht entfernt werden.")
        return

def new_preset_from_project():
    preset_dialog = PresetDialog()
    if preset_dialog.exec() != PresetDialog.DialogCode.Accepted:
        return
    
    title = preset_dialog.preset_title
    description = preset_dialog.preset_description
    save_layer_crs = preset_dialog.save_layer_crs
    registry.preset_manager.create_user_preset_from_project(title, description, save_layer_crs)
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()

def change_user_preset(preset: Union['preset_service.Preset', str], parent=None) -> None:    
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    preset_dialog = PresetDialog(
        preset_obj.title, 
        preset_obj.description, 
        save_crs_checkbox_visible=False, 
        parent=parent
    )
    if preset_dialog.exec() != PresetDialog.DialogCode.Accepted:
        return
    
    preset_obj.title = preset_dialog.preset_title
    preset_obj.description = preset_dialog.preset_description
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()

# FIXME: UI box in ui helper module
# FIXME: Move multiple functions frm preset_service to preset_ops
def delete_user_preset(preset: Union['preset_service.Preset', str], parent=None) -> None:    
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    confirm = QMessageBox.question(
        parent,
        "Preset löschen",
        f"Preset '{preset_obj.title}' löschen?",
    )
    if confirm != QMessageBox.StandardButton.Yes:
        return

    registry.preset_manager.remove_user_preset(preset_obj.id)
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()