from typing import TYPE_CHECKING
from qgis.PyQt.QtWidgets import QAction
from ....core.ui import CustomQMenu
from ..models import catalog_models as catalog_types

if TYPE_CHECKING:
    from ....shared_ui.context_menus import TopicContextMenuFactory
    

class TopicMenu(CustomQMenu):
    def __init__(self, title: str, object_name: str, context_menu_factory: "TopicContextMenuFactory", parent=None):
        super().__init__(title, object_name, parent)
        self._context_menu_factory = context_menu_factory

    def _show_context_menu(self, action: QAction, global_pos) -> None:
        data = action.data()
        if not isinstance(data, catalog_types.TopicEntry):
            return
        
        context_menu = self._context_menu_factory.create(data, self)
        context_menu.exec(global_pos)