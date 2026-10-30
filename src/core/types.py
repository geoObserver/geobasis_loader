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
    GBL_CRS = "gbl_crs"
