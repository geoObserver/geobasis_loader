from enum import Enum


class CatalogEntryServiceType(str, Enum):
    WMS = "ogc_wms"
    WMTS = "ogc_wmts"
    WFS = "ogc_wfs"
    WCS = "ogc_wcs"
    APIF = "ogc_api_features"
    VECTORTILES = "ogc_vectortiles"
    ARCGIS_FEATURE_SERVER = "arcgis_featureserver"
    ARCGIS_MAP_SERVER = "arcgis_mapserver"
    WEB = "web"

class CustomLayerProperty(str, Enum):
    GBL_NAME = "gbl_name"
    GBL_ID = "gbl_id"
    GBL_PATH = "gbl_path"
    GBL_PARENT_ID = "gbl_parent_id"
    GBL_CRS = "gbl_crs"

class CatalogEntryType(str, Enum):
    TOPIC = "topic"
    TOPIC_GROUP = "group"
    TOPIC_COMBINATION = "combination"
