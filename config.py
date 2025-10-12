from enum import Enum
import os
from qgis.core import QgsSettings

PLUGIN_VERSION = '1.4'
PLUGIN_NAME = 'GeoBasis Loader'
PLUGIN_NAME_AND_VERSION = PLUGIN_NAME + ' (v' + PLUGIN_VERSION + ')'
MY_CRITICAL_1 = 'Layerladefehler '
MY_CRITICAL_2 = ', Dienst nicht verfügbar (URL?)'
MY_INFO_1 = 'Layer '
MY_INFO_2 = ' erfolgreich geladen.'

PLUGIN_DIR = os.path.dirname(__file__)
CURRENT_CATALOG_SETTINGS_KEY = 'geobasis_loader/current_catalog'
AUTOMATIC_CRS_SETTINGS_KEY = 'geobasis_loader/automatic_crs'
SERVERS_SETTINGS_KEY = 'geobasis_loader/servers'

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
        server_index = qgs_settings.value(SERVERS_SETTINGS_KEY, 0, type=int)
        if server_index == 0:
            servers = cls.get_all_servers()
        else:
            servers.append(cls.get_all_servers()[server_index - 1])
            
        return servers
    
class InternalProperties(str, Enum):
    VISIBILITY = "__visible__"
    LOADING = "__loading__"
    PATH = "__path__"
    
    @classmethod
    def get_properties(cls) -> list["InternalProperties"]:
        return [a for a in cls if a != cls.PATH]