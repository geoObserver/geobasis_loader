"""Settings dialog for the GeoBasis Loader QGIS plugin.

Provides the SettingsDialog class for configuring server endpoints, CRS behavior,
and per-layer visibility, loading, and favorite properties.
"""

from __future__ import annotations

import os

from qgis.core import QgsSettings
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QShowEvent

from .. import config
from ..catalog_manager import CatalogManager

SETTINGS_DIALOG = uic.loadUiType(os.path.join(os.path.dirname(__file__), "design_files", "settings_dialog.ui"))[0]
FAVORITE_CHECKBOX_COL = 1
VISIBILITY_CHECKBOX_COL = 2
LOADING_CHECKBOX_COL = 3

class SettingsDialog(QtWidgets.QDialog, SETTINGS_DIALOG):
    """Dialog for managing plugin settings and per-layer properties.

    Allows the user to choose a server endpoint, toggle automatic CRS selection,
    and configure favorite, visibility, and loading states for each catalog entry
    via a tree widget.
    """

    def __init__(self, parent = None):
        """Initialize the settings dialog and connect UI signals.

        Args:
            parent: Optional parent widget for the dialog.

        """
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        # Store all tree view items for each exec_ -> Dont go through tree recursively to get check status of each item
        self._items: list[QtWidgets.QTreeWidgetItem] = []
        self._current_catalog: dict = {}

        # Visibility tree buttons/actions
        self.expand_button.clicked.connect(self.visibility_tree.expandAll)
        self.collapse_button.clicked.connect(self.visibility_tree.collapseAll)
        self.check_visibility_button.clicked.connect(
            lambda: self.set_check_state_all_items(
                VISIBILITY_CHECKBOX_COL, Qt.CheckState.Checked))
        self.uncheck_visibility_button.clicked.connect(
            lambda: self.set_check_state_all_items(
                VISIBILITY_CHECKBOX_COL, Qt.CheckState.Unchecked))
        self.check_loading_button.clicked.connect(
            lambda: self.set_check_state_all_items(
                LOADING_CHECKBOX_COL, Qt.CheckState.Checked))
        self.uncheck_loading_button.clicked.connect(
            lambda: self.set_check_state_all_items(
                LOADING_CHECKBOX_COL, Qt.CheckState.Unchecked))

        # Button box
        self.button_box.accepted.connect(self.confirm_settings)
        self.reset_button.clicked.connect(self.restore_defaults)

        # IntelliSense
        self.visibility_tree: QtWidgets.QTreeWidget = self.visibility_tree
        self.server_button_group: QtWidgets.QButtonGroup = self.server_button_group
        self.automatic_crs_checkbox: QtWidgets.QCheckBox = self.automatic_crs_checkbox

    def setup(self):
        """Configure column widths of the visibility tree widget based on available space."""
        available_width = self.visibility_tree.width()
        checkbox_col_width = 80
        name_col_width = available_width - self.visibility_tree.verticalScrollBar().width() - 3 * checkbox_col_width                               # type: ignore
        self.visibility_tree.setColumnWidth(0, name_col_width)
        self.visibility_tree.setColumnWidth(FAVORITE_CHECKBOX_COL, checkbox_col_width)
        self.visibility_tree.setColumnWidth(VISIBILITY_CHECKBOX_COL, checkbox_col_width)
        self.visibility_tree.setColumnWidth(LOADING_CHECKBOX_COL, checkbox_col_width)

    def showEvent(self, a0: QShowEvent | None) -> None:
        """Handle the dialog show event by refreshing layout and settings.

        Args:
            a0: The show event provided by Qt.

        """
        super().showEvent(a0)
        self.setup()
        self.set_settings()

    def set_settings(self):
        """Populate the dialog with current catalog data and persisted QgsSettings."""
        def _add_visibility_entry(data: dict, parent: QtWidgets.QTreeWidgetItem | None = None):
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
                        # Favorite
                        checked = (
                            Qt.CheckState.Checked
                            if value.get(config.InternalProperties.FAVORITE, False)
                            else Qt.CheckState.Unchecked
                        )
                        item.setCheckState(FAVORITE_CHECKBOX_COL, checked)
                        # Visibility
                        checked = (
                            Qt.CheckState.Checked
                            if value.get(config.InternalProperties.VISIBILITY, True)
                            else Qt.CheckState.Unchecked
                        )
                        item.setCheckState(VISIBILITY_CHECKBOX_COL, checked)
                        # Loading
                        checked = (
                            Qt.CheckState.Checked
                            if value.get(config.InternalProperties.LOADING, True)
                            else Qt.CheckState.Unchecked
                        )
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
        automatic_crs = qgs_settings.value(config.AUTOMATIC_CRS_SETTINGS_KEY, False, bool)
        self.automatic_crs_checkbox.setChecked(automatic_crs)

    def set_check_state_all_items(self, column: int, state: Qt.CheckState) -> None:
        """Set the check state of all tree items in a given column.

        Args:
            column: Column index of the checkbox to update.
            state: The desired ``Qt.CheckState`` (Checked or Unchecked).

        """
        for item in self._items:
            item.setCheckState(column, state)
        viewport = self.visibility_tree.viewport()
        if viewport:
            viewport.update()

    def restore_defaults(self) -> None:
        """Reset all settings to factory defaults after user confirmation."""
        prompt_reply = QtWidgets.QMessageBox.question(
            self, "Werkseinstellungen",
            "Sollen alle Einstellungen zurückgesetzt werden?",
        )
        if prompt_reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # Visibility Tree
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
        qgs_settings = QgsSettings()
        qgs_settings.setValue(config.AUTOMATIC_CRS_SETTINGS_KEY, False)

    def confirm_settings(self) -> None:
        """Persist all current dialog values to QgsSettings and the catalog manager."""
        # Global settings
        qgs_settings = QgsSettings()
        checked_button = self.server_button_group.checkedButton()
        if checked_button:
            server_index = checked_button.property("server")
            qgs_settings.setValue(config.SERVERS_SETTINGS_KEY, server_index)

        automatic_crs = self.automatic_crs_checkbox.isChecked()
        qgs_settings.setValue(config.AUTOMATIC_CRS_SETTINGS_KEY, automatic_crs)

        # Layer settings
        check_status = {
            config.InternalProperties.FAVORITE: {},
            config.InternalProperties.VISIBILITY: {},
            config.InternalProperties.LOADING: {},
        }

        for item in self._items:
            path: str = item.data(0, Qt.ItemDataRole.UserRole)
            favorite_state = item.checkState(FAVORITE_CHECKBOX_COL)
            if favorite_state == Qt.CheckState.Unchecked:
                check_status[config.InternalProperties.FAVORITE][path] = False
            else:
                check_status[config.InternalProperties.FAVORITE][path] = True

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
        """Clear internal state and remove all items from the visibility tree."""
        self._current_catalog = {}
        self._items = []
        self.visibility_tree.clear()
