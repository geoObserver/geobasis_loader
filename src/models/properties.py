"""Property models for catalog entries.

Keeps the Properties proxy in models to avoid service import cycles.
"""

class Properties:
    """Proxy object for a single entry's properties."""

    def __init__(self, key: str) -> None:
        if not isinstance(key, str):
            raise ValueError("Key is not a string")
        self._key = key

    @property
    def favorite(self) -> bool:
        from ..services import registry
        return registry.property_manager.is_favorite(self._key)

    @favorite.setter
    def favorite(self, value) -> None:
        if not isinstance(value, bool):
            raise ValueError("Object is not a boolean")
        from ..services import registry
        registry.property_manager.set_favorite(self._key, value, True)

    @property
    def visible(self) -> bool:
        from ..services import registry
        return registry.property_manager.is_visible(self._key)

    @visible.setter
    def visible(self, value) -> None:
        if not isinstance(value, bool):
            raise ValueError("Object is not a boolean")
        from ..services import registry
        registry.property_manager.set_visibility(self._key, value, True)

    @property
    def enabled(self) -> bool:
        from ..services import registry
        return registry.property_manager.is_enabled(self._key)

    @enabled.setter
    def enabled(self, value) -> None:
        if not isinstance(value, bool):
            raise ValueError("Object is not a boolean")
        from ..services import registry
        registry.property_manager.set_enabled(self._key, value, True)
