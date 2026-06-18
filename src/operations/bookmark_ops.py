from typing import Optional
from qgis.core import QgsBookmark, QgsApplication
from ..services import registry
from ..utils import helpers, custom_logger
from .. import config

logger = custom_logger.get_logger(__name__)

def add_gbl_spatial_bookmark(name: str, id: Optional[str] = None) -> tuple[Optional[str], bool]:
    bookmark_manager = QgsApplication.bookmarkManager()
    if bookmark_manager is None:
        logger.error("QGIS Bookmark Manager nicht verfügbar. Räumliches Lesezeichen kann nicht erstellt werden.")
        return None, False
    
    bookmark = helpers.create_spatial_bookmark()
    bookmark.setId(id)
    bookmark.setName(name)
    bookmark.setGroup(config.BOOKMARK_GROUP_NAME)
    
    id, successful = bookmark_manager.addBookmark(bookmark)
    if successful:
        logger.success(f"Räumliches Lesezeichen '{name}' erstellt.")
    else:
        logger.error(f"Fehler beim Erstellen des räumlichen Lesezeichens '{name}'.")
    return id, successful

def remove_gbl_spatial_bookmark(bookmark_id: str) -> bool:
    bookmark_manager = QgsApplication.bookmarkManager()
    if bookmark_manager is None:
        logger.error("QGIS Bookmark Manager nicht verfügbar. Räumliches Lesezeichen kann nicht entfernt werden.")
        return False
    
    successful = bookmark_manager.removeBookmark(bookmark_id)
    if successful:
        logger.success(f"Räumliches Lesezeichen mit ID '{bookmark_id}' entfernt.")
    else:
        logger.error(f"Fehler beim Entfernen des räumlichen Lesezeichens mit ID '{bookmark_id}'.")
    return successful

def _remove_gbl_spatial_bookmark_from_presets(bookmark_id: str) -> None:
    for preset in registry.preset_manager.user_presets.values():
        if preset.spatial_bookmark_id == bookmark_id:
            preset.spatial_bookmark_id = None
            registry.preset_manager.save_user_presets()
            logger.success(f"Räumliches Lesezeichen mit ID '{bookmark_id}' aus Preset '{preset.title}' entfernt.")