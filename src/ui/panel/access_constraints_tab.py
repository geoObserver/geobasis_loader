import re
import dataclasses
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.core import QgsApplication, QgsProject, QgsMapLayer, QgsDataSourceUri
from ... import config
from ...ui.widgets.item_delegates import WrappedTextItemDelegate
from ...utils import custom_logger

logger = custom_logger.get_logger(__name__)

FAVORITES_TAB = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "access_constraints_tab.ui")[0]

@dataclasses.dataclass(frozen=True)
class AccessConstraints:
    layer_id: str
    layer_name: str
    fees: str
    constraints: str
    server_name: str

# FIXME: Currently only fees and constraints from web layers -> Local layers with them are not showing
class AccessConstraintsTab(QtWidgets.QWidget, FAVORITES_TAB):
    def __init__(self, parent: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.constraints: list[AccessConstraints] = []
        # self.initialized = False
        # self._all_items: list[QtWidgets.QTreeWidgetItem] = []
        
        # Type hints for UI elements
        self.view_selection_combo_box: QtWidgets.QComboBox = self.view_selection_combo_box
        self.access_constraints_tree_widget: QtWidgets.QTreeWidget = self.access_constraints_tree_widget
        self.found_constraints_count: QtWidgets.QLabel = self.found_constraints_count
        
        # Connect slots
        app = QgsApplication.instance()
        if app is not None:
            app.localeChanged.connect(self._on_locale_changed)
        # self.view_selection_combo_box.currentIndexChanged.connect(self._set_style)
        # self.access_constraints_tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        # self.access_constraints_tree_widget.itemExpanded.connect(self._on_item_expanded)
        # self.access_constraints_tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        # self.access_constraints_tree_widget.customContextMenuRequested.connect(self._on_favorites_tree_context_menu)
                
        # Settings/Defaults
        access_constraints_search = QgsApplication.translate("QgsProjectPropertiesBase", "Access constraints")
        fees_search = QgsApplication.translate("QgsProjectPropertiesBase", "Fees")
        self.regex_search = re.compile(rf"<tr><td>{fees_search}<\/td><td>(.*?)<\/td><\/tr><tr><td>{access_constraints_search}<\/td><td>(.*?)<\/td><\/tr>", re.IGNORECASE | re.MULTILINE)
        
        project = QgsProject.instance()
        if project is not None:
            project.layersAdded.connect(self._on_layers_added)
            project.layersRemoved.connect(self._on_layers_removed)
            layers = project.mapLayers(True).values()
            self._on_layers_added(list(layers))

        self.access_constraints_tree_widget.setUniformRowHeights(False)
        self.access_constraints_tree_widget.setTextElideMode(QtCore.Qt.TextElideMode.ElideNone)
        self.access_constraints_tree_widget.setItemDelegate(WrappedTextItemDelegate(self.access_constraints_tree_widget, wrap_column=1))
        self.access_constraints_tree_widget.viewport().installEventFilter(self)
        self.access_constraints_tree_widget.header().sectionResized.connect(self._on_header_resized)

        self._refresh_tree_layout()
    
    def dispose(self) -> None:
        project = QgsProject.instance()
        if project is not None:
            project.layersAdded.disconnect(self._on_layers_added)
            project.layersRemoved.disconnect(self._on_layers_removed)
        app = QgsApplication.instance()
        if app is not None:
            app.localeChanged.disconnect(self._on_locale_changed)
        self.access_constraints_tree_widget.viewport().removeEventFilter(self)
        self.access_constraints_tree_widget.header().sectionResized.disconnect(self._on_header_resized)

    def eventFilter(self, obj, event):
        if obj is self.access_constraints_tree_widget.viewport() and event.type() == QtCore.QEvent.Type.Resize:
            self._refresh_tree_layout()
        return super().eventFilter(obj, event)

    def _on_header_resized(self, *_args):
        self._refresh_tree_layout()

    def _refresh_tree_layout(self) -> None:
        tree_header = self.access_constraints_tree_widget.header()
        if tree_header is None:
            return

        translated_labels = [
            "Fees",
            "Constraints",
            QgsApplication.translate("QgsProjectPropertiesBase", "Fees"),
            QgsApplication.translate("QgsProjectPropertiesBase", "Access constraints"),
        ]
        metrics = self.access_constraints_tree_widget.fontMetrics()
        widest = max((metrics.horizontalAdvance(label) for label in translated_labels if label), default=120)
        left_width = max(150, widest + 40)

        tree_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tree_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        tree_header.setStretchLastSection(False)
        self.access_constraints_tree_widget.setColumnWidth(0, left_width)
        self.access_constraints_tree_widget.updateGeometries()
        self.access_constraints_tree_widget.viewport().update()

        for index in range(self.access_constraints_tree_widget.topLevelItemCount()):
            parent = self.access_constraints_tree_widget.topLevelItem(index)
            if parent is None:
                continue
            for child_index in range(parent.childCount()):
                child = parent.child(child_index)
                if child is None:
                    continue
                value = child.text(1)
                if not value:
                    continue
                width = max(1, self.access_constraints_tree_widget.viewport().width() - left_width - 30)
                height = self.access_constraints_tree_widget.fontMetrics().boundingRect(
                    QtCore.QRect(0, 0, width, 10000),
                    QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.TextWordWrap,
                    value,
                ).height()
                child.setSizeHint(1, QtCore.QSize(width, max(24, height)))
        
    def build_constraints_tree(self) -> None:
        self.access_constraints_tree_widget.clear()
        for constraint in self.constraints:
            layer_item = QtWidgets.QTreeWidgetItem(self.access_constraints_tree_widget)
            layer_item.setText(0, constraint.layer_name)
            layer_item.setFirstColumnSpanned(True)
            fees_item = QtWidgets.QTreeWidgetItem(layer_item)
            fees_item.setText(0, QgsApplication.translate("QgsProjectPropertiesBase", "Fees"))
            fees_item.setText(1, constraint.fees)

            constraints_item = QtWidgets.QTreeWidgetItem(layer_item)
            constraints_item.setText(0, QgsApplication.translate("QgsProjectPropertiesBase", "Access constraints"))
            constraints_item.setText(1, constraint.constraints)
            self.access_constraints_tree_widget.addTopLevelItem(layer_item)

        self._refresh_tree_layout()
        self.found_constraints_count.setText(str(len(self.constraints)))
    
    def _on_layers_added(self, layers: list[QgsMapLayer]) -> None:
        for layer in layers:
            if layer is None or not layer.isValid():
                continue
            
            # Prefer provider metadata if layer metadata hasn't been explicitly saved over
            meta = layer.dataProvider().layerMetadata() if layer.dataProvider() else layer.metadata()

            # If provider layerMetadata() is empty, fall back to layer.metadata()
            if not meta.fees() and not meta.constraints() and not meta.licenses() and not meta.rights():
                meta = layer.metadata()
            
            print(meta.fees())
            
            # server_url = "Test"
            # print(f"Processing layer: {layer.name()}, Server: {server_url}")
            # html = layer.htmlMetadata()
            # fees, constraints = re.findall(self.regex_search, html)[0]
            # access_constraint = AccessConstraints(
            #     layer_id=layer.id(),
            #     layer_name=layer.name(),
            #     fees=fees,
            #     constraints=constraints,
            #     server_name=server_url
            # )
            # self.constraints.append(access_constraint)
            # self.build_constraints_tree()
    
    def _on_layers_removed(self, layers: list[str]) -> None:
        self.constraints = [c for c in self.constraints if c.layer_id not in layers]
        self.build_constraints_tree()

    def _on_locale_changed(self) -> None:
        access_constraints_search = "<tr><td>" + QgsApplication.translate("QgsProjectPropertiesBase", "Access constraints") + "</td></tr>"
        fees_search = "<tr><td>" + QgsApplication.translate("QgsProjectPropertiesBase", "Fees") + "</td></tr>"
        self.regex_search = re.compile(rf"<tr><td>{fees_search}<\/td><td>(.*?)<\/td><\/tr><tr><td>{access_constraints_search}<\/td><td>(.*?)<\/td><\/tr>", re.IGNORECASE | re.MULTILINE)
        self.build_constraints_tree()
        