from qgis.PyQt import uic, QtWidgets
from ... import config

PRESET_DIALOG = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "preset_dialog.ui")[0]

class PresetDialog(QtWidgets.QDialog, PRESET_DIALOG):
    def __init__(self, preset_title: str = "", preset_description: str = "", save_layer_crs: bool = False, save_crs_checkbox_visible: bool = True, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        
        # Variables
        self.preset_title: str = preset_title
        self.preset_description: str | None = preset_description
        self.save_layer_crs: bool = save_layer_crs or save_crs_checkbox_visible
        
        # Type hints for UI elements
        self.description_edit: QtWidgets.QPlainTextEdit = self.description_edit
        self.title_edit: QtWidgets.QLineEdit = self.title_edit
        self.save_layer_crs_checkbox: QtWidgets.QCheckBox = self.save_layer_crs_checkbox
        
        # Default values
        self.title_edit.setText(preset_title)
        self.description_edit.setPlainText(preset_description)
        self.save_layer_crs_checkbox.setChecked(save_layer_crs)
        self.save_layer_crs_checkbox.setVisible(save_crs_checkbox_visible)
        
        self.buttonBox.accepted.connect(self.confirm_options)
    
    def confirm_options(self) -> None:
        title = self.title_edit.text().strip()
        description = self.description_edit.toPlainText()
        save_layer_crs = self.save_layer_crs_checkbox.isChecked()
        
        if not title:
            QtWidgets.QMessageBox.warning(self, "Ungültiger Titel", "Der Titel darf nicht leer sein.")
            return
        
        self.preset_title = title
        self.preset_description = description if description else None
        self.save_layer_crs = save_layer_crs
        self.accept()
        self.deleteLater()