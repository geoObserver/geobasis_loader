from typing import Optional
from qgis.core import QgsBookmark, QgsBookmarkManager, QgsApplication, QgsCsException, QgsReferencedRectangle


class BookmarkRepository:
    def __init__(self, bookmark_manager: QgsBookmarkManager):
        self._bookmark_manager = bookmark_manager

    def get_spatial_bookmark_by_id(self, bookmark_id: str) -> Optional[QgsBookmark]:
        bookmark = self._bookmark_manager.bookmarkById(bookmark_id)
        if bookmark is None or bookmark.id() != bookmark_id:
            return None
        return bookmark
    
    def has_spatial_bookmark(self, bookmark_id: str) -> bool:
        bookmark = self._bookmark_manager.bookmarkById(bookmark_id)
        return bookmark is not None and bookmark.id() == bookmark_id

    def add_spatial_bookmark(self, bookmark: QgsBookmark) -> tuple[Optional[str], bool]:
        if self.has_spatial_bookmark(bookmark.id()):
            successful = self._bookmark_manager.updateBookmark(bookmark)
            return bookmark.id(), successful
        else:
            id, successful = self._bookmark_manager.addBookmark(bookmark)
            return id, successful

    def remove_spatial_bookmark(self, bookmark_id: str) -> bool:       
        return self._bookmark_manager.removeBookmark(bookmark_id)
