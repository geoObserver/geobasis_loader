import pathlib, json
from qgis.core import QgsSettings
from . import config
from . import custom_logger

logger = custom_logger.get_logger(__file__)

class Properties:   
    def __init__(self, key: str) -> None:
        self._key = key
    
    @property
    def init(self) -> bool:
        return singleton.is_init(self._key)
    
    @init.setter
    def init(self, value) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"Object isn't a boolean")
        singleton.set_initialisation(self._key, value)
    
    @property
    def favorite(self) -> bool:
        return singleton.is_favorite(self._key)
    
    @favorite.setter
    def favorite(self, value) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"Object isn't a boolean")
        singleton.set_favorite(self._key, value)
    
    @property
    def visible(self) -> bool:
        return singleton.is_visible(self._key)
    
    @visible.setter
    def visible(self, value) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"Object isn't a boolean")
        singleton.set_visibility(self._key, value)
    
    @property
    def enabled(self) -> bool:
        return singleton.is_enabled(self._key)
    
    @enabled.setter
    def enabled(self, value) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"Object isn't a boolean")
        singleton.set_enabled(self._key, value)
    
class PropertyManager:
    def __init__(self):
        self._init: set[str] = set()
        self._favorite: set[str] = set()
        self._invisible: set[str] = set()
        self._disabled: set[str] = set()
        self.load_all()
    
    def __getitem__(self, key: str) -> Properties:
        return Properties(key)
    
    def get_properties(self, key: str) -> Properties:
        return self[key]
    
    def set_initialisation(self, key: str, init: bool, save_change: bool = False):
        if init:
            self._init.add(key)
        else:
            self._init.discard(key)
        
        if save_change:
            self.save(config.QgsSettingsKeys.PROPERTY_INIT)
    
    def set_favorite(self, key: str, favorite: bool, save_change: bool = False):
        if favorite:
            self._favorite.add(key)
        else:
            self._favorite.discard(key)
            
        if save_change:
            self.save(config.QgsSettingsKeys.PROPERTY_FAVORITE)
    
    def set_visibility(self, key: str, visible: bool, save_change: bool = False):
        if not visible:
            self._invisible.add(key)
        else:
            self._invisible.discard(key)
            
        if save_change:
            self.save(config.QgsSettingsKeys.PROPERTY_INVISIBLE)
    
    def set_enabled(self, key: str, enabled: bool, save_change: bool = False):
        if not enabled:
            self._disabled.add(key)
        else:
            self._disabled.discard(key)
            
        if save_change:
            self.save(config.QgsSettingsKeys.PROPERTY_DISABLED)
    
    def is_init(self, key: str) -> bool:
        return key in self._init
    
    def is_favorite(self, key: str) -> bool:
        return key in self._favorite
    
    def is_visible(self, key: str) -> bool:
        return key not in self._invisible
    
    def is_enabled(self, key: str) -> bool:
        return key not in self._disabled
    
    def _convert_old_properties(self, path: pathlib.Path):
        if not path.exists():
            logger.info(f"Alte Konfigurationsdatei nicht gefunden. Werkseinstellungen wiederhergestellt")
            return
        
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            properties = data["properties"]
            
            visible = properties["__visible__"]
            for key, value in visible.items():
                self.set_visibility(key, value)
                
            enabled = properties["__loading__"]
            for key, value in enabled.items():
                self.set_enabled(key, value)
    
    def save(self, property_key: config.QgsSettingsKeys) -> None:
        if property_key == config.QgsSettingsKeys.PROPERTY_INIT:
            property_value = self._init
        elif property_key == config.QgsSettingsKeys.PROPERTY_FAVORITE:
            property_value = self._favorite
        elif property_key == config.QgsSettingsKeys.PROPERTY_INVISIBLE:
            property_value = self._invisible
        elif property_key == config.QgsSettingsKeys.PROPERTY_DISABLED:
            property_value = self._disabled
        else:
            raise ValueError(f"Can't save '{property_key}': Unknown property")
        
        qgs_settings = QgsSettings()
        qgs_settings.setValue(property_key, list(property_value))
    
    def load_all(self):
        qgs_settings = QgsSettings()
        if not qgs_settings.contains(config.QgsSettingsKeys.PROPERTY_INIT):
            path = pathlib.Path(config.PLUGIN_DIR) / "catalogs" / "settings.json"
            self._convert_old_properties(path)
            self.save_all()
            return
        
        self._init: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_INIT, list(), type=list))
        self._favorite: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_FAVORITE, list(), type=list))
        self._invisible: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_INVISIBLE, list(), type=list))
        self._disabled: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_DISABLED, list(), type=list))
    
    def save_all(self):
        qgs_settings = QgsSettings()
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_INIT, list(self._init))
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_FAVORITE, list(self._favorite))
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_INVISIBLE, list(self._invisible))
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_DISABLED, list(self._disabled))

singleton = PropertyManager()