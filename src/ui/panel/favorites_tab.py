from qgis.PyQt import uic, QtWidgets, QtCore
from ...models import catalog_types
from ...core import events
from ...services import registry
from .. import icons
from .. import context_menus
from ...operations import topic_ops
from ... import config
from ...utils import custom_logger

logger = custom_logger.get_logger(__name__)

FAVORITES_TAB = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "favorites_tab.ui")[0]
CATALOG_USER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
REGION_USER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2
URI_USER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 3

# FIXME: Estending after clicking the arrow is weird. If clicking with specific timing nothing happens
# FIXME: Adding/removing favorites resets view (scroollbar position)
# FIXME: Save view selection
class FavoritesTab(QtWidgets.QWidget, FAVORITES_TAB):
    def __init__(self, parent: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.initialized = False
        self._all_items: list[QtWidgets.QTreeWidgetItem] = []
           
        # Type hints for UI elements
        self.view_selection_combo_box: QtWidgets.QComboBox = self.view_selection_combo_box
        self.favorites_tree_widget: QtWidgets.QTreeWidget = self.favorites_tree_widget
        self.favorite_count: QtWidgets.QLabel = self.favorite_count
        self.missing_favorites_widget: QtWidgets.QWidget = self.missing_favorites_widget
        self.missing_favorite_count: QtWidgets.QLabel = self.missing_favorite_count
        
        # Connect slots
        self.view_selection_combo_box.currentIndexChanged.connect(self._set_style)
        self.favorites_tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.favorites_tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.favorites_tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        self.favorites_tree_widget.customContextMenuRequested.connect(self._on_favorites_tree_context_menu)
        
        events.connect_favorites_updated(self.build_favorites_tree)
        
        # Settings/Defaults
        self.missing_favorites_widget.setVisible(False)
    
    def build_favorites_tree(self) -> None:
        def _add_entry(data: catalog_types.BasicEntry) -> QtWidgets.QTreeWidgetItem:            
            item = QtWidgets.QTreeWidgetItem(None)
            icon = icons.get_icon_from_entry(data)
            item.setIcon(0, icon)
            item.setText(0, data.name)
            # FIXME: Method in BasicEntry to get description
            if isinstance(data, catalog_types.TopicGroup):
                item.setToolTip(0, f"{data.name} [Gruppe, {len(data.get_subtopics())} Themen]")
            elif isinstance(data, catalog_types.TopicCombination):
                item.setToolTip(0, f"{data.name} [Kombination, {len(data.topic_paths)} Themen]")
            else:
                item.setToolTip(0, data.name)
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data.path)
            if isinstance(data, catalog_types.Topic) and data.topic_type == catalog_types.TopicType.WEB:
                item.setData(0, URI_USER_ROLE, data.uri)
            
            return item
        
        self._all_items.clear()
        favorites = registry.property_manager.get_favorites()
        count = 0
        # topics = [registry.catalog_manager.get_topic_by_path(fav) for fav in favorites]
        for fav in favorites:
            path_parts = registry.catalog_manager.get_parts_by_path(fav)
            if path_parts is None:
                logger.warning(f"Favorite topic not found: {fav}")
                continue
            
            topic = path_parts.entry
            if isinstance(topic, catalog_types.Catalog):
                logger.warning(f"Favorite topic is a catalog, not a topic: {fav}")
                continue
            
            item = _add_entry(topic)
            region_name = path_parts.region.name if path_parts.region else "Unknown"
            catalog_name = path_parts.catalog.name if path_parts.catalog else "Unknown"
            item.setData(0, CATALOG_USER_ROLE, catalog_name)
            item.setData(0, REGION_USER_ROLE, region_name)
            count += 1
            self._all_items.append(item)
        
        self._set_style(self.view_selection_combo_box.currentIndex())
        
        self.favorite_count.setText(str(count))
        missing = len(favorites) - count
        self._set_missing_favorites_widget(missing)
        self.initialized = missing == 0             # Always init on zero missing -> Always relaod tree upon tab enter -> just in case catalogs are missing
    
    def _show_flat_style(self) -> None:
        for item in self._all_items:
            self.favorites_tree_widget.addTopLevelItem(item)
    
    def _show_catalog_style(self) -> None:
        self._grouped_style(CATALOG_USER_ROLE)
    
    def _show_region_style(self) -> None:
        self._grouped_style(REGION_USER_ROLE)
    
    def _grouped_style(self, user_role: int) -> None:
        for item in self._all_items:
            parent_name = item.data(0, user_role)
            parent_items = self.favorites_tree_widget.findItems(parent_name, QtCore.Qt.MatchFlag.MatchExactly, 0)
            if parent_items:
                parent_item = parent_items[0]
            else:
                parent_item = QtWidgets.QTreeWidgetItem(self.favorites_tree_widget)
                parent_item.setText(0, parent_name)
                parent_item.setIcon(0, icons.get_icon(icons.IconKey.FOLDER_OPEN))
                parent_item.setExpanded(True)
            
            parent_item.addChild(item)
    
    def _set_style(self, index: int) -> None:
        self._clear_tree()
        if index == 0:
            self._show_flat_style()
        elif index == 1:
            self._show_catalog_style()
        else:
            self._show_region_style()
        self.favorites_tree_widget.sortItems(0, QtCore.Qt.SortOrder.AscendingOrder)
    
    # Custom method necessary so the items arent destroyed upon clearing
    # This means changing the style doesnt result in a total rebuild of the tree, but just a reparenting of the items    
    def _clear_tree(self) -> None:
        for item in self._all_items:
            parent = item.parent()
            if parent is not None:
                parent.removeChild(item)
            else:
                self.favorites_tree_widget.takeTopLevelItem(self.favorites_tree_widget.indexOfTopLevelItem(item))
        self.favorites_tree_widget.clear()
    
    def _on_item_double_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            return
        
        uri = item.data(0, URI_USER_ROLE)
        if isinstance(data, str):
            if uri:
                topic_ops.open_web_site(uri)
            else:
                topic_ops.add_topic(data)
        else:
            logger.warning(f"Unexpected data type for the double-clicked item: {type(data)}")
    
    def _on_favorites_tree_context_menu(self, position: QtCore.QPoint) -> None:
        item = self.favorites_tree_widget.itemAt(position)
        if item is None:
            return
        
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            return
        
        menu = context_menus.TopicContextMenu(data, self)
        viewport = self.favorites_tree_widget.viewport()
        if not viewport:
            logger.warning("Viewport not found for the favorites tree widget.")
            return
        
        menu.exec(viewport.mapToGlobal(position))
    
    def _set_missing_favorites_widget(self, count: int) -> None:
        self.missing_favorite_count.setText(str(count))
        self.missing_favorites_widget.setVisible(count > 0)
    
    def _on_item_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        item.setIcon(0, icons.get_icon(icons.IconKey.FOLDER_OPEN))
        
    def _on_item_collapsed(self, item: QtWidgets.QTreeWidgetItem) -> None:
        item.setIcon(0, icons.get_icon(icons.IconKey.FOLDER_CLOSED))