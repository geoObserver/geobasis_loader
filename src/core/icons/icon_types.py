from enum import Enum
from ..types import CatalogEntryServiceType


class IconKey(str, Enum):
    FAVORITE_STAR = "favorite_star"
    PRESET_USER = "preset_user"
    SETTINGS = "settings"
    SPATIAL_BOOKMARK = "spatial_bookmark"
    SPATIAL_BOOKMARK_NEW = "spatial_bookmark_new"
    SPATIAL_BOOKMARK_ZOOM = "spatial_bookmark_zoom"
    DELETE = "delete"
    FOLDER_CLOSED = "folder_closed"
    FOLDER_OPEN = "folder_open"
    GROUP_ADD = "group_add"
    COMBINATION_ADD = "combination_add"
    REFRESH_ARROWS = "refresh_arrows"
    ADD_PLUS = "add_plus"
    REMOVE_MINUS = "remove_minus"
    
    # Own resources
    CATALOG_GLOBE_ICON = "catalog_globe"
    BULB_ON_ICON = "bulb_on"
    BULB_OFF_ICON = "bulb_off"
    TOOLBAR_MAIN_MENU_ICON = "toolbar_main_menu"
    TOOLBAR_GBL_PANEL_ICON = "toolbar_gbl_panel"

# QGIS icons start with "/" while Plugin icons/images/resources start without "/"
ICON_PATHS: dict[IconKey, str] = {
    IconKey.FAVORITE_STAR: "/mIconFavorites.svg",
    IconKey.PRESET_USER: "/user.svg",
    IconKey.SETTINGS: "/console/iconSettingsConsole.svg",
    IconKey.SPATIAL_BOOKMARK: "/mItemBookmark.svg",
    IconKey.SPATIAL_BOOKMARK_NEW: "/mActionNewBookmark.svg",
    IconKey.SPATIAL_BOOKMARK_ZOOM: "/mActionZoomToBookmark.svg",
    IconKey.DELETE: "/mActionDeleteSelected.svg",
    IconKey.FOLDER_CLOSED: "/mIconFolder.svg",
    IconKey.FOLDER_OPEN: "/mIconFolderOpen.svg",
    IconKey.GROUP_ADD: "/mActionAddGroup.svg",
    IconKey.COMBINATION_ADD: "/mActionDataSourceManager.svg",
    IconKey.REFRESH_ARROWS: "/mActionRefresh.svg",
    IconKey.ADD_PLUS: "/symbologyAdd.svg",
    IconKey.REMOVE_MINUS: "/symbologyRemove.svg",
    
    IconKey.CATALOG_GLOBE_ICON: "globe.svg",
    IconKey.BULB_ON_ICON: "bulb_on.svg",
    IconKey.BULB_OFF_ICON: "bulb_off.svg",
    IconKey.TOOLBAR_MAIN_MENU_ICON: "GeoBasis_Loader_Main_Icon.svg",
    IconKey.TOOLBAR_GBL_PANEL_ICON: "GeoBasis_Loader_Catalog_Icon.svg"
}

LAYER_TYPE_ICON_PATHS: dict[CatalogEntryServiceType, str] = {
    CatalogEntryServiceType.WMS: "/mIconWms.svg",
    CatalogEntryServiceType.WMTS: "/mIconWms.svg",
    CatalogEntryServiceType.WCS: "/mIconWcs.svg",
    CatalogEntryServiceType.WFS: "/mIconWfs.svg",
    CatalogEntryServiceType.APIF: "/mIconWfs.svg",
    CatalogEntryServiceType.VECTORTILES: "/mIconVectorTileLayer.svg",
    CatalogEntryServiceType.ARCGIS_FEATURE_SERVER: "/mActionAddAfsLayer.svg",
    CatalogEntryServiceType.ARCGIS_MAP_SERVER: "/mActionAddAmsLayer.svg",
    CatalogEntryServiceType.WEB: "/search.svg"
}
