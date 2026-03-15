import pathlib, json
from enum import Enum
from qgis.core import QgsSettings
from . import config
from . import custom_logger

logger = custom_logger.get_logger(__file__)

class PropertyManager:
    class Property(str, Enum):
        INIT = "init"
        FAVORITE = "favorite"
        VISIBLE = "visible"
        ENABLED = "enabled"
    
    def __init__(self):
        self._init: set[str] = set()
        self._favorite: set[str] = set()
        self._invisible: set[str] = set()
        self._disabled: set[str] = set()
        self.load()
    
    def __getitem__(self, key):       
        data = {
            self.Property.INIT:     self.is_init(key),
            self.Property.FAVORITE: self.is_favorite(key),
            self.Property.VISIBLE:  self.is_visible(key),
            self.Property.ENABLED:  self.is_enabled(key)
        }
        
        return data
    
    def set_initialisation(self, key: str, init: bool):
        if init:
            self._init.add(key)
        else:
            self._init.discard(key)
    
    def set_favorite(self, key: str, favorite: bool):
        if favorite:
            self._favorite.add(key)
        else:
            self._favorite.discard(key)
    
    def set_visibility(self, key: str, visible: bool):
        if not visible:
            self._invisible.add(key)
        else:
            self._invisible.discard(key)
    
    def set_enabled(self, key: str, enabled: bool):
        if not enabled:
            self._disabled.add(key)
        else:
            self._disabled.discard(key)
    
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
    
    def load(self):
        qgs_settings = QgsSettings()
        if not qgs_settings.contains(config.QgsSettingsKeys.PROPERTY_INIT):
            path = pathlib.Path(config.PLUGIN_DIR) / "catalogs" / "settings.json"
            self._convert_old_properties(path)
            self.save()
            return
        
        self._init: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_INIT, list(), type=list))
        self._favorite: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_FAVORITE, list(), type=list))
        self._invisible: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_INVISIBLE, list(), type=list))
        self._disabled: set[str] = set(qgs_settings.value(config.QgsSettingsKeys.PROPERTY_DISABLED, list(), type=list))
    
    def save(self):
        qgs_settings = QgsSettings()
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_INIT, list(self._init))
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_FAVORITE, list(self._favorite))
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_INVISIBLE, list(self._invisible))
        qgs_settings.setValue(config.QgsSettingsKeys.PROPERTY_DISABLED, list(self._disabled))

singleton = PropertyManager()