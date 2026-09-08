from typing import Optional, Union

from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.core import QgsSettings
from ...core import events
from ... import config
from ...utils import custom_logger

logger = custom_logger.get_logger(__name__)

SETTINGS_WIDGET = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "general_settings_widget.ui")[0]

class SettingsWidget(QtWidgets.QWidget, SETTINGS_WIDGET):
    def __init__(self, parent: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self._qgs_settings = QgsSettings()
        self._automatic_save_settings = True
        self.set_settings()
        
        # Type hints for UI elements
        self.server_selection_button_group: QtWidgets.QButtonGroup = self.server_selection_button_group
        self.automatic_crs_check_box: QtWidgets.QCheckBox = self.automatic_crs_check_box
        self.advanced_settings_group_box: QtWidgets.QGroupBox = self.advanced_settings_group_box
        self.open_advanced_settings_button: QtWidgets.QPushButton = self.open_advanced_settings_button
    
        # Connect slots
        self.server_selection_button_group.buttonClicked.connect(self._on_server_selection_clicked)
        self.automatic_crs_check_box.clicked.connect(self._on_automatic_crs_check_box_changed)          # Clicked -> Only user interaction, not programmatic changes
        self.open_advanced_settings_button.clicked.connect(self._on_advanced_settings_button_clicked)
        events.connect_server_selection_changed(self._on_server_selection_changed)
        events.connect_automatic_crs_changed(self._on_automatic_crs_changed)

    @property
    def automatic_save_settings(self) -> bool:
        return self._automatic_save_settings
    
    @automatic_save_settings.setter
    def automatic_save_settings(self, value: bool) -> None:
        self._automatic_save_settings = value
    
    def set_settings(self) -> None:
        server = self._qgs_settings.value(config.QgsSettingsKeys.SERVERS, 0, type=int)
        for button in self.server_selection_button_group.buttons():
            if button.property("server") == server:
                button.setChecked(True)
            else:
                button.setChecked(False)
        automatic_crs = self._qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, bool)
        self.automatic_crs_check_box.setChecked(automatic_crs)
    
    def save_settings(self) -> None:
        for button in self.server_selection_button_group.buttons():
            if button.isChecked():
                server = button.property("server")
                self._qgs_settings.setValue(config.QgsSettingsKeys.SERVERS, server)
                break
        automatic_crs = self.automatic_crs_check_box.isChecked()
        self._qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, automatic_crs)
    
    def set_default_settings(self) -> None:
        # Server selection
        for button in self.server_selection_button_group.buttons():
            if button.property("server") == 0:
                button.setChecked(True)
            else:
                button.setChecked(False)
                
        # Automatic CRS
        self.automatic_crs_check_box.setChecked(False)
    
    def _on_server_selection_clicked(self, button: QtWidgets.QAbstractButton) -> None:
        if self.automatic_save_settings:
            server = button.property("server")
            self._qgs_settings.setValue(config.QgsSettingsKeys.SERVERS, server)
            events.emit_server_selection_changed()
    
    def _on_server_selection_changed(self) -> None:
        server = self._qgs_settings.value(config.QgsSettingsKeys.SERVERS, 0, type=int)
        for button in self.server_selection_button_group.buttons():
            if button.property("server") == server:
                button.setChecked(True)
            else:
                button.setChecked(False)
    
    def _on_automatic_crs_check_box_changed(self, state: bool) -> None:
        if self.automatic_save_settings:
            self._qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, state)
            events.emit_automatic_crs_changed()
    
    def _on_automatic_crs_changed(self) -> None:
        automatic_crs = self._qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, bool)
        self.automatic_crs_check_box.setChecked(automatic_crs)
    
    def _on_advanced_settings_button_clicked(self) -> None:
        from ..dialogs import open_settings
        open_settings()
    
    # The advanced button needs to be hidden in the dialog but since there is no other component
    # in the section, the entire group box is hidden
    # This needs to chenge when more settings are added to the section
    def set_advanced_settings_visibility(self, visible: bool) -> None:
        self.advanced_settings_group_box.setVisible(visible)