"""Plugin-wide configuration constants, enums, and settings accessors.

Provides ``LayerType``, ``ServerHosts``, and ``InternalProperties`` enums used
throughout the GeoBasis Loader plugin.
"""

from __future__ import annotations

import os
from enum import Enum

from qgis.core import QgsSettings

PLUGIN_VERSION = '2.1'
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

FAVORITES_SETTINGS_KEY = 'geobasis_loader/favorites'

CATALOG_OVERVIEW = "GeoBasis_Loader_v6_Kataloge.json"
CATALOG_OVERVIEW_NAME = "catalog_overview"

class LayerType(str, Enum):
    """Supported geospatial service types for catalog layers."""

    WMS = "ogc_wms"
    WFS = "ogc_wfs"
    WCS = "ogc_wcs"
    WMTS = "ogc_wmts"
    VECTOR_TILES = "ogc_vectortiles"
    OGC_API_FEATURES = "ogc_api_features"
    WEB = "web"

class ServerHosts(str, Enum):
    """Remote catalog host URLs with a ``{name}`` placeholder for the catalog filename.

    The plugin tries each enabled server in order and falls back to the next
    one on failure.
    """

    GEOOBSERVER = "https://geoobserver.de/download/GeoBasis_Loader/{name}"
    GITHUB = "https://api.github.com/repos/geoObserver/geobasis_loader/contents/kataloge/{name}?ref=main"

    @classmethod
    def get_all_servers(cls) -> list[str]:
        """Return the URL templates of all defined server hosts.

        Returns:
            List of URL template strings, one per enum member.

        """
        return [a.value for a in cls]

    @classmethod
    def get_enabled_servers(cls) -> list[str]:
        """Return the URL templates of servers enabled in the user settings.

        When the stored server index is ``0`` (default), all servers are
        returned.  Otherwise only the single server at *index - 1* is
        returned.

        Returns:
            List of enabled URL template strings.

        """
        servers = []
        qgs_settings = QgsSettings()
        server_index = qgs_settings.value(SERVERS_SETTINGS_KEY, 0, type=int)
        if server_index == 0:
            servers = cls.get_all_servers()
        else:
            servers.append(cls.get_all_servers()[server_index - 1])

        return servers

class InternalProperties(str, Enum):
    """Internal marker keys attached to layer definitions for runtime state.

    These properties are not part of the catalog JSON but are added at
    runtime to track visibility, loading state, and favorites.
    """

    FAVORITE = "__favorite__"
    VISIBILITY = "__visible__"
    LOADING = "__loading__"
    PATH = "__path__"

    @classmethod
    def get_properties(cls) -> list[InternalProperties]:
        """Return the internal properties used for layer state tracking.

        ``PATH`` and ``FAVORITE`` are excluded because they serve a
        different purpose (navigation / persistence).

        Returns:
            List of ``InternalProperties`` members relevant to runtime state.

        """
        return [a for a in cls if a not in (cls.PATH, cls.FAVORITE)]
