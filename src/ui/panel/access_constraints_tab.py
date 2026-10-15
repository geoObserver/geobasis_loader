import re
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.core import QgsApplication, QgsProject, QgsMapLayer
from ... import config
from ...utils import custom_logger

logger = custom_logger.get_logger(__name__)

FAVORITES_TAB = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "access_constraints_tab.ui")[0]

# FIXME: Currently only fees and constraints from web layers -> Local layers with them are not showing
class AccessConstraintsTab(QtWidgets.QWidget, FAVORITES_TAB):
    def __init__(self, parent: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
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
    
    
    def _on_layers_added(self, layers: list[QgsMapLayer]) -> None:
        for layer in layers:
            if layer is None or not layer.isValid():
                continue
            
            html = layer.htmlMetadata()
            fees, constraints = re.findall(self.regex_search, html)[0]
            print(f"Layer: {layer.name()}, Fees: {fees}, Constraints: {constraints}")
    
    def _on_locale_changed(self) -> None:
        print("Locale changed, updating Access Constraints tab...")
        access_constraints_search = "<tr><td>" + QgsApplication.translate("QgsProjectPropertiesBase", "Access constraints") + "</td></tr>"
        fees_search = "<tr><td>" + QgsApplication.translate("QgsProjectPropertiesBase", "Fees") + "</td></tr>"
        self.regex_search = re.compile(rf"<tr><td>{fees_search}<\/td><td>(.*?)<\/td><\/tr><tr><td>{access_constraints_search}<\/td><td>(.*?)<\/td><\/tr>", re.IGNORECASE | re.MULTILINE)
        