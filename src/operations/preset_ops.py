from functools import singledispatch
from typing import Optional, Union
from qgis.PyQt.QtWidgets import QMessageBox
from ..core import events
from ..models import catalog_types
from . import bookmark_ops
from . import topic_ops
from ..models.preset_types import Preset
from ..services import registry
from ..ui.dialogs import PresetDialog
from ..utils import custom_logger, helpers

logger = custom_logger.get_logger(__name__)

def _get_preset_by_id(preset_id: Union[Preset, str]) -> Optional[Preset]:
    if isinstance(preset_id, Preset):
        return preset_id
    elif not isinstance(preset_id, str):
        logger.error(f"Ungültiger Typ für Preset-ID: {type(preset_id)}. Erwartet wird 'Preset' oder 'str'.")
        return None

    preset = registry.preset_manager.user_presets.get(preset_id)
    if not preset:
        logger.error(f"Preset mit ID '{preset_id}' nicht gefunden.")
        return None
    return preset

def _get_entry_from_preset(preset: Union[Preset, str], entry_path: str) -> Optional[Preset.Entry]:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return None

    entry = preset_obj.get_entry(entry_path)
    if not entry:
        logger.error(f"Eintrag '{entry_path}' nicht im Preset '{preset_obj.title}' gefunden.")
        return None
    return entry

@singledispatch
def add_preset_to_project(preset) -> None:
    logger.critical(f"Nicht unterstützter Typ für Preset: {type(preset)}")

@add_preset_to_project.register(str)
def _(preset_id: str) -> None:
    preset = registry.preset_manager.user_presets.get(preset_id)
    if not preset:
        preset = registry.preset_manager.curated_presets.get(preset_id)
        
    if not preset:
        logger.critical(f"Preset nicht gefunden: {preset_id}")
        return
    
    add_preset_to_project(preset)

@add_preset_to_project.register(Preset)
def _(preset: Preset) -> None:
    failures = 0
    # entries are stored top-to-bottom, but add_layer/add_layer_group insert
    # each new layer/group at the top (position 0). Apply in reverse so the
    # resulting layer-tree order matches the order the preset was saved in.
    for entry in reversed(preset.entries):
        path = entry["path"]
        crs = entry.get("crs")
        visible = entry.get("visible", True)
        subtopics_visibility = entry.get("subtopic_visible", {})
        visiblity = {**subtopics_visibility, path: visible}
        success = topic_ops.add_topic(path, visiblity, crs, False)
        if not success:
            failures += 1
    
    if failures == 0:
        logger.success(f"Preset '{preset.title}' erfolgreich geladen", extra={"show_banner": True})
    else:
        logger.warning(f"Preset '{preset.title}' teilweise geladen: {failures}/{len(preset.entries)} Themen konnten nicht geladen werden", extra={"show_banner": True})

def load_entry_from_preset(preset: Union[Preset, str], entry_path: str) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    entry = _get_entry_from_preset(preset, entry_path)
    if not entry:
        return

    path = entry["path"]
    crs = entry.get("crs")
    visible = entry.get("visible", True)
    subtopics_visibility = entry.get("subtopic_visible", {})
    visiblity = {**subtopics_visibility, path: visible}
    topic_ops.add_topic(path, visiblity, crs, True)

def load_subtopic_from_preset(preset: Union[Preset, str], entry_path: str, subtopic_path: str) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    entry = _get_entry_from_preset(preset, entry_path)
    if not entry:
        return

    subtopic = registry.catalog_manager.get_topic_by_path(subtopic_path)
    if isinstance(subtopic, catalog_types.Topic) and subtopic.topic_type == catalog_types.TopicType.WEB:
        logger.warning(f"Web-Unterthema '{subtopic.name}' kann nicht aus einem Preset geladen werden")
        return

    subtopic_visibility = entry.get("subtopic_visible", {}).get(subtopic_path, True)
    crs = entry.get("crs")
    topic_ops.add_topic(subtopic_path, subtopic_visibility, crs, True)

# FIXME: Rename bookamrk after preset renamed
def create_spatial_bookmark_from_preset(preset: Union[Preset, str]) -> None:
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

def apply_spatial_bookmark_from_preset(preset: Union[Preset, str]) -> None:
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

def remove_spatial_bookmark_from_preset(preset: Union[Preset, str]) -> None:
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

def change_user_preset(preset: Union[Preset, str], parent=None) -> None:    
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

def change_entry_visibility_in_preset(preset: Union[Preset, str], entry_path: str, visible: bool) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    entry = _get_entry_from_preset(preset, entry_path)
    if not entry:
        return

    entry["visible"] = visible
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()

def change_subtopic_visibility_in_preset(preset: Union[Preset, str], entry_path: str, subtopic_path: str, visible: bool) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    entry = _get_entry_from_preset(preset, entry_path)
    if not entry:
        return

    if "subtopic_visible" not in entry:
        entry["subtopic_visible"] = {}
    
    entry["subtopic_visible"][subtopic_path] = visible
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()

def remove_entry_from_preset(preset: Union[Preset, str], entry_path: str) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    entry = _get_entry_from_preset(preset, entry_path)
    if not entry:
        return

    preset_obj.remove_entry(entry_path)
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()

def move_entry_in_preset(preset: Union[Preset, str], entry_path: str, new_index: int) -> None:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return

    preset_obj.change_order(entry_path, new_index)
    registry.preset_manager.save_user_presets()
    events.emit_presets_updated()

def get_new_index(preset: Union[Preset, str], entry_path: str, diff: int) -> int:
    preset_obj = _get_preset_by_id(preset)
    if not preset_obj:
        return 0

    current_index = preset_obj.get_index_of_entry(entry_path)
    if current_index is None:
        return 0

    return max(0, min(len(preset_obj.entries) - 1, current_index + diff))

# FIXME: UI box in ui helper module
# FIXME: Move multiple functions frm preset_service to preset_ops
def delete_user_preset(preset: Union[Preset, str], parent=None) -> None:    
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