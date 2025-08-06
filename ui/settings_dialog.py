import os
from typing import Union
from qgis.PyQt import uic, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QShowEvent
from ..catalog_manager import CatalogManager
from .. import config

SETTINGS_DIALOG = uic.loadUiType(os.path.join(os.path.dirname(__file__), f"settings_dialog.ui"))[0]
VISIBILITY_CHECKBOX_COL = 0

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    # Store all tree view items for each exec_ -> Dont go through tree recursively to get check status of each item
    _items: list[QtWidgets.QTreeWidgetItem] = []
    _current_catalog = {}
    
    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        
        self.expand_button.clicked.connect(self.visibility_tree.expandAll)
        self.collapse_button.clicked.connect(self.visibility_tree.collapseAll)
        self.check_button.clicked.connect(lambda: self.set_check_state_all_items(Qt.CheckState.Checked))
        self.uncheck_button.clicked.connect(lambda: self.set_check_state_all_items(Qt.CheckState.Unchecked))
        
        self.button_box.accepted.connect(self.confirm_settings)
        
        # IntelliSense
        self.visibility_tree: QtWidgets.QTreeWidget = self.visibility_tree
    
    def setup(self):
        available_width = self.visibility_tree.width()
        checkbox_col_width = 80
        name_col_width = available_width - self.visibility_tree.verticalScrollBar().width() - 2 * checkbox_col_width                               # type: ignore
        self.visibility_tree.setColumnWidth(0, name_col_width)
        self.visibility_tree.setColumnWidth(1, checkbox_col_width)
        self.visibility_tree.setColumnWidth(2, checkbox_col_width)
        # self.visibility_tree.setHeaderLabels(["Thema", "Sichtbarkeit", "Laden"])
    
    def showEvent(self, a0: Union[QShowEvent, None]) -> None:
        super().showEvent(a0)
        self.setup()
        self.set_visibility_tree_data()
       
    def set_visibility_tree_data(self):
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
                        checked = Qt.CheckState.Checked if value.get(config.InternalProperties.VISIBILITY, True) else Qt.CheckState.Unchecked
                        item.setCheckState(VISIBILITY_CHECKBOX_COL, checked)
                        item.setData(0, Qt.ItemDataRole.UserRole, value.get(config.InternalProperties.PATH, None))
                        self._items.append(item)
                    
                    _add_visibility_entry(value, item)                    
        
        self.clear_data()
        current_catalog = CatalogManager.get_current_catalog()
        if current_catalog is None:
            return
        
        self._current_catalog = dict(current_catalog)
        _add_visibility_entry(self._current_catalog)
        
    def set_check_state_all_items(self, state: Qt.CheckState) -> None:
        for item in self._items:
            item.setCheckState(VISIBILITY_CHECKBOX_COL, state)
        viewport = self.visibility_tree.viewport()
        if viewport:
            viewport.update()
    
    def confirm_settings(self) -> None:
        check_status = []
                
        for item in self._items:
            state = item.checkState(VISIBILITY_CHECKBOX_COL)
            path: str = item.data(0, Qt.ItemDataRole.UserRole)
            if state == Qt.CheckState.Unchecked:
                check_status.append((path, False))
            else:
                check_status.append((path, True))
        
        CatalogManager.update_internal_properties(check_status, config.InternalProperties.VISIBILITY)
        self.clear_data()
        
    def clear_data(self) -> None:
        self._current_catalog = {}
        self._items = []
        self.visibility_tree.clear()