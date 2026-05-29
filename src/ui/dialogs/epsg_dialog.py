from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt import uic, QtWidgets, QtCore
from ... import config

EPSG_DIALOG = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "epsg_selector.ui")[0]

class EpsgDialog(QtWidgets.QDialog, EPSG_DIALOG):
    selected_coord = None

    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setupUi(self)
        
        self.table: QtWidgets.QTableWidget = self.tableWidget
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        # Layout auf das vorhandene setzen
        layout = self.verticalLayout_2
        self.setLayout(layout)

        self.table.cellDoubleClicked.connect(self.confirm_selected_coord)
        self.buttonBox.accepted.connect(self.confirm_selected_coord)
        
    def set_table_data(self, supported_auth_ids: frozenset[str], layer_name: str) -> None:
        # Gespeichertes Koordinatensystem zurücksetzen
        self.selected_coord = None
        
        # Dialog Titel setzen
        self.setWindowTitle(f"Koordinatensystem für Layer '{layer_name}'")
        
        # Vorhandene Einträge löschen
        self.table.clearContents()
        for _ in range(self.table.rowCount()):
            self.table.removeRow(0)
        
        # CRS84 in Tabelle einfügen, wenn nicht in unterstützten Koordinatensystemen
        # if "EPSG:4326" not in supported_auth_ids:
        #     crs = QgsCoordinateReferenceSystem("EPSG:4326")
        #     self.table.insertRow(0)
        #     self.table.setItem(0, 0, QtWidgets.QTableWidgetItem(crs.description()))
        #     self.table.setItem(0, 1, QtWidgets.QTableWidgetItem("EPSG:4326"))
        
        # Alle erlaubten/verfügbaren Koordinatensysteme in Tabelle einfügen
        for auth_id in supported_auth_ids:
            # if auth_id == "CRS:84":
            #     auth_id = "OGC:CRS84"

            crs = QgsCoordinateReferenceSystem(auth_id)
            
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            self.table.setItem(row_pos, 0, QtWidgets.QTableWidgetItem(crs.description()))
            self.table.setItem(row_pos, 1, QtWidgets.QTableWidgetItem(auth_id))
    
    def confirm_selected_coord(self) -> None:
        current_row = self.table.currentRow()
        auth_id_item = self.table.item(current_row, 1) if current_row >= 0 else None
        if auth_id_item is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Keine Auswahl",
                "Bitte wählen Sie ein Koordinatensystem aus.",
            )
            return
        
        self.selected_coord = auth_id_item.text()
        self.accept()
