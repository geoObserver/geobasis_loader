import weakref
from qgis.PyQt.QtWidgets import QAction
from ....core.ui import CustomQMenu
from ....core import icons
from .favorite_view_model import FavoriteViewModel
from ....core.utils import signal_utils

class FavoritesMenu(CustomQMenu):
    def __init__(self, favorite_view_model: FavoriteViewModel, parent):
        super().__init__("Favoriten", "favorites-menu", parent)
        self.setIcon(icons.get_icon(icons.IconKey.FAVORITE_STAR))
        self.favorite_view_model = favorite_view_model
        self._action_dict: weakref.WeakValueDictionary[str, QAction] = weakref.WeakValueDictionary()
        self._triggered_action_func = None
        
        self.favorite_view_model.favorite_nodes_updated.connect(self.build)
    
    def build(self) -> None:
        self.clear()
        self._action_dict.clear()
        
        nodes = self.favorite_view_model.get_favorite_nodes()
        if not nodes:
            action = QAction("(Keine)", self)
            action.setObjectName("no-favorites")
            action.setEnabled(False)
            self.addAction(action)
        else:
            for favorite_node in nodes:
                action = QAction(favorite_node.icon, favorite_node.title, self)
                action.setToolTip(favorite_node.tooltip)
                action.setData(favorite_node.entry)
                action.setObjectName(f"favorite-action_{favorite_node.title}")
                action.triggered.connect(self._triggered_action_func)
                self._action_dict[favorite_node.id] = action
                self.addAction(action)
    
    def dispose(self) -> None:
        signal_utils.disconnect_signal(self.favorite_view_model.favorite_nodes_updated, self.build)
        self.clear()
        self._action_dict.clear()
        self.setParent(None)
        self.deleteLater()
    
    def set_triggered_action_func(self, func) -> None:
        self._triggered_action_func = func

    # def _show_context_menu(self, action: QAction, global_pos) -> None:
    #     data = action.data()
    #     if not isinstance(data, str):
    #         return
        
    #     context_menu = TopicContextMenu(data, self)
    #     context_menu.exec(global_pos)