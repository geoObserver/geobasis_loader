import uuid
from typing import Union
from datetime import datetime
from .preset_models import Preset, PresetEntry


def parse_preset_file(data: dict) -> dict[str, Preset]:
    """
    Parses a dictionary into a Preset object.

    :param data: Dictionary containing preset data.
    :return: A Preset object.
    :raises ValueError: If the format version is unsupported.
    """
    
    presets_data = data.get("presets", [])
    presets = {}
    for preset_data in presets_data:
        modified_str = preset_data.get("modified")
        modified = datetime.fromisoformat(modified_str.removesuffix("Z")) if modified_str else datetime.now()
        preset = Preset(
            id=preset_data.get("id", str(uuid.uuid4())),
            title=preset_data.get("title", "Preset"),
            description=preset_data.get("description"),
            modified=modified,
            entries=_parse_entries(preset_data.get("entries", [])),
            spatial_bookmark_id=preset_data.get("spatial_bookmark_id")
        )
        presets[preset.id] = preset
    
    return presets

def _parse_entries(data: list[dict]) -> list[PresetEntry]:
    """
    Parses a list of dictionaries into a list of PresetEntry objects.

    :param data: List of dictionaries containing entry data.
    :return: A list of PresetEntry objects.
    """
    
    entries = []
    for entry_data in data:
        entry = PresetEntry(
            title=entry_data.get("name", "Unbekannt"),
            id=entry_data.get("id", ""),
            visible=entry_data.get("visible", True),
            crs=entry_data.get("crs"),
            subtopic_visible=entry_data.get("subtopic_visible")
        )
        entries.append(entry)
    
    return entries

def dump_presets(presets: dict[str, Preset]) -> list[tuple[str, dict]]:
    """
    Dumps a dictionary of Preset objects into a list of dictionaries.

    :param presets: Dictionary of Preset objects.
    :return: A list of dictionaries representing the presets.
    """
    
    return [("user_presets", {
        "format_version": 7.0,
        "presets":
        [
            {
                "id": preset.id,
                "title": preset.title,
                "description": preset.description,
                # FIXME: A bit convoluted; Better with utc and replace or even better datetime.UTC but only 3.11+
                "modified": preset.modified.isoformat(timespec="seconds") + "Z",
                "entries": [entry.__dict__ for entry in preset],
                "spatial_bookmark_id": preset.spatial_bookmark_id
            }
            for preset in presets.values()
        ]
    })]