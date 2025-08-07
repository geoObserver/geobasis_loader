import os
from typing import Union
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QShowEvent
from qgis.core import QgsSettings
from ..catalog_manager import CatalogManager
from .. import config

SETTINGS_DIALOG = uic.loadUiType(os.path.join(os.path.dirname(__file__), f"settings_dialog.ui"))[0]
VISIBILITY_CHECKBOX_COL = 1
LOADING_CHECKBOX_COL = 2

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    # Store all tree view items for each exec_ -> Dont go through tree recursively to get check status of each item
    _items: list[QtWidgets.QTreeWidgetItem] = []
    _current_catalog = {}
    
    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        
        # Visibility tree buttons/actions
        self.expand_button.clicked.connect(self.visibility_tree.expandAll)
        self.collapse_button.clicked.connect(self.visibility_tree.collapseAll)
        self.check_button.clicked.connect(lambda: self.set_check_state_all_items(Qt.CheckState.Checked))
        self.uncheck_button.clicked.connect(lambda: self.set_check_state_all_items(Qt.CheckState.Unchecked))
        
        # Button box
        self.button_box.accepted.connect(self.confirm_settings)
        self.reset_button.clicked.connect(self.restore_defaults)
        
        # IntelliSense
        self.visibility_tree: QtWidgets.QTreeWidget = self.visibility_tree
        self.server_button_group: QtWidgets.QButtonGroup = self.server_button_group
    
    def setup(self):
        available_width = self.visibility_tree.width()
        checkbox_col_width = 80
        name_col_width = available_width - self.visibility_tree.verticalScrollBar().width() - 2 * checkbox_col_width                               # type: ignore
        self.visibility_tree.setColumnWidth(0, name_col_width)
        self.visibility_tree.setColumnWidth(1, checkbox_col_width)
        self.visibility_tree.setColumnWidth(2, checkbox_col_width)

    def showEvent(self, a0: Union[QShowEvent, None]) -> None:
        super().showEvent(a0)
        self.setup()
        self.set_settings()
       
    def set_settings(self):
        def _add_visibility_entry(data: dict, parent: Union[QtWidgets.QTreeWidgetItem, None] = None):
            name_key = "name"
            if parent is None:
                parent = self.visibility_tree
                name_key = "menu"
            
            for key, value in data.items():   
                if isinstance(value, dict):
                    if key == "themen" or key == "layers":
                        item = parent
                    else:
                        item = QtWidgets.QTreeWidgetItem(parent)
                        item.setText(0, value[name_key])
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                        # Visibility
                        checked = Qt.CheckState.Checked if value.get(config.InternalProperties.VISIBILITY, True) else Qt.CheckState.Unchecked
                        item.setCheckState(VISIBILITY_CHECKBOX_COL, checked)
                        # Loading
                        checked = Qt.CheckState.Checked if value.get(config.InternalProperties.LOADING, True) else Qt.CheckState.Unchecked
                        item.setCheckState(LOADING_CHECKBOX_COL, checked)
                        item.setData(0, Qt.ItemDataRole.UserRole, value.get(config.InternalProperties.PATH, None))
                        self._items.append(item)
                    
                    _add_visibility_entry(value, item)                    
        
        self.clear_data()
        current_catalog = CatalogManager.get_current_catalog()
        if current_catalog is None:
            return
        
        # Visibility Tree
        self._current_catalog = dict(current_catalog)
        _add_visibility_entry(self._current_catalog)
        
        # Global Settings
        qgs_settings = QgsSettings()
        server = qgs_settings.value(config.SERVERS_SETTINGS_KEY, 0, type=int)
        for button in self.server_button_group.buttons():
            if button.property("server") == server:
                button.setChecked(True)
            else:
                button.setChecked(False)
        
    def set_check_state_all_items(self, state: Qt.CheckState) -> None:
        for item in self._items:
            item.setCheckState(VISIBILITY_CHECKBOX_COL, state)
            item.setCheckState(LOADING_CHECKBOX_COL, state)
        viewport = self.visibility_tree.viewport()
        if viewport:
            viewport.update()
    
    def restore_defaults(self) -> None:
        prompt_reply = QtWidgets.QMessageBox.question(self, "Werkseinstellungen", "Sollen alle Einstellungen zurückgesetzt werden?")
        if prompt_reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        
        # Visibility Tree
        self.set_check_state_all_items(Qt.CheckState.Checked)
        
        # Global Settings
        # Server Select
        for button in self.server_button_group.buttons():
            if button.property("server") == 0:
                button.setChecked(True)
            else:
                button.setChecked(False)
    
    def confirm_settings(self) -> None:
        qgs_settings = QgsSettings()
        checked_button = self.server_button_group.checkedButton()
        if checked_button:
            server_index = checked_button.property("server")
            qgs_settings.setValue(config.SERVERS_SETTINGS_KEY, server_index)
        
        check_status = {
            config.InternalProperties.VISIBILITY: {},
            config.InternalProperties.LOADING: {},
        }
                
        for item in self._items:
            path: str = item.data(0, Qt.ItemDataRole.UserRole)
            visibility_state = item.checkState(VISIBILITY_CHECKBOX_COL)
            if visibility_state == Qt.CheckState.Unchecked:
                check_status[config.InternalProperties.VISIBILITY][path] = False
            else:
                check_status[config.InternalProperties.VISIBILITY][path] = True
                
            loading_state = item.checkState(LOADING_CHECKBOX_COL)
            if loading_state == Qt.CheckState.Unchecked:
                check_status[config.InternalProperties.LOADING][path] = False
            else:
                check_status[config.InternalProperties.LOADING][path] = True
        
        CatalogManager.update_internal_properties(check_status)
        self.clear_data()
        
    def clear_data(self) -> None:
        self._current_catalog = {}
        self._items = []
        self.visibility_tree.clear()