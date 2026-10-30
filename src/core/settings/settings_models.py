from enum import Enum
from typing import Union
from ..config import PLUGIN_NAME


class PluginSettingsKeys(str, Enum):
    AUTOMATIC_CRS = 'automatic_crs'
    CURRENT_CATALOG = 'current_catalog'
    DISPLAY_HIGHLIGHT_FAVORITES = 'display_highlight_favorites'
    SERVERS = 'servers'
    SHOW_GBL_PANEL = 'show_gbl_panel'
    PROPERTY_FAVORITE = 'properties/favorite'
    PROPERTY_INVISIBLE = 'properties/invisible'
    PROPERTY_DISABLED = 'properties/disabled'
    
    def __new__(cls, value):
        obj = str.__new__(cls, value)
        obj._value_ = PLUGIN_NAME + '/' + value
        return obj

class QgsSettingsKeys(str, Enum):
    pass

SettingsKeys = Union[PluginSettingsKeys, QgsSettingsKeys]
