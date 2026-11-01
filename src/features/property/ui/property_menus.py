import weakref
from qgis.PyQt.QtWidgets import QAction
from ....core.ui import CustomQMenu
from ....core import icons
from ....core.utils import signal_utils
from ...catalog.models import catalog_models as catalog_types
from ...catalog.topic.topic_app import TopicLoader
from .favorite_view_model import FavoriteViewModel


class FavoritesMenu(CustomQMenu):
    def __init__(self, favorite_view_model: FavoriteViewModel, parent):
        """Initializes the FavoritesMenu. The provided FavoriteViewModel is used to build the menu and update it when the favorites change.
        The private property manager of the FavoriteViewModel is used to create a TopicLoader for loading topics.
        Since the UI has to be in sync with the topic loader this approach should be fine.

        Args:
            favorite_view_model (FavoriteViewModel): The FavoriteViewModel used to build the menu and update it when the favorites change.
            parent (QWidget): The parent widget of the menu.
        """
        super().__init__("Favoriten", "favorites-menu", parent)
        self.setIcon(icons.get_icon(icons.IconKey.FAVORITE_STAR))
        self._property_manager = favorite_view_model._property_manager
        self.topic_loader = TopicLoader(self._property_manager)
        self.favorite_view_model = favorite_view_model
        self._action_dict: weakref.WeakValueDictionary[str, QAction] = weakref.WeakValueDictionary()
        
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
                action.triggered.connect(self._on_topic_action_triggered)
                self._action_dict[favorite_node.id] = action
                self.addAction(action)
    
    def dispose(self) -> None:
        signal_utils.disconnect_signal(self.favorite_view_model.favorite_nodes_updated, self.build)
        self.clear()
        self._action_dict.clear()
        self.setParent(None)
        self.deleteLater()
    
    def _on_topic_action_triggered(self) -> None:
        sender = self.sender()
        if isinstance(sender, QAction):
            entry: catalog_types.TopicEntry = sender.data()
            if isinstance(entry, catalog_types.TopicEntry):
                if isinstance(entry, catalog_types.Topic) and entry.is_web():
                    self.topic_loader.open_web_site(entry.uri)
                else:
                    self.topic_loader.add_topic(entry)
            else:
                logger.warning(f"Ungültige Daten im QAction-Objekt: {sender.objectName()}")

    # def _show_context_menu(self, action: QAction, global_pos) -> None:
    #     data = action.data()
    #     if not isinstance(data, str):
    #         return
        
    #     context_menu = TopicContextMenu(data, self)
    #     context_menu.exec(global_pos)