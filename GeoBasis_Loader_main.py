import re
from functools import partial
from typing import Union, Optional
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtGui import QIcon, QColor, QDesktopServices
from qgis.PyQt.QtCore import QUrl, QObject
from qgis.core import QgsSettings, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer, QgsLayerTree, QgsSymbolLayer, QgsWkbTypes, Qgis
from qgis.gui import QgisInterface
from .topic_search import SearchFilter
from . import config
from . import ui as custom_ui
from .catalog_manager import CatalogManager
from .property_manager import singleton as PropertyManager

if Qgis.versionInt() < 33000:   # Breaking change in Version 3.30 -> Geometry types now in Qgis instead of QgsWkbTypes
    geometry_types = QgsWkbTypes.Type       # type: ignore
else:
    geometry_types = Qgis.WkbType

class GeoBasis_Loader(QObject):
    services = None
    
    search_filter = None
    qgs_settings = QgsSettings()

# =========================================================================
    def __init__(self, iface: QgisInterface, parent = None) -> None:
        super().__init__(parent)
        self.iface = iface
        CatalogManager.setup(iface)
        CatalogManager.get_overview(callback=self.initGui)
        
        # ------- Create dialog variables, create dialogs lazily
        self._epsg_dialog: Optional[custom_ui.EpsgDialog] = None
        self._settings_dialog: Optional[custom_ui.SettingsDialog] = None

        # ------- Letzten Katalog laden --------------------------------------------
        current_catalog = self.qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is not None and "name" in current_catalog:
            CatalogManager.get_catalog(current_catalog["titel"], current_catalog["name"], self.set_services)
            
        # ------- Letzte Einstellung für automatisches Koordinatensystem laden -----
        self.automatic_crs = self.qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, type=bool)

        icon = QIcon(config.PLUGIN_DIR + "/GeoBasis_Loader_icon.png")
        self.main_menu = QMenu(config.PLUGIN_NAME_AND_VERSION)
        self.main_menu.setIcon(icon)
        self.iface.pluginMenu().addMenu(self.main_menu)
        
        self.search_filter = SearchFilter(self)
        self.iface.registerLocatorFilter(self.search_filter)    
        #self.iface.messageBar().pushMessage(self.myPluginV,f'Sollte Euch das Plugin gefallen,{"&nbsp;"}könnt Ihr es gern mit Eurer Mitarbeit,{"&nbsp;"}einem Voting und ggf.{"&nbsp;"}einem kleinen Betrag unterstützen ...{"&nbsp;"}Danke!!', 3, 8)     
    
    def initGui(self) -> None:
        self.main_menu.clear()
        
        if self.services is not None:
            # ------- Name des Katalogs einfügen -------------------------
            self.main_menu.addAction(self.qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)["titel"])
            self.main_menu.addSeparator()
            # ------- Menübaum bauen und einfügen ------------------------
            for abr, region in self.services:
                # Falls der zweite Eintrag kein Dictionary ist, überspringen, da es Metadaten sind
                if not isinstance(region, dict) or not PropertyManager.is_visible(region[config.InternalProperties.PATH]):
                    continue
                
                region_menu = self.gui_for_one_region(region['themen'], region['menu'])
                self.main_menu.addMenu(region_menu)
                
                if abr == 'de' or "seperator" in region:
                    self.main_menu.addSeparator()
            
            self.main_menu.addSeparator()
            
        if CatalogManager.overview is not None:
            # ------- Katalogmenü erstellen ------------------------------------
            catalogs_menu = self.main_menu.addMenu("Katalog wechseln (Change Catalogs)")
            catalogs_menu.setObjectName('catalog-overview')
            
            # ------- Einträge im Katalogmenü erstellen ------------------------
            for catalog in CatalogManager.overview:
                catalog_action = catalogs_menu.addAction(catalog["titel"], partial(self.change_current_catalog, catalog))
                catalog_action.setObjectName("open-" + catalog["titel"])
            
            action = self.main_menu.addAction("Kataloge neu laden (Reload Catalogs)")
            action.triggered.connect(lambda: CatalogManager.get_overview(callback=self.initGui))
            
            self.main_menu.addSeparator()
                
        # ------- Über-Schaltfläche für die JSON-Datei ------------------------
        action = QAction(text="Wenn möglich, Dienste autom. im KBS laden", parent=self.main_menu, checkable=True, checked=self.automatic_crs)
        action.toggled.connect(self.toggle_automatic_crs)
        self.main_menu.addAction(action)
        
        self.main_menu.addAction("Einstellungen (Aktueller Katalog)", self.open_settings)
        self.main_menu.addSeparator()
        
        # ------- Spenden-Schaltfläche für #geoObserver ------------------------
        action = self.main_menu.addAction("GeoBasis_Loader per Spende unterstützen ...", self.open_web_site)
        if action:
            action.setData('https://geoobserver.de/support_geobasis_loader/')
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        action = self.main_menu.addAction("Über ...", self.open_web_site)
        if action:
            action.setData('https://geoobserver.de/qgis-plugin-geobasis-loader/')

        # ------- Status-Schaltfläche für #geoObserver ------------------------
        # self.mainMenu.addAction("Status ...", partial(self.openWebSite, 'https://geoobserver.de/qgis-plugin-geobasis-loader/#statustabelle'))
        
    def gui_for_one_region(self, topic_dict: dict, topic_abbreviation: str) -> QMenu:
        def _create_action(name: str, parent: QMenu, path: str, tip: str = "Thema hinzufügen", slot = self.add_topic) -> QAction:
            action = QAction(name, parent)
            action.setObjectName(name)
            action.setStatusTip(tip)
            action.setToolTip(tip)
            action.setData(path)
            action.triggered.connect(slot)
            return action
        
        menu = QMenu(topic_abbreviation, self.main_menu)
        menu.setObjectName('loader-' + topic_abbreviation)
        menu.setToolTipsVisible(True)
        
        for topic in topic_dict.values():
            if not PropertyManager.is_visible(topic[config.InternalProperties.PATH]):
                continue
            
            if topic.get("type", "").lower() == "web":
                action = _create_action(topic["name"], menu, topic["uri"], "Informationen öffnen", self.open_web_site)
                menu.addAction(action)
                continue
            
            if isinstance(topic.get("layers", []), dict):
                topic_group_menu = QMenu(topic["name"], menu)
                topic_group_menu.setToolTipsVisible(True)
                
                add_all_action = _create_action("Alle laden", topic_group_menu, topic[config.InternalProperties.PATH], "Alle Themen der Gruppe laden")
                topic_group_menu.addAction(add_all_action)
                topic_group_menu.addSeparator()

                for _, subtopic in topic["layers"].items():
                    if not PropertyManager.is_visible(subtopic[config.InternalProperties.PATH]):
                        continue
                    
                    if subtopic.get("type", "").lower() == "web":
                        subtopic_action = _create_action(subtopic["name"], topic_group_menu, subtopic["uri"], "Informationen öffnen", self.open_web_site)
                    else:
                        subtopic_action = _create_action(subtopic["name"], topic_group_menu, subtopic[config.InternalProperties.PATH])
                    topic_group_menu.addAction(subtopic_action)

                menu.addMenu(topic_group_menu)
            else:        
                action = _create_action(topic['name'], menu, topic[config.InternalProperties.PATH])            
                menu.addAction(action)
                
            if "seperator" in topic:
                menu.addSeparator()
        return menu
    
