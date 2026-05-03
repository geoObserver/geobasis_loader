import os
from typing import Union, Optional
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QShowEvent
from qgis.core import QgsSettings
from .. import config
from ..services import registry
from ..models import catalog_types
# FIXME
from . import icons as Icons
from ..utils import custom_logger

SETTINGS_DIALOG = uic.loadUiType(os.path.join(os.path.dirname(__file__), "design_files", "settings_dialog.ui"))[0]
FAVORITE_CHECKBOX_COL = 1
VISIBILITY_CHECKBOX_COL = 2
LOADING_CHECKBOX_COL = 3

logger = custom_logger.get_logger(__file__)

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        
        # Store all tree view items for each exec -> Dont go through tree recursively to get check status of each item
        self._items: list[QtWidgets.QTreeWidgetItem] = []
        self._current_catalog = None
        self._updating_items = False
        self._qgs_settings = QgsSettings()
        
        self.setupUi(self)
        
        # Topic settings tree
        self.layer_settings_tree.itemChanged.connect(self.on_item_changed)
        
        # Visibility tree buttons/actions
        self.expand_button.clicked.connect(self.layer_settings_tree.expandAll)
        self.collapse_button.clicked.connect(self.layer_settings_tree.collapseAll)
        self.check_visibility_button.clicked.connect(lambda: self.set_check_state_all_items(VISIBILITY_CHECKBOX_COL, Qt.CheckState.Checked))
        self.uncheck_visibility_button.clicked.connect(lambda: self.set_check_state_all_items(VISIBILITY_CHECKBOX_COL, Qt.CheckState.Unchecked))
        self.check_loading_button.clicked.connect(lambda: self.set_check_state_all_items(LOADING_CHECKBOX_COL, Qt.CheckState.Checked))
        self.uncheck_loading_button.clicked.connect(lambda: self.set_check_state_all_items(LOADING_CHECKBOX_COL, Qt.CheckState.Unchecked))
        
        self.layer_settings_tree.itemExpanded.connect(self._on_item_expanded)
        self.layer_settings_tree.itemCollapsed.connect(self._on_item_collapsed)
        self.accepted.connect(self.confirm_settings)
        self.reset_button.clicked.connect(self.restore_defaults)
        
        # IntelliSense
        self.layer_settings_tree: QtWidgets.QTreeWidget = self.layer_settings_tree
        self.server_button_group: QtWidgets.QButtonGroup = self.server_button_group
        self.automatic_crs_checkbox: QtWidgets.QCheckBox = self.automatic_crs_checkbox
    
    def _set_state_of_children(self, item: QtWidgets.QTreeWidgetItem, column: int, state: Qt.CheckState) -> None:
        for i in range(item.childCount()):
            child = item.child(i)
            if child is None:
                continue
            
            self._set_state(child, column, state)
            self._set_state_of_children(child, column, state)
    
    def _set_state_of_parents(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        parent = item.parent()
        if parent is None:
            return
        
        has_checked = False
        has_unchecked = False
        
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child is None:
                continue
            
            state = self._get_state(child, column)
            if state == Qt.CheckState.Checked:
                has_checked = True
            
            if state == Qt.CheckState.Unchecked:
                has_unchecked = True
                
            if state == Qt.CheckState.PartiallyChecked:
                has_checked = True
                has_unchecked = True
            
            # Break for-loop if both states are observed in children since further probing is unnecessary
            if has_checked and has_unchecked:
                break

        if column == FAVORITE_CHECKBOX_COL:
            # Keep explicitly favorited groups checked. Otherwise favorites are an
            # indicator state: partial when any descendant is favorited.
            if self._get_state(parent, column) == Qt.CheckState.Checked:
                new_parent_state = Qt.CheckState.Checked
            elif has_checked:
                new_parent_state = Qt.CheckState.PartiallyChecked
            else:
                new_parent_state = Qt.CheckState.Unchecked
        else:
            if has_checked and not has_unchecked:
                new_parent_state = Qt.CheckState.Checked
            elif not has_checked and has_unchecked:
                new_parent_state = Qt.CheckState.Unchecked
            else:
                new_parent_state = Qt.CheckState.PartiallyChecked
            
        self._set_state(parent, column, new_parent_state)
        self._set_state_of_parents(parent, column)
    
    def on_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if self._updating_items or column == 0:
            return
        
        state = self._get_state(item, column)
        has_checked, has_unchecked = self._get_child_state_summary(item, column)
        if state == Qt.CheckState.PartiallyChecked and (item.childCount() == 0 or not (has_checked and has_unchecked)):
            # Prevent users from setting partial states directly.
            self._updating_items = True
            normalized_state = Qt.CheckState.Checked if has_checked else Qt.CheckState.Unchecked
            self._set_state(item, column, normalized_state)
            self._updating_items = False
            return

        self._updating_items = True
        if column not in (VISIBILITY_CHECKBOX_COL, LOADING_CHECKBOX_COL):
            # Favorite groups can be checked independently from their children.
            # If a group is unchecked, fall back to partial when descendants are favorited.
            if item.childCount() > 0 and self._get_state(item, column) == Qt.CheckState.Unchecked:
                has_favorited_child = False
                for i in range(item.childCount()):
                    child = item.child(i)
                    if child is None:
                        continue
                    if self._get_state(child, column) != Qt.CheckState.Unchecked:
                        has_favorited_child = True
                        break
                if has_favorited_child:
                    self._set_state(item, column, Qt.CheckState.PartiallyChecked)

            self._set_state_of_parents(item, column)
        else:
            state = self._get_state(item, column)
            self._set_state_of_children(item, column, state)
            self._set_state_of_parents(item, column)
        self._updating_items = False
    
    def _get_checkbox(self, item: QtWidgets.QTreeWidgetItem, column: int) -> QtWidgets.QCheckBox:
        checkbox = self.layer_settings_tree.itemWidget(item, column)
        if not isinstance(checkbox, QtWidgets.QCheckBox):
            raise TypeError(f"No checkbox widget for column {column}")
        return checkbox

    def _get_state(self, item: QtWidgets.QTreeWidgetItem, column: int) -> Qt.CheckState:
        return self._get_checkbox(item, column).checkState()

    def _set_state(self, item: QtWidgets.QTreeWidgetItem, column: int, state: Qt.CheckState) -> None:
        checkbox = self._get_checkbox(item, column)
        if column == FAVORITE_CHECKBOX_COL:
            checkbox.setTristate(state == Qt.CheckState.PartiallyChecked)
        checkbox.setCheckState(state)

    def _get_child_state_summary(self, item: QtWidgets.QTreeWidgetItem, column: int) -> tuple[bool, bool]:
        has_checked = False
        has_unchecked = False
        for i in range(item.childCount()):
            child = item.child(i)
            if child is None:
                continue
            state = self._get_state(child, column)
            if state == Qt.CheckState.Checked:
                has_checked = True
            elif state == Qt.CheckState.Unchecked:
                has_unchecked = True
            else:
                has_checked = True
                has_unchecked = True
            if has_checked and has_unchecked:
                break
        return has_checked, has_unchecked
    
    def _on_item_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        item_icon = item.icon(0)
        folder_closed_icon = Icons.get_icon(Icons.IconKey.FOLDER_CLOSED)
        if item_icon.cacheKey() == folder_closed_icon.cacheKey():
            item.setIcon(0, Icons.get_icon(Icons.IconKey.FOLDER_OPEN))
    
    def _on_item_collapsed(self, item: QtWidgets.QTreeWidgetItem) -> None:
        item_icon = item.icon(0)
        folder_open_icon = Icons.get_icon(Icons.IconKey.FOLDER_OPEN)
        if item_icon.cacheKey() == folder_open_icon.cacheKey():
            item.setIcon(0, Icons.get_icon(Icons.IconKey.FOLDER_CLOSED))
        
    def setup(self):
        available_width = self.layer_settings_tree.width()
        checkbox_col_width = 80
        name_col_width = available_width - self.layer_settings_tree.verticalScrollBar().width() - 3 * checkbox_col_width                               # type: ignore
        self.layer_settings_tree.setColumnWidth(0, name_col_width)
        self.layer_settings_tree.setColumnWidth(1, checkbox_col_width)
        self.layer_settings_tree.setColumnWidth(2, checkbox_col_width)
        self.layer_settings_tree.setColumnWidth(3, checkbox_col_width)

    def showEvent(self, a0: Optional[QShowEvent]) -> None:
        super().showEvent(a0)
        self.setup()
       
    def set_settings(self, catalog: catalog_types.Catalog) -> None:
        def _add_entry(data: catalog_types.BasicEntry, parent: Union[QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidget]) -> QtWidgets.QTreeWidgetItem:            
            item = QtWidgets.QTreeWidgetItem(parent)
            if isinstance(data, catalog_types.Region):
                icon = Icons.get_icon(Icons.IconKey.FOLDER_CLOSED)
            elif isinstance(data, catalog_types.Topic):
                icon = Icons.get_icon(data.topic_type)
            elif isinstance(data, catalog_types.TopicGroup):
                icon = Icons.get_icon(Icons.IconKey.FOLDER_CLOSED)
            elif isinstance(data, catalog_types.TopicCombination):
                icon = Icons.get_icon(Icons.IconKey.COMBINATION_ADD)
            else:
                logger.critical(f"Ungültiger Typ für Knoten: {type(data)}")
                icon = QIcon()
            
            item.setIcon(0, icon)
            item.setText(0, data.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            
            # Favorite
            checked = Qt.CheckState.Checked if data.properties.favorite else Qt.CheckState.Unchecked
            favorite_checkbox = QtWidgets.QCheckBox()
            favorite_checkbox.setTristate(False)
            favorite_checkbox.setCheckState(checked)
            favorite_checkbox.stateChanged.connect(lambda _=None, i=item, c=FAVORITE_CHECKBOX_COL: self.on_item_changed(i, c))
            self.layer_settings_tree.setItemWidget(item, FAVORITE_CHECKBOX_COL, favorite_checkbox)
            # Visibility
            checked = Qt.CheckState.Checked if data.properties.visible else Qt.CheckState.Unchecked
            visibility_checkbox = QtWidgets.QCheckBox()
            visibility_checkbox.setCheckState(checked)
            visibility_checkbox.stateChanged.connect(lambda _=None, i=item, c=VISIBILITY_CHECKBOX_COL: self.on_item_changed(i, c))
            self.layer_settings_tree.setItemWidget(item, VISIBILITY_CHECKBOX_COL, visibility_checkbox)
            # Loading
            checked = Qt.CheckState.Checked if data.properties.enabled else Qt.CheckState.Unchecked
            loading_checkbox = QtWidgets.QCheckBox()
            loading_checkbox.setCheckState(checked)
            loading_checkbox.stateChanged.connect(lambda _=None, i=item, c=LOADING_CHECKBOX_COL: self.on_item_changed(i, c))
            self.layer_settings_tree.setItemWidget(item, LOADING_CHECKBOX_COL, loading_checkbox)
            
            item.setData(0, Qt.ItemDataRole.UserRole, data.path)
            self._items.append(item)
        
            return item
        
        self.clear_data()
        if not isinstance(catalog, catalog_types.Catalog):
            logger.critical(f"Ungültiger Typ für Katalog: {type(catalog)}")
            return
        
        self._current_catalog = catalog        
        self._updating_items = True
        
        # Properties Tree
        for region in self._current_catalog.get_regions():
            region_item = _add_entry(region, self.layer_settings_tree)
            for topic in region.get_topics():
                topic_item = _add_entry(topic, region_item)
                if isinstance(topic, catalog_types.TopicGroup):
                    for subtopic in topic.get_subtopics():
                        _ = _add_entry(subtopic, topic_item)

        # Sync parent favorite states after initial population while signals are suppressed.
        # FIXME: Kinda slow, future performance increase needed
        for item in self._items:
            if item.childCount() == 0:
                self._set_state_of_parents(item, FAVORITE_CHECKBOX_COL)
                self._set_state_of_parents(item, VISIBILITY_CHECKBOX_COL)
                self._set_state_of_parents(item, LOADING_CHECKBOX_COL)
        
        self._updating_items = False
        
        # Global Settings
        server = self._qgs_settings.value(config.QgsSettingsKeys.SERVERS, 0, type=int)
        for button in self.server_button_group.buttons():
            if button.property("server") == server:
                button.setChecked(True)
            else:
                button.setChecked(False)
        automatic_crs = self._qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, bool)
        self.automatic_crs_checkbox.setChecked(automatic_crs)
        
    def set_check_state_all_items(self, column: int, state: Qt.CheckState) -> None:
        self._updating_items = True
        for item in self._items:
            self._set_state(item, column, state)
        self._updating_items = False
        viewport = self.layer_settings_tree.viewport()
        if viewport:
            viewport.update()
    
    def restore_defaults(self) -> None:
        prompt_reply = QtWidgets.QMessageBox.question(self, "Werkseinstellungen", "Sollen alle Einstellungen zurückgesetzt werden?")
        if prompt_reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        
        # Topics Tree
        self.set_check_state_all_items(FAVORITE_CHECKBOX_COL, Qt.CheckState.Unchecked)
        self.set_check_state_all_items(VISIBILITY_CHECKBOX_COL, Qt.CheckState.Checked)
        self.set_check_state_all_items(LOADING_CHECKBOX_COL, Qt.CheckState.Checked)
        
        # Global Settings
        # Server Select
        for button in self.server_button_group.buttons():
            if button.property("server") == 0:
                button.setChecked(True)
            else:
                button.setChecked(False)
                
        # Automatic CRS
        self.automatic_crs_checkbox.setChecked(False)
    
    def confirm_settings(self) -> None:
        # Global settings
        checked_button = self.server_button_group.checkedButton()
        if checked_button:
            server_index = checked_button.property("server")
            self._qgs_settings.setValue(config.QgsSettingsKeys.SERVERS, server_index)
        
        automatic_crs = self.automatic_crs_checkbox.isChecked()
        self._qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, automatic_crs)
        
        # Layer settings
        for item in self._items:
            path: str = item.data(0, Qt.ItemDataRole.UserRole)
            favorite_state = self._get_state(item, FAVORITE_CHECKBOX_COL)
            # Check whether it's unchecked or not due to tristate -> Negate it and ignore partially checked
            is_favorite = not favorite_state == Qt.CheckState.Unchecked and favorite_state != Qt.CheckState.PartiallyChecked
            if "/" in path:     # Skip regions, since it wouldn't make sense
                registry.property_manager.set_favorite(path, is_favorite)
            
            visibility_state = self._get_state(item, VISIBILITY_CHECKBOX_COL)
            # Check whether it's unchecked or not due to tristate -> Negate it
            is_visible = not visibility_state == Qt.CheckState.Unchecked
            registry.property_manager.set_visibility(path, is_visible)
                
            loading_state = self._get_state(item, LOADING_CHECKBOX_COL)
            # Check whether it's unchecked or not due to tristate -> Negate it
            is_enabled = not loading_state == Qt.CheckState.Unchecked
            registry.property_manager.set_enabled(path, is_enabled)
        
        registry.property_manager.save_all()
        self.clear_data()
        
    def clear_data(self) -> None:
        self._current_catalog = {}
        self._items = []
        self.layer_settings_tree.clear()

