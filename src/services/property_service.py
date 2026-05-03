"""Manage persistent properties for catalog entries.

The module stores and retrieves per-entry flags (favorite, visible,
enabled) via QGIS settings and exposes a proxy object for attribute-style
access.
"""

import pathlib
import json
from qgis.core import QgsSettings
from .. import config
from ..utils import custom_logger
from ..models.properties import Properties

logger = custom_logger.get_logger(__file__)

class PropertyManager:
    """Manage property state and persistence for all entries."""

    def __init__(self):
        """Initialize in-memory sets and load persisted values."""
        self._favorite: set[str] = set()
        self._invisible: set[str] = set()
        self._disabled: set[str] = set()
        self._qgs_settings = QgsSettings()
    
    def __getitem__(self, key: str) -> Properties:
        """Return a properties proxy for an entry key.

        Args:
            key: Unique catalog path/key of the entry.

        Returns:
            A Properties proxy bound to key.
        """
        return Properties(key)
    
    def get_properties(self, key: str) -> Properties:
        """Return a properties proxy for an entry key.

        Args:
            key: Unique catalog path/key of the entry.

        Returns:
            A Properties proxy bound to key.
        """
        return self[key]
    
    def set_favorite(self, key: str, favorite: bool, save_change: bool = False):
        """Set favorite flag for an entry.

        Args:
            key: Unique catalog path/key of the entry.
            favorite: New favorite state.
            save_change: Whether to persist this change immediately.
        """
        if favorite:
            self._favorite.add(key)
        else:
            self._favorite.discard(key)
            
        if save_change:
            self.save(config.QgsSettingsKeys.PROPERTY_FAVORITE)
    
    def set_visibility(self, key: str, visible: bool, save_change: bool = False):
        """Set visibility flag for an entry.

        Internally, invisible keys are stored for compact default-true logic.

        Args:
            key: Unique catalog path/key of the entry.
            visible: New visibility state.
            save_change: Whether to persist this change immediately.
        """
        if not visible:
            self._invisible.add(key)
        else:
            self._invisible.discard(key)
            
        if save_change:
            self.save(config.QgsSettingsKeys.PROPERTY_INVISIBLE)
    
    def set_enabled(self, key: str, enabled: bool, save_change: bool = False):
        """Set enabled flag for an entry.

        Internally, disabled keys are stored for compact default-true logic.

        Args:
            key: Unique catalog path/key of the entry.
            enabled: New enabled state.
            save_change: Whether to persist this change immediately.
        """
        if not enabled:
            self._disabled.add(key)
        else:
            self._disabled.discard(key)
            
        if save_change:
            self.save(config.QgsSettingsKeys.PROPERTY_DISABLED)
    
    def is_favorite(self, key: str) -> bool:
        """Return favorite state for an entry.

        Args:
            key: Unique catalog path/key of the entry.

        Returns:
            True if favorite, else False.
        """
        return key in self._favorite
    
    def is_visible(self, key: str) -> bool:
        """Return visibility state for an entry.

        Args:
            key: Unique catalog path/key of the entry.

        Returns:
            True if visible, else False.
        """
        return key not in self._invisible
    
    def is_enabled(self, key: str) -> bool:
        """Return enabled state for an entry.

        Args:
            key: Unique catalog path/key of the entry.

        Returns:
            True if enabled, else False.
        """
        return key not in self._disabled
    
    def get_favorites(self) -> set[str]:
        """Return a set of all favorite entry keys."""
        return self._favorite
    
    def _convert_old_properties(self, path: pathlib.Path):
        """Migrate legacy JSON settings into current QgsSettings sets.

        Args:
            path: Path to the legacy settings JSON file.
        """
        if not path.exists():
            logger.info(f"Alte Konfigurationsdatei nicht gefunden. Werkseinstellungen wiederhergestellt")
            return
        
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            properties = data.get("properties", {})
            
            visible = properties.get("__visible__", {})
            for key, value in visible.items():
                self.set_visibility(key, value)
                
            enabled = properties.get("__loading__", {})
            for key, value in enabled.items():
                self.set_enabled(key, value)
    
    def save(self, property_key: config.QgsSettingsKeys) -> None:
        """Persist one property to QgsSettings.

        Args:
            property_key: Settings key of the property to persist.

        Raises:
            ValueError: If property_key is unknown.
        """
        
        if property_key == config.QgsSettingsKeys.PROPERTY_FAVORITE:
            property_value = self._favorite
        elif property_key == config.QgsSettingsKeys.PROPERTY_INVISIBLE:
            property_value = self._invisible
        elif property_key == config.QgsSettingsKeys.PROPERTY_DISABLED:
            property_value = self._disabled
        else:
            raise ValueError(f"Can't save '{property_key}': Unknown property")
        
        self._qgs_settings.setValue(property_key, list(property_value))
    
    def load_all(self):
        """Load all property buckets from QgsSettings.

        If modern keys do not exist yet, this method tries to migrate legacy
        settings from catalogs/settings.json and then persists the migrated
        state in the new format.
        """

        if not self._qgs_settings.contains(config.QgsSettingsKeys.PROPERTY_FAVORITE):
            path = pathlib.Path(config.PLUGIN_DIR) / "catalogs" / "settings.json"
            self._convert_old_properties(path)
            self.save_all()
            return
        
        self._favorite: set[str] = set(self._qgs_settings.value(config.QgsSettingsKeys.PROPERTY_FAVORITE, list(), type=list))
        self._invisible: set[str] = set(self._qgs_settings.value(config.QgsSettingsKeys.PROPERTY_INVISIBLE, list(), type=list))
        self._disabled: set[str] = set(self._qgs_settings.value(config.QgsSettingsKeys.PROPERTY_DISABLED, list(), type=list))
    
    def save_all(self):
        """Persist all properties to QgsSettings in one call."""

        self._qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_FAVORITE, list(self._favorite))
        self._qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_INVISIBLE, list(self._invisible))
        self._qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_DISABLED, list(self._disabled))

singleton = PropertyManager()