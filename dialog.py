import os
from qgis.core import QgsCoordinateReferenceSystem
from PyQt5 import uic, QtWidgets

EPSG_DIALOG = uic.loadUiType(os.path.join(os.path.dirname(__file__), f"ui{os.path.sep}epsg_selector.ui"))[0]

class EpsgDialog(QtWidgets.QDialog, EPSG_DIALOG):
    selected_coord = None

    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        self._want_to_close = False
        
        self.table: QtWidgets.QTableWidget = self.tableWidget
        header = self.table.horizontalHeader()       
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        
        # Layout auf das vorhandene setzen
        layout = self.verticalLayout_2
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.confirm_selected_coord)
        self.table.cellDoubleClicked.connect(self.confirm_selected_coord)
        
    def set_table_data(self, supported_auth_ids: list[str], layer_name: str) -> None:
        # Gespeichertes Koordinatensystem zurücksetzen
        self.selected_coord = None
        
        # Dialog Titel setzen
        self.setWindowTitle(f"Koordinatensystem für Layer '{layer_name}'")
        
        # Vorhandene Einträge löschen
        self.table.clearContents()
        for row in range(self.table.rowCount()):
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
        selected_items = self.table.selectedItems()
        if len(selected_items) > 0:
            auth_id = selected_items[1].text()            
            self.selected_coord = auth_id
            self.close()