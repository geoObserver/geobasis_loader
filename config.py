from enum import Enum
import os
import pathlib
from qgis.core import QgsSettings, QgsApplication

PLUGIN_VERSION = '2.0.0'
PLUGIN_NAME = 'GeoBasis Loader'
PLUGIN_NAME_AND_VERSION = PLUGIN_NAME + ' (v' + PLUGIN_VERSION + ')'

PLUGIN_DIR = os.path.dirname(__file__)
REQUEST_TIMEOUT_MS = 30000
PLUGIN_LOGGER_NAME = "geobasis_loader"
LOGGING_SUCCESS_LEVEL = 25

CATALOG_OVERVIEW = "GeoBasis_Loader_v6_Kataloge.json"
CATALOG_OVERVIEW_NAME = "catalog_overview"
class ServerHosts(str, Enum):
    GEOOBSERVER = "https://geoobserver.de/download/GeoBasis_Loader/{name}"
    GITHUB = "https://api.github.com/repos/geoObserver/geobasis_loader/contents/kataloge/{name}?ref=main"
    
    @classmethod
    def get_all_servers(cls) -> list[str]:
        return [a.value for a in cls]
    
    @classmethod
    def get_enabled_servers(cls) -> list[str]:
        servers = []
        qgs_settings = QgsSettings()
        server_index = qgs_settings.value(QgsSettingsKeys.SERVERS, 0, type=int)
        if server_index == 0:
            servers = cls.get_all_servers()
        else:
            servers.append(cls.get_all_servers()[server_index - 1])
            
        return servers
    
class QgsSettingsKeys(str, Enum):
    CURRENT_CATALOG = 'geobasis_loader/current_catalog'
    AUTOMATIC_CRS = 'geobasis_loader/automatic_crs'
    SERVERS = 'geobasis_loader/servers'
    PROPERTY_FAVORITE = 'geobasis_loader/properties/favorite'
    PROPERTY_INVISIBLE = 'geobasis_loader/properties/invisible'
    PROPERTY_DISABLED = 'geobasis_loader/properties/disabled'

class QgsIcons:
    FAVORITES_STAR = QgsApplication.getThemeIcon("mIconFavorites.svg")
    
    TOPIC_GROUP_FOLDER = QgsApplication.getThemeIcon("mIconFolder.svg")
    TOPIC_GROUP_ADD = QgsApplication.getThemeIcon("mActionAddGroup.svg")
    TOPIC_COMBINATION_ICON = QgsApplication.getThemeIcon("mActionDataSourceManager.svg")
    
    WEB_ICON = QgsApplication.getThemeIcon("search.svg")
    
    WFS_ICON = QgsApplication.getThemeIcon("mIconWfs.svg")
    WMS_ICON = QgsApplication.getThemeIcon("mIconWms.svg")
    WCS_ICON = QgsApplication.getThemeIcon("mIconWcs.svg")
    VECTORTILES_ICON = QgsApplication.getThemeIcon("mIconVectorTileLayer.svg")
    ARCGIS_FEATURE_ICON = QgsApplication.getThemeIcon("mActionAddAfsLayer.svg")
    ARCGIS_MAP_ICON = QgsApplication.getThemeIcon("mActionAddAmsLayer.svg")