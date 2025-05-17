import os

PLUGIN_VERSION = '1.2'
PLUGIN_NAME = 'GeoBasis Loader'
PLUGIN_NAME_AND_VERSION = PLUGIN_NAME + ' (v' + PLUGIN_VERSION + ')'
MY_CRITICAL_1 = 'Layerladefehler '
MY_CRITICAL_2 = ', Dienst nicht verfügbar (URL?)'
MY_INFO_1 = 'Layer '
MY_INFO_2 = ' erfolgreich geladen.'

PLUGIN_DIR = os.path.dirname(__file__)
CURRENT_CATALOG_SETTINGS_KEY = 'geobasis_loader/current_catalog'
AUTOMATIC_CRS_SETTINGS_KEY = 'geobasis_loader/automatic_crs'

CATALOG_OVERVIEW = "https://geoobserver.de/download/GeoBasis_Loader/GeoBasis_Loader_v4_Kataloge.json"
CATALOG_OVERVIEW_NAME = "catalog_overview"