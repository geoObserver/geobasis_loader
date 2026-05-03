from enum import Enum
from typing import Union
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication
from ..models import catalog_types
from ..utils import custom_logger
from .. import config

logger = custom_logger.get_logger(__file__)

class IconKey(str, Enum):
    FAVORITE_STAR = "favorite_star"
    PRESET_USER = "preset_user"
    FOLDER_CLOSED = "folder_closed"
    FOLDER_OPEN = "folder_open"
    GROUP_ADD = "group_add"
    COMBINATION_ADD = "combination_add"
    
    # Own resources
    TOOLBAR_MAIN_MENU_ICON = "toolbar_main_menu"
    
# QGIS icons start with "/" while Plugin icons/images/resources start without "/"
ICON_PATHS: dict[IconKey, str] = {
    IconKey.FAVORITE_STAR: "/mIconFavorites.svg",
    IconKey.PRESET_USER: "/user.svg",
    IconKey.FOLDER_CLOSED: "/mIconFolder.svg",
    IconKey.FOLDER_OPEN: "/mIconFolderOpen.svg",
    IconKey.GROUP_ADD: "/mActionAddGroup.svg",
    IconKey.COMBINATION_ADD: "/mActionDataSourceManager.svg",
    IconKey.TOOLBAR_MAIN_MENU_ICON: "GeoBasis_Loader_Main_Icon.png"
}

LAYER_TYPE_ICON_PATHS: dict[catalog_types.TopicType, str] = {
    catalog_types.TopicType.WMS: "/mIconWms.svg",
    catalog_types.TopicType.WMTS: "/mIconWms.svg",
    catalog_types.TopicType.WCS: "/mIconWcs.svg",
    catalog_types.TopicType.WFS: "/mIconWfs.svg",
    catalog_types.TopicType.APIF: "/mIconWfs.svg",
    catalog_types.TopicType.VECTORTILES: "/mIconVectorTileLayer.svg",
    catalog_types.TopicType.ARCGIS_FEATURE_SERVER: "/mActionAddAfsLayer.svg",
    catalog_types.TopicType.ARCGIS_MAP_SERVER: "/mActionAddAmsLayer.svg",
    catalog_types.TopicType.WEB: "/search.svg"
}

_icons: dict[str, QIcon] = {}

def get_icon_from_topic_type(topic_type: catalog_types.TopicType) -> QIcon:
    if not isinstance(topic_type, catalog_types.TopicType):
        logger.critical(f"Icon not found: Topic type '{type}' unknown")
        return QIcon()
    
    if topic_type in _icons:
        return _icons[topic_type]
    
    # Lazy init
    if topic_type not in LAYER_TYPE_ICON_PATHS:
        logger.critical(f"Icon not found: No icon known for topic type '{topic_type}'")
        return QIcon()
    
    icon = QgsApplication.getThemeIcon(LAYER_TYPE_ICON_PATHS[topic_type])
    _icons[topic_type] = icon
    
    return icon

def get_icon_from_key(icon_key: IconKey) -> QIcon:
    if not isinstance(icon_key, IconKey):
        logger.critical(f"Icon not found: Icon key '{icon_key}' unknown")
        return QIcon()
    
    if icon_key in _icons:
        return _icons[icon_key]
    
    # Lazy init
    if icon_key not in ICON_PATHS:
        logger.critical(f"Icon not found: No icon known for key '{icon_key}'")
        return QIcon()
    
    icon_path = ICON_PATHS[icon_key]
    if icon_path.startswith("/"):
        icon = QgsApplication.getThemeIcon(icon_path)
    else:
        path = (config.RESOURCES_DIR / icon_path).resolve()
        icon = QIcon(str(path))
    
    _icons[icon_key] = icon
    
    return icon

def get_icon_from_entry(entry: catalog_types.BasicEntry) -> QIcon:
    if isinstance(entry, catalog_types.Region):
        icon = get_icon(IconKey.FOLDER_CLOSED)
    elif isinstance(entry, catalog_types.Topic):
        icon = get_icon(entry.topic_type)
    elif isinstance(entry, catalog_types.TopicGroup):
        icon = get_icon(IconKey.FOLDER_CLOSED)
    elif isinstance(entry, catalog_types.TopicCombination):
        icon = get_icon(IconKey.COMBINATION_ADD)
    else:
        logger.critical(f"Ungültiger Typ für Eintrag: {type(entry)}")
        icon = QIcon()
        
    return icon

def get_icon(key: Union[str, IconKey, catalog_types.TopicType]) -> QIcon:
    if not isinstance(key, str):
        logger.critical(f"Icon ID is not a string: ID of type {key.__class__}")
        return QIcon()
    
    if key in _icons:
        return _icons[key]
    
    try:
        topic_type = catalog_types.TopicType(key)
        return get_icon_from_topic_type(topic_type)
    except ValueError:
        pass
    
    try:
        icon_key = IconKey(key)
        return get_icon_from_key(icon_key)
    except ValueError:
        pass
    
    logger.critical(f"Icon not found: Icon key '{key}' unknown")
    return QIcon()