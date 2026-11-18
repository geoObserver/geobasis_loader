from typing import Optional
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QObject, pyqtSignal
from .bookmark_repository import BookmarkRepository
from . import bookmark_infrastructure
from ...core.utils import custom_logger, signal_utils
from ...core import config

logger = custom_logger.get_logger(__name__)

class BookmarkManager(QObject):
    qgis_bookmark_removed = pyqtSignal(str)
    
    def __init__(self):
        self._bookmark_repository = None
    
    @property
    def bookmark_repository(self) -> Optional[BookmarkRepository]:
        if self._bookmark_repository is None:
            bookmark_manager = QgsApplication.bookmarkManager()
            if bookmark_manager is None:
                logger.error("QGIS Bookmark Manager nicht verfügbar.")
                return None
            self._bookmark_repository = BookmarkRepository(bookmark_manager)
            bookmark_manager.bookmarkRemoved.connect(self._on_qgis_bookmark_removed)
        return self._bookmark_repository
    
    def dispose(self) -> None:
        repo = self.bookmark_repository
        if repo is not None:
            signal_utils.disconnect_signal(repo._bookmark_manager.bookmarkRemoved, self._on_qgis_bookmark_removed)
        else:
            logger.warning("Bookmark Repository ist nicht verfügbar. Signal konnte nicht getrennt werden.")
        signal_utils.disconnect_all_signals(self)
        self.deleteLater()
    
    def has_spatial_bookmark(self, bookmark_id: str) -> bool:
        if self.bookmark_repository is None:
            logger.error("Bookmark Repository nicht verfügbar. Überprüfung auf räumliches Lesezeichen kann nicht durchgeführt werden.")
            return False
        return self.bookmark_repository.has_spatial_bookmark(bookmark_id)
    
    def create_and_add_spatial_bookmark_from_canvas(self, name: str, id: Optional[str] = None) -> Optional[str]:
        if self.bookmark_repository is None:
            logger.error("Bookmark Repository nicht verfügbar. Räumliches Lesezeichen kann nicht erstellt werden.")
            return None
        
        try:
            bookmark = bookmark_infrastructure.create_spatial_bookmark_from_canvas()
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des räumlichen Lesezeichens aus der Kartenansicht: {e}")
            return None
        
        bookmark.setId(id)
        bookmark.setName(name)
        bookmark.setGroup(config.BOOKMARK_GROUP_NAME)
        
        if self.bookmark_repository.has_spatial_bookmark(bookmark.id()):
            logger.info(f"Räumliches Lesezeichen mit ID '{bookmark.id()}' existiert bereits. Es wird überschrieben.")
        
        id, success = self.bookmark_repository.add_spatial_bookmark(bookmark)
        if success:
            logger.success(f"Räumliches Lesezeichen '{bookmark.name()}' erstellt.")
        else:
            logger.error(f"Fehler beim Erstellen des räumlichen Lesezeichens '{bookmark.name()}'.")
        return id
    
    def apply_spatial_bookmark(self, bookmark_id: str) -> None:
        if self.bookmark_repository is None:
            logger.error("Bookmark Repository nicht verfügbar. Räumliches Lesezeichen kann nicht angewendet werden.")
            return
        
        bookmark = self.bookmark_repository.get_spatial_bookmark_by_id(bookmark_id)
        if bookmark is None:
            logger.error(f"Räumliches Lesezeichen mit ID '{bookmark_id}' nicht gefunden. Anwenden nicht möglich.")
            return
        
        try:
            bookmark_infrastructure.apply_spatial_bookmark(bookmark)
        except Exception as e:
            logger.error(f"Fehler beim Anwenden des räumlichen Lesezeichens '{bookmark.name()}': {e}")

    def remove_spatial_bookmark(self, bookmark_id: str) -> None:
        if self.bookmark_repository is None:
            logger.error("Bookmark Repository nicht verfügbar. Räumliches Lesezeichen kann nicht entfernt werden.")
            return
        
        success = self.bookmark_repository.remove_spatial_bookmark(bookmark_id)
        if success:
            logger.success(f"Räumliches Lesezeichen mit ID '{bookmark_id}' entfernt.")
        else:
            logger.error(f"Fehler beim Entfernen des räumlichen Lesezeichens mit ID '{bookmark_id}'.")

    def _on_qgis_bookmark_removed(self, bookmark_id: str) -> None:
        self.qgis_bookmark_removed.emit(bookmark_id)
