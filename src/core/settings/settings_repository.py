from qgis.PyQt.QtCore import QObject, pyqtSignal
from .settings_models import PluginSettingsKeys
from .settings_infrastructure import CustomQgsSettings


class PluginSettings(QObject):
    __slots__ = ("_qgs_settings",)
    automatic_crs_changed = pyqtSignal(bool)
    
    def __init__(self):
        self._qgs_settings = CustomQgsSettings()
    
    def _check_type(self, value, expected_type):
        if expected_type is not None and not isinstance(value, expected_type):
            raise TypeError(f"Expected value of type {expected_type}, got {type(value)}")
    
    @property
    def automatic_crs(self) -> bool:
        return self._qgs_settings.value(PluginSettingsKeys.AUTOMATIC_CRS, False, type=bool)
    
    @property
    def current_catalog(self) -> str:
        return self._qgs_settings.value(PluginSettingsKeys.CURRENT_CATALOG, "", type=str)
    
    @property
    def highlight_favorites(self) -> bool:
        return self._qgs_settings.value(PluginSettingsKeys.DISPLAY_HIGHLIGHT_FAVORITES, False, type=bool)
    
    @property
    def current_server(self) -> int:
        return self._qgs_settings.value(PluginSettingsKeys.SERVERS, 0, type=int)
    
    @property
    def show_gbl_panel(self) -> bool:
        return self._qgs_settings.value(PluginSettingsKeys.SHOW_GBL_PANEL, False, type=bool)
    
    @automatic_crs.setter
    def automatic_crs(self, value: bool):
        self._check_type(value, bool)
        self._qgs_settings.setValue(PluginSettingsKeys.AUTOMATIC_CRS, value)
        self.automatic_crs_changed.emit(value)
    
    @current_catalog.setter
    def current_catalog(self, value: str):
        self._check_type(value, str)
        self._qgs_settings.setValue(PluginSettingsKeys.CURRENT_CATALOG, value)
    
    @highlight_favorites.setter
    def highlight_favorites(self, value: bool):
        self._check_type(value, bool)
        self._qgs_settings.setValue(PluginSettingsKeys.DISPLAY_HIGHLIGHT_FAVORITES, value)
    
    @current_server.setter
    def current_server(self, value: int):
        # FIXME
        self._check_type(value, int)
        if value < 0 or value > 2:
            raise ValueError(f"Invalid server index: {value}")
        self._qgs_settings.setValue(PluginSettingsKeys.SERVERS, value)
    
    @show_gbl_panel.setter
    def show_gbl_panel(self, value: bool):
        self._check_type(value, bool)
        self._qgs_settings.setValue(PluginSettingsKeys.SHOW_GBL_PANEL, value)
