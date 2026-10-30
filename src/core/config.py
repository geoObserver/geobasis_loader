import configparser
import pathlib
from dataclasses import dataclass
from typing import Optional
from qgis.core import QgsApplication


PLUGIN_DIR = pathlib.Path(__file__).resolve().parents[2]
PLUGIN_USER_DIR = pathlib.Path(QgsApplication.qgisSettingsDirPath()) / "geobasis_loader"

RESOURCES_DIR = PLUGIN_DIR / "resources"
CACHE_DIR = PLUGIN_DIR / "cache"
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

PLUGIN_NAME = plugin_info.name.lower()
PLUGIN_TITLE = plugin_info.name
PLUGIN_NAME_AND_VERSION = PLUGIN_TITLE + ' (v' + plugin_info.version + ')'

TOOLBAR_NAME = "geoObserverTools"
LOGGING_SUCCESS_LEVEL = 25
PRESET_FORMAT_VERSION = 7.00
CATALOG_FORMAT_VERSION = 7.00
STAR_PREFIX = "\u2605 "  # ★
SEARCH_HIGHLIGHT_COLOR = "#DA0000"  # Red, for highlight text when searching in the panel
GRAYED_OUT_COLOR = "#808080"  # Gray, for items from other catalogs

# CURRENT_CATALOG_SCORE_BONUS = 1000  # Score bonus for entries from the currently selected catalog

GEOOBSERVER_SERVICE = "https://geoobserver.de/download/GeoBasis_Loader/{name}"
GITHUB_SERVICE = "https://api.github.com/repos/geoObserver/geobasis_loader/contents/kataloge/{name}?ref=main"
