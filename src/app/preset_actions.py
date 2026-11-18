from ..features.preset import PresetManager
from ..features.bookmark import BookmarkManager

class PresetActions:
    def __init__(self, preset_manager: PresetManager, bookmark_manager: BookmarkManager):
        self._preset_manager = preset_manager
        self._bookmark_manager = bookmark_manager
    
    