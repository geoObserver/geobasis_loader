"""QGIS plugin entry point for GeoBasis_Loader.

Provides the ``classFactory`` function required by QGIS to instantiate the plugin.
"""

from .GeoBasis_Loader_main import GeoBasis_Loader


def classFactory(iface):
    """Create and return the GeoBasis_Loader plugin instance.

    Args:
        iface: A ``QgisInterface`` instance giving access to the QGIS application.

    Returns:
        A ``GeoBasis_Loader`` plugin object bound to *iface*.

    """
    return GeoBasis_Loader(iface)
