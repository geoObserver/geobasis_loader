import json
import re
import dataclasses
from typing import Optional
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.core import QgsApplication, QgsProject, QgsMapLayer, Qgis
from ... import config
from ...models import catalog_types
from ...utils import custom_logger
from ...ui import icons

logger = custom_logger.get_logger(__name__)

FAVORITES_TAB = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "access_constraints_tab.ui")[0]

@dataclasses.dataclass(frozen=True)
class ConstraintEntry:
    layer_id: str
    layer_name: str
    layer_type: Qgis.LayerType
    server_name: str
    server_url: str

@dataclasses.dataclass(frozen=True)
class AccessConstraints(ConstraintEntry):
    fees: str
    constraints: str
    
@dataclasses.dataclass(frozen=True)
class LicenseEntry(ConstraintEntry):
    license: str

# FIXME: Currently only fees and constraints from web layers -> Local layers with them are not showing
class AccessConstraintsTab(QtWidgets.QWidget, FAVORITES_TAB):
    def __init__(self, parent: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.constraints: list[ConstraintEntry] = []
        # self.initialized = False
        # self._all_items: list[QtWidgets.QTreeWidgetItem] = []
        
        # Type hints for UI elements
        self.view_selection_combo_box: QtWidgets.QComboBox = self.view_selection_combo_box
        self.access_constraints_tree_widget: QtWidgets.QTreeWidget = self.access_constraints_tree_widget
        self.found_constraints_count: QtWidgets.QLabel = self.found_constraints_count
        
        self.text_browser: QtWidgets.QTextBrowser = self.text_browser
        
        # Connect slots
        # self.view_selection_combo_box.currentIndexChanged.connect(self._set_style)
        # self.access_constraints_tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        # self.access_constraints_tree_widget.itemExpanded.connect(self._on_item_expanded)
        # self.access_constraints_tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        # self.access_constraints_tree_widget.customContextMenuRequested.connect(self._on_favorites_tree_context_menu)
        self.access_constraints_tree_widget.itemClicked.connect(self._on_item_clicked)
        self.view_selection_combo_box.currentIndexChanged.connect(self._set_style)
                
        # Settings/Defaults        
        project = QgsProject.instance()
        if project is not None:
            project.layersAdded.connect(self._on_layers_added)
            project.layersRemoved.connect(self._on_layers_removed)
            layers = project.mapLayers(True).values()
            self._on_layers_added(list(layers))
    
    def dispose(self) -> None:
        project = QgsProject.instance()
        if project is not None:
            project.layersAdded.disconnect(self._on_layers_added)
            project.layersRemoved.disconnect(self._on_layers_removed)
        
    def _set_flat_style(self) -> None:
        self.access_constraints_tree_widget.clear()
        for constraint in self.constraints:
            layer_item = QtWidgets.QTreeWidgetItem(self.access_constraints_tree_widget)
            layer_item.setText(0, constraint.layer_name)
            # Icons not correct -> ArcGIs has own icons not yet here represented
            if constraint.layer_type == Qgis.LayerType.Vector:
                layer_item.setIcon(0, icons.get_icon(catalog_types.TopicType.WFS))
            elif constraint.layer_type == Qgis.LayerType.Raster:
                layer_item.setIcon(0, icons.get_icon(catalog_types.TopicType.WMS))
            elif constraint.layer_type == Qgis.LayerType.VectorTile:
                layer_item.setIcon(0, icons.get_icon(catalog_types.TopicType.VECTORTILES))
            else:
                pass

            layer_item.setFirstColumnSpanned(True)
            layer_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, constraint)
            self.access_constraints_tree_widget.addTopLevelItem(layer_item)

        self.found_constraints_count.setText(str(len(self.constraints)))
    
    def _set_grouped_style(self) -> None:
        import itertools
        
        self.access_constraints_tree_widget.clear()
        server_groups = itertools.groupby(sorted(self.constraints, key=lambda c: c.server_url), key=lambda c: c.server_url)
        for server_url, group in server_groups:
            server_item = QtWidgets.QTreeWidgetItem(self.access_constraints_tree_widget)
            # server_item.setText(0, next(group).server_name)
            server_item.setFirstColumnSpanned(True)
            self.access_constraints_tree_widget.addTopLevelItem(server_item)

            for constraint in group:
                server_item.setText(0, constraint.server_name)
                layer_item = QtWidgets.QTreeWidgetItem(server_item)
                layer_item.setText(0, constraint.layer_name)
                # Icons not correct -> ArcGIs has own icons not yet here represented
                if constraint.layer_type == Qgis.LayerType.Vector:
                    layer_item.setIcon(0, icons.get_icon(catalog_types.TopicType.WFS))
                elif constraint.layer_type == Qgis.LayerType.Raster:
                    layer_item.setIcon(0, icons.get_icon(catalog_types.TopicType.WMS))
                elif constraint.layer_type == Qgis.LayerType.VectorTile:
                    layer_item.setIcon(0, icons.get_icon(catalog_types.TopicType.VECTORTILES))
                else:
                    pass

                layer_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, constraint)
                server_item.addChild(layer_item)

    def _on_layers_added(self, layers: list[QgsMapLayer]) -> None:
        for layer in layers:
            if layer is None or not layer.isValid():
                continue
            
            data_provider = layer.dataProvider()
            if data_provider is None:
                continue
            
            # Prefer provider metadata if layer metadata hasn't been explicitly saved over
            # meta = layer.dataProvider().layerMetadata() if layer.dataProvider() else layer.metadata()

            # # If provider layerMetadata() is empty, fall back to layer.metadata()
            # if not meta.fees() and not meta.constraints() and not meta.licenses() and not meta.rights():
            #     meta = layer.metadata()
            
            # print(meta.fees())
            
            import urllib.parse as urlparse
            from qgis.core import QgsDataSourceUri, QgsBlockingNetworkRequest
            from qgis.PyQt import QtNetwork
            
            data_provider = layer.dataProvider()
            source_uri = layer.source()
            # source_uri = "https://example.com/Alice%26Bob?param1%3Dvalue1%26param2=value2"
            parsed_url = urlparse.urlsplit(source_uri, scheme='http')
            #TODO: Chack with database layers
            if parsed_url.scheme not in ['http', 'https']:
                continue  # Skip non-HTTP/HTTPS layers
            
            # Normal URLs
            # Encode the domain and path so that QgsDataSourceUri doesnt interprate special characters like '&' and '=' as query parameters.
            # Then decode the query string to preserve its original form. This also allows mixed strings (both encoded and unencoded parts without issues).
            if source_uri.startswith(("http://", "https://", "www.")):
                base_url = urlparse.quote(f"{parsed_url.netloc}{parsed_url.path}")
                query_string = urlparse.unquote(f"{parsed_url.query}")
                source_uri = "url=" + parsed_url.scheme + "://" + base_url + "&" + query_string
            
            uri = QgsDataSourceUri(source_uri)
            encoded_uri = uri.encodedUri()
            uri = QgsDataSourceUri()
            uri.setEncodedUri(urlparse.unquote(encoded_uri.data().decode('utf-8')))
            
            # Create capabilities url
            base_url: Optional[str] = uri.param("url")
            if not base_url:
                continue
            
            base_url = base_url.split("?")[0]  # Remove query parameters
            qurl = QtCore.QUrl(base_url)
            query = QtCore.QUrlQuery(qurl)
            complete_url = ""
            
            ptype = layer.providerType().lower()
            if ptype in ("wms", "wfs", "wcs"):
                # If it's a static WMTS REST capabilities XML URL, return as-is
                if ptype == "wms" and qurl.path().lower().endswith(".xml"):
                    complete_url = base_url
                else:
                    query.addQueryItem("SERVICE", ptype.upper())
                    query.addQueryItem("REQUEST", "GetCapabilities")
                    if version := (uri.param("version") or uri.param("VERSION")):
                        if version.lower() != "auto":
                            query.addQueryItem("VERSION", version)
                    
                qurl.setQuery(query)
                complete_url = qurl.toString()
                
            elif ptype == "oapif":
                query.addQueryItem("f", "json")
                qurl.setQuery(query)
                complete_url = qurl.toString()
                
            elif ptype in ("arcgisfeatureserver", "arcgismapserver"):
                # TODO: Test this
                # Strip trailing /<layer_id> (e.g. .../MapServer/0 -> .../MapServer)
                clean_path = re.sub(r"/\d+/?$", "", qurl.path())
                qurl.setPath(clean_path)
                query.addQueryItem("f", "json")
                qurl.setQuery(query)
                complete_url = qurl.toString()

            else:
                continue  # Skip unsupported provider types
            
            req = QtNetwork.QNetworkRequest(QtCore.QUrl(complete_url))
            req.setRawHeader(b"Accept", b"application/json, application/xml, text/xml, */*")

            blocker = QgsBlockingNetworkRequest()
            if authcfg := uri.param("authcfg"):
                blocker.setAuthCfg(authcfg)
            
            err = blocker.get(req, forceRefresh=False)  # Uses QGIS cache if available!
            if err != QgsBlockingNetworkRequest.ErrorCode.NoError:
                print(err)
                continue  # Skip if request failed
            
            raw_text = blocker.reply().content().data().decode("utf-8", errors="replace")
            if ptype in ("wms", "wfs", "wcs"):
                from xml.etree import ElementTree as ET
                doc = ET.fromstring(raw_text)
                service_title = doc.findtext(".{*}Service/{*}Title") or doc.findtext(".{*}ServiceIdentification/{*}Title")
                service_fees = doc.findtext(".{*}Service/{*}Fees") or doc.findtext(".{*}ServiceIdentification/{*}Fees")
                service_constraints = doc.findtext(".{*}Service/{*}AccessConstraints") or doc.findtext(".{*}ServiceIdentification/{*}AccessConstraints")
                
                self.constraints.append(AccessConstraints(
                    layer_id=layer.id(),
                    layer_name=layer.name(),
                    layer_type=layer.type(),
                    fees=service_fees if service_fees else "N/A",
                    constraints=service_constraints if service_constraints else "N/A",
                    server_name=service_title if service_title else "N/A",
                    server_url=base_url
                ))
                # self.build_constraints_tree()
                continue
            
            # --- B. Parse JSON (OGC API & ArcGIS REST) ---
            try:
                data = json.loads(raw_text)
            except json.JSONDecodeError:
                continue  # Skip if JSON parsing fails
            
            # TODO: License Links on the rest url not just home page
            if ptype == "oapif":
                licenses = [
                    link.get("title") or link.get("href")
                    for link in data.get("links", [])
                    if link.get("rel") == "license"
                ]
                self.constraints.append(LicenseEntry(
                    layer_id=layer.id(),
                    layer_name=layer.name(),
                    layer_type=layer.type(),
                    license="; ".join(licenses) if licenses else "N/A",
                    server_name=data.get("title", "N/A"),
                    server_url=base_url,
                ))
                # print(f"{layer.name()} - Licenses: {licenses if licenses else 'N/A'}")
                # self.build_constraints_tree()
                continue

            if ptype in ("arcgisfeatureserver", "arcgismapserver"):
                constraints = []
                if data.get("copyrightText"):
                    constraints.append(data["copyrightText"])
                # if data.get("accessInformation"):
                #     constraints.append(data["accessInformation"])
                self.constraints.append(AccessConstraints(
                    layer_id=layer.id(),
                    layer_name=layer.name(),
                    layer_type=layer.type(),
                    fees="N/A",
                    constraints="; ".join([c.strip() for c in constraints]) if constraints else "N/A",
                    server_name=data.get("serviceDescription", "N/A"),
                    server_url=base_url
                ))
                # print(f"{layer.name()} - Constraints: {constraints if constraints else 'N/A'}")
                # self.build_constraints_tree()
                continue

            print(f"Unsupported provider type: {ptype} for layer {layer.name()}")

            # access_constraint = AccessConstraints(
            #     layer_id=layer.id(),
            #     layer_name=layer.name(),
            #     fees=fees,
            #     constraints=constraints,
            #     server_name=server_url
            # )
            # self.constraints.append(access_constraint)
        self._set_style(self.view_selection_combo_box.currentIndex())
    
    def _on_layers_removed(self, layers: list[str]) -> None:
        self.constraints = [c for c in self.constraints if c.layer_id not in layers]
        self._set_flat_style()
    
    def _on_item_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:       
        constraints = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        
        def convert_urls(matchobj: re.Match) -> str:
            url: str = matchobj.group(0)
            href = url
            if url.endswith("."):
                href = url[:-1]  # Remove trailing period
            return f'<a href="{href}">{url}</a>'
        
        regex = r"(?:http[s]?:\/\/.)?(?:www\.)?[-a-zA-Z0-9@%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:\,%_\+.~#?&\/\/=]*)"
        
        if constraints:
            # TODO: Also allow IP address range for internal servers
            if isinstance(constraints, LicenseEntry):
                license_text = re.sub(regex, convert_urls, constraints.license)
                self.text_browser.setHtml(f"<b>{QgsApplication.translate('QgsProjectPropertiesBase', 'Layer')}:</b> {constraints.layer_name}<br>"
                                          f"<b>Server:</b> {constraints.server_name}<br>"
                                          f"<b>{QgsApplication.translate('QgsProjectProperties', 'License')}:</b> {license_text}")
            else:
                fees_text = re.sub(regex, convert_urls, constraints.fees)
                constraints_text = re.sub(regex, convert_urls, constraints.constraints)
                
                self.text_browser.setHtml(f"<b>{QgsApplication.translate('QgsProjectPropertiesBase', 'Layer')}:</b> {constraints.layer_name}<br>"
                                          f"<b>Server:</b> {constraints.server_name}<br>"
                                          f"<b>{QgsApplication.translate('QgsProjectPropertiesBase', 'Fees')}:</b> {fees_text}<br>"
                                          f"<b>{QgsApplication.translate('QgsProjectPropertiesBase', 'Access constraints')}:</b> {constraints_text}")

    def _set_style(self, index: int) -> None:
        self.access_constraints_tree_widget.clear()
        if index == 0:  
            self._set_flat_style()
        elif index == 1:
            self._set_grouped_style()
        else:
            print(f"Unknown view selection index: {index}")