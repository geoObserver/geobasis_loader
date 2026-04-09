"""Dialog for selecting a coordinate reference system (EPSG) from a list of supported CRS options."""

import os

from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt import QtWidgets, uic

EPSG_DIALOG = uic.loadUiType(os.path.join(os.path.dirname(__file__), "design_files", "epsg_selector.ui"))[0]

class EpsgDialog(QtWidgets.QDialog, EPSG_DIALOG):
    """Dialog that lets the user pick a coordinate reference system from a table.

    Displays supported CRS authority IDs with their descriptions and stores
    the user's selection in ``selected_coord``.
    """

    selected_coord = None

    def __init__(self, parent = None):
        QtWidgets.QDialog.__init__(self, parent)
        self.setupUi(self)
        self._want_to_close = False

        self.table: QtWidgets.QTableWidget = self.tableWidget
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Layout auf das vorhandene setzen
        layout = self.verticalLayout_2
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.confirm_selected_coord)
        self.table.cellDoubleClicked.connect(self.confirm_selected_coord)

    def set_table_data(self, supported_auth_ids: list[str], layer_name: str) -> None:
        """Populate the table with the given coordinate reference systems.

        Resets any previous selection, updates the dialog title to include the
        layer name, and fills the table with CRS descriptions and authority IDs.

        Args:
            supported_auth_ids: Authority IDs of the supported coordinate
                reference systems (e.g. ``["EPSG:25832", "EPSG:4326"]``).
            layer_name: Name of the layer, shown in the dialog title.

        """
        # Gespeichertes Koordinatensystem zurücksetzen
        self.selected_coord = None

        # Dialog Titel setzen
        self.setWindowTitle(f"Koordinatensystem für Layer '{layer_name}'")

        # Vorhandene Einträge löschen
        self.table.clearContents()
        self.table.setRowCount(0)

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
        """Store the currently selected CRS authority ID and close the dialog.

        Does nothing if no row is selected or the selected cell is empty.
        On success, sets ``selected_coord`` to the authority ID string
        (e.g. ``"EPSG:25832"``) and closes the dialog.
        """
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 1)
        if item is None:
            return
        self.selected_coord = item.text()
        self.close()
