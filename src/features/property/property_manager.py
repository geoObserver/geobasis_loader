"""Manage persistent properties for catalog entries.

The module stores and retrieves per-entry flags (favorite, visible,
enabled) via QGIS settings and exposes a proxy object for attribute-style
access.
"""

from contextlib import contextmanager
from typing import Optional
from qgis.PyQt.QtCore import QObject, pyqtSignal
from .property_repository import PropertyRepository
from .property_models import Properties
from . import property_infrastructure
from ...core.settings import PluginSettingsKeys
from ...core.settings.settings_infrastructure import CustomQgsSettings
from ...core.utils import signal_utils
from ...core import config
from ...core.utils import custom_logger

logger = custom_logger.get_logger(__name__)


class PropertyManager(QObject):
    """Manage property state and persistence for all entries."""
    enabled_changed = pyqtSignal(dict)
    favorite_changed = pyqtSignal(dict)
    visibility_changed = pyqtSignal(dict)
    
    def __init__(self, property_repository: Optional[PropertyRepository] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.property_repository = property_repository or PropertyRepository()
        self._qgs_settings = CustomQgsSettings()
        self._update_depth = 0
        self._pending_changes: dict[str, dict[str, bool]] = {}
    
    def __getitem__(self, id: str) -> Properties:
        """Return a properties proxy for an entry key.

        Args:
            id: Unique id of the entry.

        Returns:
            A Properties proxy bound to key.
        """
        return self.property_repository[id]
    
    def get_properties(self, id: str) -> Properties:
        """Return a properties proxy for an entry key.

        Args:
            id: Unique catalog path/key of the entry.

        Returns:
            A Properties proxy bound to key.
        """
        return self.property_repository.get_properties(id)

    def dispose(self) -> None:
        signal_utils.disconnect_all_signals(self)
        self.deleteLater()
    
    @contextmanager
    def batch_update(self):
        """Context manager for batch updates.

        This context manager allows for multiple property changes to be made
        without triggering signals for each individual change. Instead, a single
        signal is emitted after all changes are made.

        Usage:
            with property_manager.batch_update() as pm:
                pm.set_favorite("entry1", True)
                pm.set_visibility("entry2", False)

        Signals:
            enabled_changed: Emitted after all changes are made, with a dict of
                             changed enabled states.
            favorite_changed: Emitted after all changes are made, with a dict of
                              changed favorite states.
            visibility_changed: Emitted after all changes are made, with a dict of
                                changed visibility states.
        """
        self._update_depth += 1
        try:
            yield self
        finally:
            self._update_depth -= 1
            if self._update_depth == 0 and self._pending_changes:
                # TODO: Check whether this works or not
                print(f"Batch update completed. Pending changes: {self._pending_changes}")
                enabled_changes = self._pending_changes.get("enabled", {}).copy()
                favorite_changes = self._pending_changes.get("favorite", {}).copy()
                visibility_changes = self._pending_changes.get("visibility", {}).copy()
                self._pending_changes.clear()
                
                if enabled_changes:
                    self.save_property(PluginSettingsKeys.PROPERTY_DISABLED)
                    self.enabled_changed.emit(enabled_changes)
                if favorite_changes:
                    self.save_property(PluginSettingsKeys.PROPERTY_FAVORITE)
                    self.favorite_changed.emit(favorite_changes)
                if visibility_changes:
                    self.save_property(PluginSettingsKeys.PROPERTY_INVISIBLE)
                    self.visibility_changed.emit(visibility_changes)
    
    def set_favorite(self, id: str, favorite: bool):
        """Set favorite flag for an entry.

        Args:
            id: Unique id of the entry.
            favorite: New favorite state.
            save_change: Whether to persist this change immediately.
        """
        self.property_repository.set_favorite(id, favorite)
            
        if not self._update_depth > 0:
            self.save_property(PluginSettingsKeys.PROPERTY_FAVORITE)
            self.favorite_changed.emit({id: favorite})
        else:
            self._pending_changes.setdefault("favorite", {})[id] = favorite

    def set_visibility(self, id: str, visible: bool):
        """Set visibility flag for an entry.

        Internally, invisible keys are stored for compact default-true logic.

        Args:
            id: Unique id of the entry.
            visible: New visibility state.
            save_change: Whether to persist this change immediately.
        """
        self.property_repository.set_visibility(id, visible)
            
        if not self._update_depth > 0:
            self.save_property(PluginSettingsKeys.PROPERTY_INVISIBLE)
            self.visibility_changed.emit({id: visible})
        else:
            self._pending_changes.setdefault("visibility", {})[id] = visible

    def set_enabled(self, id: str, enabled: bool):
        """Set enabled flag for an entry.

        Internally, disabled keys are stored for compact default-true logic.

        Args:
            id: Unique id of the entry.
            enabled: New enabled state.
            save_change: Whether to persist this change immediately.
        """
        self.property_repository.set_enabled(id, enabled)
            
        if not self._update_depth > 0:
            self.save_property(PluginSettingsKeys.PROPERTY_DISABLED)
            self.enabled_changed.emit({id: enabled})
        else:
            self._pending_changes.setdefault("enabled", {})[id] = enabled
    
    def is_favorite(self, id: str) -> bool:
        """Return favorite state for an entry.

        Args:
            id: Unique id of the entry.

        Returns:
            True if favorite, else False.
        """
        return self.property_repository.is_favorite(id)
    
    def is_visible(self, id: str) -> bool:
        """Return visibility state for an entry.

        Args:
            id: Unique id of the entry.

        Returns:
            True if visible, else False.
        """
        return self.property_repository.is_visible(id)

    def is_enabled(self, id: str) -> bool:
        """Return enabled state for an entry.

        Args:
            id: Unique id of the entry.

        Returns:
            True if enabled, else False.
        """
        return self.property_repository.is_enabled(id)
    
    def get_favorites(self) -> frozenset[str]:
        """Return a set of all favorite entry keys."""
        return frozenset(self.property_repository._favorite)
    
    def load_property(self, property: PluginSettingsKeys) -> None:
        values = property_infrastructure.load(property, self._qgs_settings)
        if property == PluginSettingsKeys.PROPERTY_FAVORITE:
            self.property_repository.load_favorites(set(values))
        elif property == PluginSettingsKeys.PROPERTY_INVISIBLE:
            self.property_repository.load_invisible(set(values))
        elif property == PluginSettingsKeys.PROPERTY_DISABLED:
            self.property_repository.load_disabled(set(values))
        else:
            raise ValueError(f"Can't load '{property}': Unknown property")
        
    def load_all(self):
        """Load all property buckets from QgsSettings.

        If modern keys do not exist yet, this method tries to migrate legacy
        settings from catalogs/settings.json and then persists the migrated
        state in the slightly less old path format.
        """

        if not self._qgs_settings.contains(PluginSettingsKeys.PROPERTY_FAVORITE):
            path = config.PLUGIN_DIR / "catalogs" / "settings.json"
            if not path.exists():
                logger.warning(f"Alte Konfiguration nicht gefunden: {path}. Keine Eigenschaften geladen.")
                return
            
            try:
                is_enabled, is_visible = property_infrastructure.convert_old_properties(path)
            except Exception as e:
                logger.error(f"Error occurred while converting old properties: {type(e).__name__}, {e}")
                return
            
            new_invisible = set()
            new_disabled = set()
            
            for key, value in is_visible:
                new_invisible.add(key) if not value else None
            
            for key, value in is_enabled:
                new_disabled.add(key) if not value else None
            
            self.property_repository.load_invisible(new_invisible)
            self.property_repository.load_disabled(new_disabled)
            
            self.save_all()
            return
        
        self.load_property(PluginSettingsKeys.PROPERTY_FAVORITE)
        self.load_property(PluginSettingsKeys.PROPERTY_INVISIBLE)
        self.load_property(PluginSettingsKeys.PROPERTY_DISABLED)
    
    def save_property(self, property: PluginSettingsKeys) -> None:
        if property == PluginSettingsKeys.PROPERTY_FAVORITE:
            values = list(self.property_repository._favorite)
        elif property == PluginSettingsKeys.PROPERTY_INVISIBLE:
            values = list(self.property_repository._invisible)
        elif property == PluginSettingsKeys.PROPERTY_DISABLED:
            values = list(self.property_repository._disabled)
        else:
            raise ValueError(f"Can't save '{property}': Unknown property")
        
        property_infrastructure.save(property, values, self._qgs_settings)

    def save_all(self):
        """Persist all properties to QgsSettings in one call."""

        self.save_property(PluginSettingsKeys.PROPERTY_FAVORITE)
        self.save_property(PluginSettingsKeys.PROPERTY_INVISIBLE)
        self.save_property(PluginSettingsKeys.PROPERTY_DISABLED)

    # def contains_old_paths(self) -> bool:
    #     combined = self._favorite.union(self._invisible).union(self._disabled)
    #     for value in combined:
    #         if "/" in value:
    #             return True
    #     return False
