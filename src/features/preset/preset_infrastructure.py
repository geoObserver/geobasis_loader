from typing import Optional
from pathlib import Path
from qgis.core import QgsProject, QgsLayerTreeNode
from .models import Preset, v7_preset_loader
from .models.preset_models import PresetEntry
from ...core.data_infrastructure import file_handlers
from ...core import config


# TODO: Change (remove internal_key) in 3.0
def create_preset_entries_from_project() -> list[PresetEntry]:
    entries: list[PresetEntry] = []
    def _traverse_layer_tree(node: QgsLayerTreeNode, parent_path: str = "") -> None:
        for child in node.children():
            properties = child.customProperties()
            name: str = child.customProperty("gbl_name", "Thema")
            crs: Optional[str] = child.customProperty("gbl_crs", None)
            if "gbl_id" not in properties:
                path: Optional[str] = child.customProperty("gbl_path", None)
                if path is not None:
                    if not path.startswith(parent_path) or parent_path == "":
                        entry = PresetEntry(title=name, id=path, visible=child.itemVisibilityChecked())
                        entry.crs = crs
                        entries.append(entry)
                    elif path.startswith(parent_path):
                        entry = next((e for e in entries if e.id == parent_path), None)
                        if entry:
                            subtopics_visible = entry.subtopic_visible or {}
                            subtopics_visible[path] = child.itemVisibilityChecked()
                            entry.subtopic_visible = subtopics_visible
                _traverse_layer_tree(child, parent_path=path if path is not None else "")
            else:
                id: Optional[str] = child.customProperty("gbl_id", None)
                parent_id: Optional[str] = child.customProperty("gbl_parent", None)
                if id is not None:
                    if not parent_id or parent_path == "":
                        entry = PresetEntry(title=name, id=id, visible=child.itemVisibilityChecked())
                        entry.crs = crs
                        entries.append(entry)
                    else:
                        parent = child.parent()
                        entry = next((e for e in entries if e.id == parent_path), None)
                        if entry and parent is not None and parent.customProperty("gbl_id", None) == parent_id:
                            subtopics_visible = entry.subtopic_visible or {}
                            subtopics_visible[id] = child.itemVisibilityChecked()
                            entry.subtopic_visible = subtopics_visible
                        
                _traverse_layer_tree(child, parent_path=id if id is not None else "")
    
    project = QgsProject.instance()
    if project is None:
        return entries

    layer_tree_root = project.layerTreeRoot()
    if layer_tree_root is None:
        return entries
    
    _traverse_layer_tree(layer_tree_root)
    
    return entries

def load_presets(folder_path: Path) -> dict[str, Preset]:
    """
    Loads presets from a JSON preset file.

    :param folder_path: Path to the folder containing the JSON file(s) with the preset(s).
    :return: A Preset object.
    :raises ValueError: If the file format is invalid or if the format version is unsupported.
    :raises FileNotFoundError: If the folder does not exist or is not a directory.
    """
    
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path} does not exist.")
    
    if not folder_path.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path} is not a directory.")
    
    presets = {}
    for file_path in folder_path.glob("*.json"):
        preset_data = file_handlers.read_json(file_path)
        if not isinstance(preset_data, dict):
            raise ValueError(f"Ungültiges Format in Preset-Datei {file_path}: Erwartet wird ein JSON-Objekt")
        
        format_version = preset_data.get("format_version", 0.0)
        if format_version == 7.0:
            preset = v7_preset_loader.parse_preset_file(preset_data)
            presets.update(preset)

    return presets

def save_presets(folder_path: Path, presets: dict[str, Preset]) -> None:
    """
    Saves presets to a JSON preset file or multiple JSON files, depending on the format version.

    :param folder_path: Path to the folder where the JSON file(s) with the preset(s) will be saved.
    :param presets: A dictionary of Preset objects to be saved.
    :raises FileNotFoundError: If the folder does not exist or is not a directory.
    :raises ValueError: If the format version is unsupported.
    """
    
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path} does not exist.")
    
    if not folder_path.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path} is not a directory.")
    
    if config.PRESET_FORMAT_VERSION == 7.0:
        for file_name, data in v7_preset_loader.dump_presets(presets):
            file_path = folder_path / f"{file_name}.json"
            file_handlers.write_json(data, file_path)
    else:
        raise ValueError(f"Unsupported preset format version: {config.PRESET_FORMAT_VERSION}")
