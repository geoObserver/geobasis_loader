import os
from typing import Union, Optional
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QShowEvent
from qgis.core import QgsSettings
from ..catalog_manager import CatalogManager
from .. import config
from ..property_manager import singleton as PropertyManager
from ..utils import catalog_types

SETTINGS_DIALOG = uic.loadUiType(os.path.join(os.path.dirname(__file__), "design_files", "settings_dialog.ui"))[0]
VISIBILITY_CHECKBOX_COL = 1
LOADING_CHECKBOX_COL = 2

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        
        # Store all tree view items for each exec -> Dont go through tree recursively to get check status of each item
        self._items: list[QtWidgets.QTreeWidgetItem] = []
        self._current_catalog = {}
        
        self.setupUi(self)
        
        # Visibility tree buttons/actions
        self.expand_button.clicked.connect(self.layer_settings_tree.expandAll)
        self.collapse_button.clicked.connect(self.layer_settings_tree.collapseAll)
        self.check_visibility_button.clicked.connect(lambda: self.set_check_state_all_items(VISIBILITY_CHECKBOX_COL, Qt.CheckState.Checked))
        self.uncheck_visibility_button.clicked.connect(lambda: self.set_check_state_all_items(VISIBILITY_CHECKBOX_COL, Qt.CheckState.Unchecked))
        self.check_loading_button.clicked.connect(lambda: self.set_check_state_all_items(LOADING_CHECKBOX_COL, Qt.CheckState.Checked))
        self.uncheck_loading_button.clicked.connect(lambda: self.set_check_state_all_items(LOADING_CHECKBOX_COL, Qt.CheckState.Unchecked))
        
        # Button box
        self.button_box.accepted.connect(self.confirm_settings)
        self.reset_button.clicked.connect(self.restore_defaults)
        
        # IntelliSense
        self.layer_settings_tree: QtWidgets.QTreeWidget = self.layer_settings_tree
        self.server_button_group: QtWidgets.QButtonGroup = self.server_button_group
        self.automatic_crs_checkbox: QtWidgets.QCheckBox = self.automatic_crs_checkbox
    
    def setup(self):
        available_width = self.layer_settings_tree.width()
        checkbox_col_width = 80
        name_col_width = available_width - self.layer_settings_tree.verticalScrollBar().width() - 2 * checkbox_col_width                               # type: ignore
        self.layer_settings_tree.setColumnWidth(0, name_col_width)
        self.layer_settings_tree.setColumnWidth(1, checkbox_col_width)
        self.layer_settings_tree.setColumnWidth(2, checkbox_col_width)

    def showEvent(self, a0: Optional[QShowEvent]) -> None:
        super().showEvent(a0)
        self.setup()
        self.set_settings()
       
    def set_settings(self):
        def _add_entry(data: catalog_types.BasicEntry, parent: Union[QtWidgets.QTreeWidgetItem, QtWidgets.QTreeWidget]) -> QtWidgets.QTreeWidgetItem:            
            item = QtWidgets.QTreeWidgetItem(parent)
            item.setText(0, data.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            
            # Visibility
            checked = Qt.CheckState.Checked if data.properties.visible else Qt.CheckState.Unchecked
            item.setCheckState(VISIBILITY_CHECKBOX_COL, checked)
            # Loading
            checked = Qt.CheckState.Checked if data.properties.enabled else Qt.CheckState.Unchecked
            item.setCheckState(LOADING_CHECKBOX_COL, checked)
            
            item.setData(0, Qt.ItemDataRole.UserRole, data.path)
            self._items.append(item)
        
            return item
        
        self.clear_data()
        self._current_catalog = CatalogManager.get_current_catalog()
        if self._current_catalog is None or isinstance(self._current_catalog, list):
            return
        
        # Properties Tree
        for region in self._current_catalog.get_regions():
            region_item = _add_entry(region, self.layer_settings_tree)
            for topic in region.get_topics():
                topic_item = _add_entry(topic, region_item)
                if isinstance(topic, catalog_types.TopicGroup):
                    for subtopic in topic.get_subtopics():
                        subtopic_item = _add_entry(subtopic, topic_item)
        
        # Global Settings
        qgs_settings = QgsSettings()
        server = qgs_settings.value(config.QgsSettingsKeys.SERVERS, 0, type=int)
        for button in self.server_button_group.buttons():
            if button.property("server") == server:
                button.setChecked(True)
            else:
                button.setChecked(False)
        automatic_crs = qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, bool)
        self.automatic_crs_checkbox.setChecked(automatic_crs)
        
    def set_check_state_all_items(self, column: int, state: Qt.CheckState) -> None:
        for item in self._items:
            item.setCheckState(column, state)
        viewport = self.layer_settings_tree.viewport()
        if viewport:
            viewport.update()
    
    def restore_defaults(self) -> None:
        prompt_reply = QtWidgets.QMessageBox.question(self, "Werkseinstellungen", "Sollen alle Einstellungen zurückgesetzt werden?")
        if prompt_reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        
        # Visibility Tree
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
        qgs_settings = QgsSettings()        
        qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, False)
    
    def confirm_settings(self) -> None:
        # Global settings
        qgs_settings = QgsSettings()
        checked_button = self.server_button_group.checkedButton()
        if checked_button:
            server_index = checked_button.property("server")
            qgs_settings.setValue(config.QgsSettingsKeys.SERVERS, server_index)
        
        automatic_crs = self.automatic_crs_checkbox.isChecked()
        qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, automatic_crs)
        
        # Layer settings
        for item in self._items:
            path: str = item.data(0, Qt.ItemDataRole.UserRole)
            visibility_state = item.checkState(VISIBILITY_CHECKBOX_COL)
            # Check whether it's unchecked or not due to tristate -> Negate it
            is_visible = not visibility_state == Qt.CheckState.Unchecked
            PropertyManager.set_visibility(path, is_visible)
                
            loading_state = item.checkState(LOADING_CHECKBOX_COL)
            # Check whether it's unchecked or not due to tristate -> Negate it
            is_enabled = not loading_state == Qt.CheckState.Unchecked
            PropertyManager.set_enabled(path, is_enabled)
        
        PropertyManager.save_all()
        self.clear_data()
        
    def clear_data(self) -> None:
        self._current_catalog = {}
        self._items = []
        self.layer_settings_tree.clear()