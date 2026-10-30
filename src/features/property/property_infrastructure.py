import pathlib
from ...core.data_infrastructure import file_handlers
from ...core.settings import PluginSettingsKeys
from ...core.settings.settings_infrastructure import CustomQgsSettings


def convert_old_properties(path: pathlib.Path) -> tuple[list[tuple[str, bool]], list[tuple[str, bool]]]:
    """Migrate legacy JSON settings into current QgsSettings sets.

    This function reads a legacy JSON settings file and converts it into the new QgsSettings format.

    Returns:
        A tuple containing the list of enabled properties and the list of visible properties.
    Args:
        path: Path to the legacy settings JSON file.
    """
    
    data = file_handlers.read_json(path)
    properties = data.get("properties", {})
    
    visible = properties.get("__visible__", {})
    new_visible = [(key, value) for key, value in visible.items() if value]
        
    enabled = properties.get("__loading__", {})
    new_enabled = [(key, value) for key, value in enabled.items() if value]
    return new_enabled, new_visible

def load(property: PluginSettingsKeys, qgs_settings: CustomQgsSettings) -> list[str]:
    property = property.value if isinstance(property, PluginSettingsKeys) else property
    return qgs_settings.value(property, list(), type=list)

def save(property: PluginSettingsKeys, values: list[str], qgs_settings: CustomQgsSettings) -> None:
    property = property.value if isinstance(property, PluginSettingsKeys) else property
    qgs_settings.setValue(property, values)