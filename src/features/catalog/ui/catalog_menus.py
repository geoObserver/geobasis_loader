from qgis.PyQt.QtWidgets import QAction
from ....core.ui import CustomQMenu


class TopicMenu(CustomQMenu):
    def __init__(self, title: str, object_name: str, parent=None):
        super().__init__(title, object_name, parent)
    
    def _show_context_menu(self, action: QAction, global_pos) -> None:
        data = action.data()
        if not isinstance(data, str):
            return
        
        # FIXME
        # context_menu = TopicContextMenu(data, self)
        # context_menu.exec(global_pos)