from typing import Union
from qgis.PyQt import uic, QtWidgets, QtCore, QtGui
from qgis.gui import QgsFilterLineEdit, QgsTreeWidgetItem
from ..widgets.item_delegates import SearchHighlightItemDelegate
from ...models import catalog_types
from ...core import events, search_index, plugin_settings
from ...operations import topic_ops
from ...services import registry
from .. import icons
from .. import context_menus
from .. import menus
from ... import config
from ...utils import custom_logger

logger = custom_logger.get_logger(__name__)

CATALOG_TAB = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "catalog_tab.ui")[0]
URI_USER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1

# FIXME: Display setting st show hidden items
class CatalogTab(QtWidgets.QWidget, CATALOG_TAB):
    def __init__(self, parent: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.initialized = False
        self._all_items = []
        self._top_level_items = []
        self._expanded_items = set()
        self._searching = False
        self._timer = QtCore.QTimer(self)
        self._search_highlight_delegate = SearchHighlightItemDelegate(self.catalog_tree_widget)
        self._display_menu = menus.CatalogDisplayOptionsMenu(self.display_settings_button)
        self.topic_search_line_edit: QgsFilterLineEdit = QgsFilterLineEdit(self.topic_search_line_edit_widget)
        
        # Type hints for UI elements
        self.catalog_selection_combo_box: QtWidgets.QComboBox = self.catalog_selection_combo_box
        self.display_settings_button: QtWidgets.QPushButton = self.display_settings_button
        self.catalog_refresh_button: QtWidgets.QPushButton = self.catalog_refresh_button
        self.topic_search_line_edit_widget: QtWidgets.QWidget = self.topic_search_line_edit_widget
        self.catalog_tree_widget: QtWidgets.QTreeWidget = self.catalog_tree_widget
        self.topic_count_widget: QtWidgets.QWidget = self.topic_count_widget
        self.search_count_widget: QtWidgets.QWidget = self.search_count_widget
        self.other_catalog_search_count_widget: QtWidgets.QWidget = self.other_catalog_search_count_widget
        self.contact_label: QtWidgets.QLabel = self.contact_label
        self.topic_count_label: QtWidgets.QLabel = self.topic_count_label
        self.current_catalog_search_count_label: QtWidgets.QLabel = self.current_catalog_search_count_label
        self.other_catalog_search_count_label: QtWidgets.QLabel = self.other_catalog_search_count_label
        
        # Add icons to buttons
        self.display_settings_button.setIcon(icons.get_icon(icons.IconKey.SETTINGS))
        self.catalog_refresh_button.setIcon(icons.get_icon(icons.IconKey.REFRESH_ARROWS))
    
        # Connect slots
        self.catalog_selection_combo_box.currentIndexChanged.connect(self._on_catalog_selection_changed)
        self.catalog_refresh_button.clicked.connect(lambda: registry.catalog_manager.get_overview())
        self.topic_search_line_edit.valueChanged.connect(self._start_search_timer)
        
        self.catalog_tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.catalog_tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.catalog_tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        self.catalog_tree_widget.customContextMenuRequested.connect(self._on_catalog_tree_context_menu)
        
        events.connect_overview_updated(self._build_catalog_selection)
        events.connect_current_catalog_updated(self.build_catalog_tree)
        events.connect_current_catalog_updated(self.set_catalog_selection)
        events.connect_visibility_updated(self.build_catalog_tree)
        events.connect_enabled_updated(self.build_catalog_tree)
        events.connect_favorites_updated(self.build_catalog_tree) # FIXME: Only selected updating instead of whole tree
        events.connect_display_highlight_favorites_changed(self.build_catalog_tree) # FIXME: Only selected updating instead of whole tree
        
        # Settings/Defaults
        self.topic_search_line_edit.setPlaceholderText("Thema suchen...")
        self.topic_search_line_edit.setShowSearchIcon(True)
        self.topic_search_line_edit.setToolTip("Eingabe zum Filtern (mind. 2 Zeichen).\nBegriffe mit Leerzeichen trennen (UND-Verknüpfung).\nDurchsucht Namen und Stichworte")
        layout = self.topic_search_line_edit_widget.layout()
        if layout is not None:
            layout.addWidget(self.topic_search_line_edit)

        self.search_count_widget.setVisible(False)
        self._timer.setInterval(300)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._filter_items)
        self.catalog_tree_widget.setItemDelegate(self._search_highlight_delegate)
        self._display_menu.build()
        self.display_settings_button.setMenu(self._display_menu)
        self.display_settings_button.setStyleSheet("""
            QPushButton::menu-indicator { 
                image: none; 
                width: 0px; 
            }
        """)
    
    def _build_catalog_selection(self) -> None:
        current_overview = registry.catalog_manager.overview
        if current_overview is None:
            logger.warning("No catalog overview available. Cannot build catalog menu.")
            return

        blocker = QtCore.QSignalBlocker(self.catalog_selection_combo_box)
        self.catalog_selection_combo_box.clear()
        for catalog_info in current_overview:
            self.catalog_selection_combo_box.addItem(catalog_info["titel"], catalog_info)
        
        self.set_catalog_selection()
    
    def _on_catalog_selection_changed(self, index: int) -> None:
        catalog_data = self.catalog_selection_combo_box.itemData(index)
        if catalog_data is None:
            logger.info("Kein Katalog ausgewählt")
            return
        
        registry.catalog_manager.set_current_catalog(catalog_data)
    
    def set_catalog_selection(self) -> None:
        # Block signal since its already being done beacuase of a signal
        blocker = QtCore.QSignalBlocker(self.catalog_selection_combo_box)
        catalog_info = plugin_settings.current_catalog
        
        selected_index = self.catalog_selection_combo_box.findData(catalog_info)
        placeholder_index = self.catalog_selection_combo_box.findData(None)
        if selected_index != -1:
            # Placeholder is None and new catalog is {} meaning that the placeholder cant be found so if nothing is found its the placeholder
            self.catalog_selection_combo_box.setCurrentIndex(selected_index)
            if placeholder_index != -1:
                self.catalog_selection_combo_box.removeItem(placeholder_index)  # Remove the placeholder item if a valid catalog is selected
        else:
            if placeholder_index == -1:
                self.catalog_selection_combo_box.insertItem(0, "Katalog auswählen...", None)  # Add a placeholder item at the top
            self.catalog_selection_combo_box.setCurrentIndex(0)  # Ensure the placeholder is selected if no valid catalog is found
    
    def build_catalog_tree(self) -> None:
        def _add_entry(data: catalog_types.BasicEntry, parent: Union[QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidget]) -> QtWidgets.QTreeWidgetItem:            
            item = QtWidgets.QTreeWidgetItem(parent)
            icon = icons.get_icon_from_entry(data)
            item.setIcon(0, icon)
            text = config.STAR_PREFIX + data.name if data.properties.favorite else data.name
            item.setText(0, text)
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data.path)
            item.setHidden(not data.properties.visible)
            
            if isinstance(data, catalog_types.Topic):
                if data.topic_type == catalog_types.TopicType.WEB:
                    item.setToolTip(0, f"{data.name} öffnen")
                    item.setData(0, URI_USER_ROLE, data.uri)
                else:
                    item.setToolTip(0, f"{data.name} laden")
            # FIXME: See prestes_tab
            elif isinstance(data, catalog_types.TopicGroup):
                item.setToolTip(0, f"{data.name} [Gruppe, {len(data.get_subtopics())} Themen]")
                add_all_item = QtWidgets.QTreeWidgetItem(item)
                add_all_item.setText(0, f"Alle laden ({data.name})")
                add_all_item.setIcon(0, icons.get_icon(icons.IconKey.GROUP_ADD))
                add_all_item.setToolTip(0, f"Alle Themen in {data.name} laden")
                add_all_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data.path)
            elif isinstance(data, catalog_types.TopicCombination):
                item.setToolTip(0, f"{data.name} [Kombination, {len(data.topic_paths)} Themen]")
            
            self._all_items.append(item)
            return item
        
        current_catalog = registry.catalog_manager.get_current_catalog()
        if current_catalog is None:
            logger.warning("No current catalog set. Cannot build catalog tree.")
            return

        if not isinstance(current_catalog, catalog_types.Catalog):
            logger.critical(f"Ungültiger Typ für Katalog: {type(current_catalog)}")
            return
        # Clear existing items in the tree
        self.catalog_tree_widget.clear()
        self._all_items.clear()
        self.catalog_selection_combo_box.setCurrentText(current_catalog.name)
        bolded_font = QtGui.QFont(self.catalog_tree_widget.font())
        bolded_font.setBold(True)
        highlight_favorites = plugin_settings.highlight_favorites
        entry_count = 0
        
        for region in current_catalog.get_regions():
            region_has_favorite = False
            region_item = _add_entry(region, self.catalog_tree_widget)
            region_item.setExpanded(region.path in self._expanded_items)
            for topic in region.get_topics():
                topic_has_favorite = False
                topic_item = _add_entry(topic, region_item)
                if topic.properties.favorite and highlight_favorites:
                    region_has_favorite = True
                    topic_item.setFont(0, bolded_font)
                
                if isinstance(topic, catalog_types.Topic):
                    entry_count += 1        # Only count destinct topics, not group items or combinations
                if not isinstance(topic, catalog_types.TopicGroup):
                    continue
                
                topic_item.setExpanded(topic.path in self._expanded_items)
                subtopics = topic.get_subtopics()
                entry_count += len(subtopics)
                for subtopic in subtopics:
                    subtopic_item = _add_entry(subtopic, topic_item)
                    if subtopic.properties.favorite and highlight_favorites:
                        region_has_favorite = True
                        topic_has_favorite = True
                        subtopic_item.setFont(0, bolded_font)
                
                if topic_has_favorite and highlight_favorites:
                    topic_item.setFont(0, bolded_font)
            
            if region_has_favorite and highlight_favorites:
                region_item.setFont(0, bolded_font)
        
        self.topic_count_label.setText(str(entry_count))
        self.initialized = True
    
    def set_searching(self, searching: bool) -> None:
        if searching:
            self.catalog_selection_combo_box.setEnabled(False)
            self.topic_count_widget.setVisible(False)
            self.search_count_widget.setVisible(True)
            self.contact_label.setVisible(False)
            while self.catalog_tree_widget.topLevelItemCount() > 0 and not self._searching:
                self._top_level_items.append(self.catalog_tree_widget.takeTopLevelItem(0))
            self.catalog_tree_widget.setTreePosition(1)
        else:
            self.catalog_selection_combo_box.setEnabled(True)
            self.topic_count_widget.setVisible(True)
            self.search_count_widget.setVisible(False)
            self.contact_label.setVisible(True)
            self.catalog_tree_widget.clear()
            self.catalog_tree_widget.addTopLevelItems(self._top_level_items)
            self._top_level_items.clear()
            self.catalog_tree_widget.setTreePosition(0)
        
        self._searching = searching

    def _filter_items(self) -> None:
        text = self.topic_search_line_edit.text()
        self.catalog_tree_widget.clear()
        current_catalog_hits = 0
        other_catalog_hits = 0
        
        search_index.get_entries()  # Ensure the search index is built
        tokens = search_index.tokenize(text)
        for entry in search_index.find(tokens):
            search_item = QgsTreeWidgetItem(self.catalog_tree_widget)
            score = search_index.score(entry, tokens)
            if entry.catalog_name == self.catalog_selection_combo_box.currentText():
                current_catalog_hits += 1
                score += config.CURRENT_CATALOG_SCORE_BONUS  # Boost score for current catalog entries
            else:
                other_catalog_hits += 1
                search_item.setForeground(0, QtGui.QColor(config.GRAYED_OUT_COLOR))  # Gray out items from other catalogs
                
            search_item.setText(0, entry.name + f" [{entry.region_name}]")
            if entry.entry_type == catalog_types.EntryType.TOPIC:
                icon = icons.get_icon(entry.layer_type)
            elif entry.entry_type == catalog_types.EntryType.TOPIC_GROUP:
                icon = icons.get_icon(icons.IconKey.GROUP_ADD)
            else:
                icon = icons.get_icon(icons.IconKey.COMBINATION_ADD)
            search_item.setIcon(0, icon)
            search_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, entry.path)
            search_item.setToolTip(0, f"{entry.name} laden\nRegion: {entry.region_name}\nKatalog: {entry.catalog_name}")
            search_item.setSortData(0, score)
        
        if self.catalog_tree_widget.topLevelItemCount() > 0:
            separation_item = QgsTreeWidgetItem(self.catalog_tree_widget)
            separation_item.setText(0, "——— Treffer aus anderen Katalogen ———")
            separation_item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)  # Make it unselectable
            separation_item.setForeground(0, QtGui.QColor(config.GRAYED_OUT_COLOR))
            separation_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, None)
            separation_item.setSortData(0, config.CURRENT_CATALOG_SCORE_BONUS - 1)
        
        self.catalog_tree_widget.sortItems(0, QtCore.Qt.SortOrder.DescendingOrder)
        self.current_catalog_search_count_label.setText(str(current_catalog_hits))
        self.other_catalog_search_count_label.setText(str(other_catalog_hits))
        self.other_catalog_search_count_widget.setVisible(other_catalog_hits > 0)
    
    def _on_item_double_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:      
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            return
        
        if isinstance(data, str):
            uri = item.data(0, URI_USER_ROLE)
            if uri:
                topic_ops.open_web_site(uri)
            else:
                topic_ops.add_topic(data)
        else:
            logger.warning(f"Unexpected data type for the double-clicked item: {type(data)}")
    
    def _on_catalog_tree_context_menu(self, position: QtCore.QPoint) -> None:
        item = self.catalog_tree_widget.itemAt(position)
        if item is None:
            return
        
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            return
        
        menu = context_menus.TopicContextMenu(data, self)
        viewport = self.catalog_tree_widget.viewport()
        if not viewport:
            logger.warning("Viewport not found for the catalog tree widget.")
            return
        
        menu.exec(viewport.mapToGlobal(position))
    
    def _start_search_timer(self, text: str) -> None:
        if text.strip() == "" and self._searching:
            self._timer.stop()
            self.set_searching(False)
            self._search_highlight_delegate.clear_search_text()
        
        if not text or len(text) < 2:
            self._timer.stop()
            return
        
        self.set_searching(True)
        self._search_highlight_delegate.set_search_tokens(search_index.tokenize(text))
        self._timer.start()
    
    def _on_item_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        item.setIcon(0, icons.get_icon(icons.IconKey.FOLDER_OPEN))
        self._expanded_items.add(item.data(0, QtCore.Qt.ItemDataRole.UserRole))
    
    def _on_item_collapsed(self, item: QtWidgets.QTreeWidgetItem) -> None:
        item.setIcon(0, icons.get_icon(icons.IconKey.FOLDER_CLOSED))
        self._expanded_items.discard(item.data(0, QtCore.Qt.ItemDataRole.UserRole))
