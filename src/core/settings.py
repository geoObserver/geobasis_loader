from typing import Union
from qgis.core import QgsSettings
from .. import config


class PluginSettings:
    __slots__ = ("_qgs_settings",)
    
    def __init__(self):
        self._qgs_settings = QgsSettings()
    
    def _check_type(self, value, expected_type):
        if expected_type is not None and not isinstance(value, expected_type):
            raise TypeError(f"Expected value of type {expected_type}, got {type(value)}")
    
    @property
    def automatic_crs(self) -> bool:
        return self.get_value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, value_type=bool)
    
    @property
    def current_catalog(self) -> dict:
        return self.get_value(config.QgsSettingsKeys.CURRENT_CATALOG, {}, value_type=dict)
    
    @property
    def highlight_favorites(self) -> bool:
        return self.get_value(config.QgsSettingsKeys.DISPLAY_HIGHLIGHT_FAVORITES, False, value_type=bool)
    
    @property
    def current_server(self) -> int:
        return self.get_value(config.QgsSettingsKeys.SERVERS, 0, value_type=int)
    
    @property
    def show_gbl_panel(self) -> bool:
        return self.get_value(config.QgsSettingsKeys.SHOW_GBL_PANEL, False, value_type=bool)
    
    @automatic_crs.setter
    def automatic_crs(self, value: bool):
        self._check_type(value, bool)
        self.set_value(config.QgsSettingsKeys.AUTOMATIC_CRS, value)
    
    @current_catalog.setter
    def current_catalog(self, value: dict):
        self._check_type(value, dict)
        self.set_value(config.QgsSettingsKeys.CURRENT_CATALOG, value)
    
    @highlight_favorites.setter
    def highlight_favorites(self, value: bool):
        self._check_type(value, bool)
        self.set_value(config.QgsSettingsKeys.DISPLAY_HIGHLIGHT_FAVORITES, value)
    
    @current_server.setter
    def current_server(self, value: Union[int, config.ServerHosts]):
        if isinstance(value, int):
            value = config.ServerHosts(value)
        self.set_value(config.QgsSettingsKeys.SERVERS, value)
    
    @show_gbl_panel.setter
    def show_gbl_panel(self, value: bool):
        self._check_type(value, bool)
        self.set_value(config.QgsSettingsKeys.SHOW_GBL_PANEL, value)
    
    def get_value(self, key: Union[config.QgsSettingsKeys, str], default=None, value_type=None):
        key = key.value if isinstance(key, config.QgsSettingsKeys) else key
        return self._qgs_settings.value(key, default, type=value_type)

    def set_value(self, key: Union[config.QgsSettingsKeys, str], value):
        key = key.value if isinstance(key, config.QgsSettingsKeys) else key
        self._qgs_settings.setValue(key, value)