#===================================================================================

    def unload(self):
        self.iface.invalidateLocatorResults()
        self.iface.deregisterLocatorFilter(self.search_filter)
        self.search_filter = None
        if self.main_menu:
            self.iface.pluginMenu().removeAction(self.main_menu.menuAction())

#===================================================================================

    @property
    def epsg_dialog(self):
        if self._epsg_dialog is None:
            self._epsg_dialog = custom_ui.EpsgDialog(self.iface.mainWindow())
        return self._epsg_dialog
    
    @property
    def settings_dialog(self):
        if self._settings_dialog is None:
            self._settings_dialog = custom_ui.SettingsDialog(self.iface.mainWindow())
        return self._settings_dialog

    def open_settings(self) -> None:
        status = self.settings_dialog.exec()
        # Abbruch
        if status == 0:
            return
        
        self.automatic_crs = self.qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, bool)
        
        self.iface.messageBar().pushMessage(config.PLUGIN_NAME_AND_VERSION, 'Einstellungen erfolgreich gespeichert', Qgis.MessageLevel.Success, 3)
        self.initGui()

    def toggle_automatic_crs(self) -> None:
        new_state = not self.automatic_crs
        
        self.automatic_crs = new_state
        self.qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, new_state)

    def open_web_site(self):
        sender = self.sender()
        if not sender or not isinstance(sender, QAction):
            return
        
        data = sender.data() # type: ignore
        url = QUrl(data)
        
        # Opens webpage in the standard browser
        QDesktopServices.openUrl(url)
        
    def change_current_catalog(self, catalog: dict):
        self.qgs_settings.setValue(config.QgsSettingsKeys.CURRENT_CATALOG, catalog)
        CatalogManager.get_catalog(catalog["titel"], callback=self.set_services)
        
    def set_services(self, services: dict):
        current_catalog = self.qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is None or "titel" not in current_catalog:
            # LOGGING
            
            return
        
        titel = current_catalog["titel"]
        name = current_catalog["name"]
        version_matches = re.findall(r'v\d+', name)
        version = version_matches[0] if version_matches else "unbekannt"
        self.iface.messageBar().pushMessage(config.PLUGIN_NAME_AND_VERSION, 'Lese '+ titel + ", Version " + version + ' ...', Qgis.MessageLevel.Success, 3)
        
        self.services = services
        self.initGui()
    
    # Get crs from user
    def get_crs(self, supported_auth_ids: list[str], layer_name: str) -> Union[str, None]:
        if supported_auth_ids is None:
            return None
        
        current_crs = QgsProject.instance().crs().authid()          
        if current_crs not in supported_auth_ids or not self.automatic_crs:
            self.epsg_dialog.set_table_data(supported_auth_ids, layer_name)
            self.epsg_dialog.exec()
            if self.epsg_dialog.selected_coord is None:
                return None
            current_crs = self.epsg_dialog.selected_coord
        
        return current_crs
    
    def add_topic(self, catalog_title: Optional[str] = None, path: str = ""):
        if path == "":
            sender = self.sender()
            if not sender:
                return

            path = sender.data() # type: ignore
            if not isinstance(path, str):
                raise TypeError("Path is unknown")
            
            # Explicitly checking the value makes sense but seems unnecessary, since the code is unreachable without it (unless QGIS doesnt reset plugins after reseting settings)
            current_catalog = self.qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
            if current_catalog is None or "titel" not in current_catalog:
                # LOGGING
                self.iface.messageBar().pushWarning(
                    config.PLUGIN_NAME_AND_VERSION,
                    "Kein Katalog ausgewaehlt. Bitte waehlen Sie zuerst einen Katalog."
                )
                return
            catalog_title = current_catalog["titel"]

        catalog: dict = dict(CatalogManager.get_catalog(catalog_title)) # type: ignore
        topic = catalog
        for key in path.split("/"):
            topic = topic[key]
        
        if "layers" not in topic:
            self.add_layer(topic, None)
            return
        
        layers = topic["layers"]
        if isinstance(layers, list):
            combination_layers = []
            group_key = path.split("/")[0]
            for layer in layers:
                sub_topic = catalog[group_key]["themen"][layer]
                combination_layers.append(sub_topic)
            self.add_layer_combination(combination_layers)
        else:
            self.add_layer_group(None, layers, topic["name"])
    
    def add_layer(self, attributes: dict, crs: Union[str, None], standalone: bool = True):
        if not PropertyManager.is_enabled(attributes[config.InternalProperties.PATH]):
            return None
        
        layer_type = attributes.get('type', 'ogc_wms').lower()
        if layer_type == "web":
            return None
        
        uri: str = attributes.get('uri', "n.n.")
        valid_epsg_codes: list[str] = attributes.get('valid_epsg', [])
       
        if crs is None or crs not in valid_epsg_codes:
            crs = self.get_crs(valid_epsg_codes, attributes.get('name', "Fehler"))
            if crs is None:
                return
        
        # if crs == "OGC:CRS84":
        #     crs = "CRS:84"
        
        uri = re.sub(r'EPSG:placeholder', crs, uri)

        if layer_type != "ogc_wfs" and layer_type != "ogc_api_features":
            uri += "&stepHeight=3000&stepWidth=3000"
        
        opacity = attributes.get('opacity', 1)
        max_scale = attributes.get('maxScale', None)
        min_scale = attributes.get('minScale', None)

        fill_color = attributes.get('fillColor', [220,220,220])
        stroke_color = attributes.get('strokeColor', 'black')
        stroke_width = attributes.get('strokeWidth', 0.3)
        
        if uri == "n.n.":
            self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + f", URL des Themas derzeit unbekannt.{'&nbsp;'}Falls gültige/aktuelle URL bekannt,{'&nbsp;'}bitte dem Autor melden.")
            return
        
        if layer_type == "ogc_wfs":
            layer = QgsVectorLayer(uri, attributes['name'], 'wfs')
        elif layer_type == "ogc_api_features":
            layer = QgsVectorLayer(uri, attributes['name'], 'oapif')
        elif layer_type == "ogc_vectortiles":
            layer = QgsVectorTileLayer(uri, attributes['name'])
            layer.loadDefaultStyle()
        elif layer_type == "ogc_wcs":
            layer = QgsRasterLayer(uri, attributes['name'], 'wcs')
        else:
            layer = QgsRasterLayer(uri, attributes['name'], 'wms')

        if not layer.isValid():
            self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + config.MY_CRITICAL_2)
            return
        
        if hasattr(layer, 'setOpacity'):
            layer.setOpacity(opacity)
            
        if isinstance(layer, QgsVectorLayer):
            if max_scale is None:
                max_scale = 1.0
            if min_scale is None:
                min_scale = 25000
        
        if min_scale is not None and max_scale is not None:
            if min_scale < max_scale:
                self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + "; Skalenwerte vertauscht oder fehlerhaft")
            elif min_scale == max_scale: 
                self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + "; Skalenwerte gleich")   
            elif min_scale > max_scale:
                layer.setMinimumScale(min_scale)
                layer.setMaximumScale(max_scale)
                layer.setScaleBasedVisibility(True)
        
        if isinstance(layer, QgsVectorLayer):
            fill_color: QColor = QColor(*[int(c) for c in fill_color]) if isinstance(fill_color, list) else QColor(fill_color)
            stroke_color: QColor = QColor(*[int(c) for c in stroke_color]) if isinstance(stroke_color, list) else QColor(stroke_color)
            
            symbol_layer: QgsSymbolLayer = layer.renderer().symbol().symbolLayer(0)
            symbol_layer.setColor(fill_color)
            
            geom_type = QgsWkbTypes.singleType(QgsWkbTypes.flatType(layer.wkbType()))
            if geom_type == geometry_types.LineString:
                symbol_layer.setWidth(stroke_width)  
            elif geom_type == geometry_types.Polygon:
                symbol_layer.setStrokeColor(stroke_color)
                symbol_layer.setStrokeWidth(stroke_width)
            elif geom_type == geometry_types.Point:
                symbol_layer.setSize(stroke_width)
            else:
                print("Fehler bei Bestimmung der Geometrieart; Bestimmte Geometrie " + QgsWkbTypes.displayString(geom_type))
                        
            layer.triggerRepaint()
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        
        self.iface.messageBar().pushMessage(config.PLUGIN_NAME_AND_VERSION, config.MY_INFO_1 + attributes['name'] + config.MY_INFO_2, Qgis.MessageLevel.Success, 1)
        # Ebene zum Projekt hinzufügen aber nicht automatisch zum Ebenenbaum
        QgsProject.instance().addMapLayer(layer, False) # type: ignore

        if standalone:
            root: QgsLayerTree = QgsProject.instance().layerTreeRoot()
            ltl = root.insertLayer(0, layer)
            if ltl:
                ltl.setExpanded(False)
                visible = PropertyManager.is_visible(attributes[config.InternalProperties.PATH])
                ltl.setItemVisibilityChecked(visible)

        return layer
    
    def add_layer_group(self, preferred_crs: Union[str, None], layers: dict, name: str) -> None:
        layer_tree_root = QgsProject.instance().layerTreeRoot()
        new_layer_group = layer_tree_root.insertGroup(0, name)
        if new_layer_group is None:
            return
        
        if preferred_crs is None:
            # Get first non-web layer for crs information
            layers_iter = iter(layers.values())
            first_layer = next(layers_iter, None)
            while True:
                if first_layer is None:
                    return
                
                layer_type = first_layer.get('type', 'ogc_wms')
                
                if layer_type == 'web':
                    first_layer = next(layers_iter, None)
                    continue
                
                break
            
            supported_auth_ids = first_layer.get('valid_epsg', None)
            layer_name = first_layer.get('name', "Fehler")
            
            preferred_crs = self.get_crs(supported_auth_ids, layer_name)
            if preferred_crs is None:
                return
        
        for layer in layers.values():
            sub_layer = self.add_layer(layer, preferred_crs, False)
            if sub_layer is None:
                continue
            ltl = new_layer_group.insertLayer(0, sub_layer)
            if ltl:
                ltl.setExpanded(False)
                visible = PropertyManager.is_visible(layer[config.InternalProperties.PATH])
                ltl.setItemVisibilityChecked(visible)
            
    def add_layer_combination(self, layers) -> None:
        preferred_crs = None
        
        if "layers" not in layers[0]:
            layer = layers[0]
            supported_auth_ids = layer.get('valid_epsg', None)
            layer_name = layer.get('name', "Fehler")
            
            preferred_crs = self.get_crs(supported_auth_ids, layer_name)
        else:
            temp_layers = layers[0]['layers']
            # Get first non-web layer for crs information
            layers_iter = iter(temp_layers.values())
            first_layer = next(layers_iter, None)
            while True:
                if first_layer is None:
                    return
                
                layer_type = first_layer.get('type', 'ogc_wms')
                
                if layer_type == 'web':
                    first_layer = next(layers_iter, None)
                    continue
                
                break
            
            supported_auth_ids = first_layer.get('valid_epsg', None)
            layer_name = first_layer.get('name', "Fehler")
            
            preferred_crs = self.get_crs(supported_auth_ids, layer_name)
        
        if preferred_crs is None:
            return
        
        for layer in layers:
            if "layers" not in layer:
                self.add_layer(layer, preferred_crs)
            else:
                self.add_layer_group(preferred_crs, layer['layers'], layer['name'])