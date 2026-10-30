from typing import Union, Optional, Any
from qgis.core import QgsSettings
from .settings_models import SettingsKeys, PluginSettingsKeys, QgsSettingsKeys

class CustomQgsSettings:
    def __init__(self):
        self._qgs_settings = QgsSettings()
    
    def _check_key(self, key: Union[SettingsKeys, str]) -> str:
        key = key.value if isinstance(key, (PluginSettingsKeys, QgsSettingsKeys)) else key
        if not isinstance(key, str):
            raise TypeError(f"Expected key of type 'str' or 'SettingsKeys', got {type(key)}")
        
        return key
    
    def contains(self, key: Optional[str], section: QgsSettings.Section = QgsSettings.Section.NoSection) -> bool:
        """Check if a key exists in the settings.

        Args:
            key (Optional[str]): The key to check for existence. If None, returns False.
            section (QgsSettings.Section, optional): The section to check in. Defaults to QgsSettings.Section.NoSection.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        if key is None:
            return False
        
        key = self._check_key(key)
        return self._qgs_settings.contains(key, section)
    
    def setValue(self, key: Optional[str], value: Any, section: QgsSettings.Section = QgsSettings.Section.NoSection) -> None:
        if key is None:
            return
        key = self._check_key(key)
        self._qgs_settings.setValue(key, value, section)
    
    def value(self, key: Optional[str], defaultValue: Any = None, type: Any = None, section: QgsSettings.Section = QgsSettings.Section.NoSection) -> Any:
        if key is None:
            return defaultValue
        key = self._check_key(key)
        if type:
            return self._qgs_settings.value(key, defaultValue, type, section)
        else:
            return self._qgs_settings.value(key, defaultValue, section=section)