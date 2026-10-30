from typing import Optional
from .property_models import Properties


class PropertyRepository:
    """Repository for managing property data."""

    def __init__(self, 
            init_favorite: Optional[set[str]] = None, 
            init_invisible: Optional[set[str]] = None,
            init_disabled: Optional[set[str]] = None, 
        ):
        self._favorite: set[str] = set(init_favorite) if init_favorite is not None else set()
        self._invisible: set[str] = set(init_invisible) if init_invisible is not None else set()
        self._disabled: set[str] = set(init_disabled) if init_disabled is not None else set()
    
    def __getitem__(self, id: str) -> Properties:
        """Return a properties proxy for an entry key.

        Args:
            id: Unique id of the entry.

        Returns:
            A Properties proxy bound to key.
        """
        return Properties(
            enabled=self.is_enabled(id),
            favorite=self.is_favorite(id),
            visible=self.is_visible(id)
        )
    
    def get_properties(self, id: str) -> Properties:
        """Return a properties proxy for an entry key.

        Args:
            id: Unique catalog path/key of the entry.

        Returns:
            A Properties proxy bound to key.
        """
        return self[id]
        
    def is_favorite(self, id: str) -> bool:
        """Return favorite state for an entry.

        Args:
            id: Unique id of the entry.

        Returns:
            True if favorite, else False.
        """
        return id in self._favorite
    
    def is_visible(self, id: str) -> bool:
        """Return visibility state for an entry.

        Args:
            id: Unique id of the entry.

        Returns:
            True if visible, else False.
        """
        return id not in self._invisible
    
    def is_enabled(self, id: str) -> bool:
        """Return enabled state for an entry.

        Args:
            id: Unique id of the entry.

        Returns:
            True if enabled, else False.
        """
        return id not in self._disabled
    
    def set_favorite(self, id: str, favorite: bool):
        """Set favorite flag for an entry.

        Args:
            id: Unique id of the entry.
            favorite: New favorite state.
            save_change: Whether to persist this change immediately.
        """
        if favorite:
            self._favorite.add(id)
        else:
            self._favorite.discard(id)
    
    def set_visibility(self, id: str, visible: bool):
        """Set visibility flag for an entry.

        Internally, invisible keys are stored for compact default-true logic.

        Args:
            id: Unique id of the entry.
            visible: New visibility state.
            save_change: Whether to persist this change immediately.
        """
        if not visible:
            self._invisible.add(id)
        else:
            self._invisible.discard(id)
    
    def set_enabled(self, id: str, enabled: bool):
        """Set enabled flag for an entry.

        Internally, disabled keys are stored for compact default-true logic.

        Args:
            id: Unique id of the entry.
            enabled: New enabled state.
            save_change: Whether to persist this change immediately.
        """
        if not enabled:
            self._disabled.add(id)
        else:
            self._disabled.discard(id)

    def load_favorites(self, favorites: set[str]) -> None:
        """Load favorite entries from a set.

        Args:
            favorites: Set of favorite entry keys.
        """
        self._favorite.clear() 
        self._favorite.update(favorites)
    
    def load_invisible(self, invisible: set[str]) -> None:
        """Load invisible entries from a set.

        Args:
            invisible: Set of invisible entry keys.
        """
        self._invisible.clear() 
        self._invisible.update(invisible)

    def load_disabled(self, disabled: set[str]) -> None:
        """Load disabled entries from a set.

        Args:
            disabled: Set of disabled entry keys.
        """
        self._disabled.clear() 
        self._disabled.update(disabled)