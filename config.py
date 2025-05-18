from enum import Enum
import os

PLUGIN_VERSION = '1.3'
PLUGIN_NAME = 'GeoBasis Loader'
PLUGIN_NAME_AND_VERSION = PLUGIN_NAME + ' (v' + PLUGIN_VERSION + ')'
MY_CRITICAL_1 = 'Layerladefehler '
MY_CRITICAL_2 = ', Dienst nicht verfügbar (URL?)'
MY_INFO_1 = 'Layer '
MY_INFO_2 = ' erfolgreich geladen.'

PLUGIN_DIR = os.path.dirname(__file__)
CURRENT_CATALOG_SETTINGS_KEY = 'geobasis_loader/current_catalog'
AUTOMATIC_CRS_SETTINGS_KEY = 'geobasis_loader/automatic_crs'

CATALOG_OVERVIEW = "GeoBasis_Loader_v5_Kataloge.json"
CATALOG_OVERVIEW_NAME = "catalog_overview"
class ServerHosts(str, Enum):
    GITHUB = "https://api.github.com/repos/geoObserver/geobasis_loader/contents/kataloge/{name}?ref=two-servers"
    GEOOBSERVER = "https://geoobserver.de/download/GeoBasis_Loader/{name}"
    
    @classmethod
    def get_servers(cls) -> list[str]:
        return [a.value for a in cls]