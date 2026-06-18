"""Service registry with lazy accessors for singletons."""

class Registry:
    @property
    def catalog_manager(self):
        from .catalog_service import singleton
        return singleton

    @property
    def preset_manager(self):
        from .preset_service import singleton
        return singleton

    @property
    def property_manager(self):
        from .property_service import singleton
        return singleton
