from enum import Enum
import configparser
import pathlib
from dataclasses import dataclass
from typing import Optional
from qgis.core import QgsSettings, QgsApplication


PLUGIN_DIR = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_USER_DIR = pathlib.Path(QgsApplication.qgisSettingsDirPath()) / "geobasis_loader"

RESOURCES_DIR = PLUGIN_DIR / "resources"
PRESETS_DIR = PLUGIN_USER_DIR / "presets"

@dataclass(frozen=True)
class PluginInfo:
    name: str = ""
    version: str = ""
    icon: str = ""
    icon_path: Optional[pathlib.Path] = None
    description: str = ""
    qgis_min_version: str = ""
    qgis_max_version: str = ""
    author: str = ""
    email: str = ""
    homepage: str = ""
    repository: str = ""
    tracker: str = ""

def read_metadata(metadata_path: Optional[pathlib.Path] = None) -> PluginInfo:
    path = metadata_path or (PLUGIN_DIR / "metadata.txt")
    if not path.exists():
        return PluginInfo()

    parser = configparser.ConfigParser()
    parser.optionxform = str
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error:
        return PluginInfo()

    section = parser["general"] if parser.has_section("general") else {}
    name = section.get("name", "")
    name = name.replace("_", " ") if name else ""
    icon = section.get("icon", "")
    icon_path = (PLUGIN_DIR / icon) if icon else None

    return PluginInfo(
        name=name,
        version=section.get("version", ""),
        icon=icon,
        icon_path=icon_path,
        description=section.get("description", ""),
        qgis_min_version=section.get("qgisMinimumVersion", ""),
        qgis_max_version=section.get("qgisMaximumVersion", ""),
        author=section.get("author", ""),
        email=section.get("email", ""),
        homepage=section.get("homepage", ""),
        repository=section.get("repository", ""),
        tracker=section.get("tracker", ""),
    )

plugin_info = read_metadata()

PLUGIN_NAME = plugin_info.name
PLUGIN_NAME_AND_VERSION = PLUGIN_NAME + ' (v' + plugin_info.version + ')'


REQUEST_TIMEOUT_MS = 10000
PLUGIN_LOGGER_NAME = "geobasis_loader"
TOOLBAR_NAME = "geoobserver"
LOGGING_SUCCESS_LEVEL = 25
PRESET_FORMAT_VERSION = 7.00

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
        all_servers = cls.get_all_servers()
        if server_index == 0 or server_index > len(all_servers):
            servers = all_servers
        else:
            servers.append(all_servers[server_index - 1])
            
        return servers
    
class QgsSettingsKeys(str, Enum):
    CURRENT_CATALOG = 'geobasis_loader/current_catalog'
    AUTOMATIC_CRS = 'geobasis_loader/automatic_crs'
    SERVERS = 'geobasis_loader/servers'
    PROPERTY_FAVORITE = 'geobasis_loader/properties/favorite'
    PROPERTY_INVISIBLE = 'geobasis_loader/properties/invisible'
    PROPERTY_DISABLED = 'geobasis_loader/properties/disabled'
