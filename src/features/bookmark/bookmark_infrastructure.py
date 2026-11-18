from typing import Optional
from qgis.core import QgsBookmark, QgsBookmarkManager, QgsProject, QgsCsException, QgsReferencedRectangle
from qgis.utils import iface


def apply_spatial_bookmark(bookmark: QgsBookmark) -> None:
    """Applies a spatial bookmark to the current QGIS project.

    Args:
        bookmark (QgsBookmark): The spatial bookmark to be applied.

    Raises:
        TypeError: If the provided bookmark is not an instance of QgsBookmark.
        ValueError: If the bookmark does not contain valid spatial information.
        RuntimeError: If the QGIS interface or map canvas is not available, or if there is an error applying the bookmark.
    """
    
    if not isinstance(bookmark, QgsBookmark):
        raise TypeError("Provided bookmark must be an instance of QgsBookmark")
    
    extent = bookmark.extent()
    if extent.isNull():
        raise ValueError("Provided bookmark extent is null or invalid")
    
    if iface is None or not hasattr(iface, 'mapCanvas'):
        raise RuntimeError("QGIS interface is not available or does not have a map canvas")
    
    canvas: QgsMapCanvas = iface.mapCanvas() # type: ignore
    if canvas is None:
        raise RuntimeError("QGIS map canvas is not available")
    
    try:
        canvas.setReferencedExtent(extent)
    except QgsCsException as e:
        raise RuntimeError(f"Failed to apply spatial bookmark due to transformation error: {e}")
    
    canvas.setRotation(bookmark.rotation())
    canvas.refresh()

def create_spatial_bookmark_from_canvas() -> QgsBookmark:
    if iface is None or not hasattr(iface, 'mapCanvas'):
        raise RuntimeError("QGIS interface is not available or does not have a map canvas")
    
    canvas: QgsMapCanvas = iface.mapCanvas() # type: ignore
    if canvas is None:
        raise RuntimeError("QGIS map canvas is not available")
    
    project = QgsProject.instance()
    if project is None:
        raise RuntimeError("QGIS project instance is not available")
    
    extent = canvas.extent()
    crs = project.crs()
    rotation = canvas.rotation()
    
    referenced_extent = QgsReferencedRectangle(extent, crs)
    bookmark = QgsBookmark()
    bookmark.setExtent(referenced_extent)
    bookmark.setRotation(rotation)
    
    return bookmark
