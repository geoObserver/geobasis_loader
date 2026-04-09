from __future__ import annotations
import re
from functools import partial
from typing import Dict, Union, Optional
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtGui import QIcon, QColor, QDesktopServices
from qgis.PyQt.QtCore import QUrl, QObject
# from qgis.PyQt.QtWebKitWidgets import QWebView # type: ignore
from qgis.core import QgsSettings, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer, QgsLayerTree, QgsSymbolLayer, QgsWkbTypes, QgsMessageLog, Qgis
from qgis.gui import QgisInterface
from .topic_search import SearchFilter
from . import config
from . import ui as custom_ui
from .catalog_manager import CatalogManager

if Qgis.versionInt() < 33000:   # Breaking chnage in Version 3.30 -> Geometry types now in Qgis instead of QgsWkbTypes
    geometry_types = QgsWkbTypes.Type       # type: ignore
else:
    geometry_types = Qgis.WkbType

STAR_PREFIX = "\u2605 "  # ★

class GeoBasis_Loader(QObject):
    services = None
    search_filter = None

# =========================================================================
    def __init__(self, iface: QgisInterface, parent = None) -> None:
        super().__init__(parent)
        self.iface = iface
        self.qgs_settings = QgsSettings()
        CatalogManager.setup(iface)
        CatalogManager.get_overview(callback=self.initGui)
        
        # ------- Dialog für die EPSG-Auswahl erstellen
        self.epsg_dialog = custom_ui.EpsgDialog(parent=iface.mainWindow())
        
        # ------- Dialog für die Einstellungen erstellen
        self.settings_dialog = custom_ui.SettingsDialog(parent=iface.mainWindow())

        # ------- Letzten Katalog laden --------------------------------------------
        current_catalog = self.qgs_settings.value(config.CURRENT_CATALOG_SETTINGS_KEY)
        if current_catalog is not None and "name" in current_catalog:
            CatalogManager.get_catalog(current_catalog["titel"], current_catalog["name"], self.set_services)
            
        # ------- Letzte Einstellung für automatisches Koordinatensystem laden -----
        self.automatic_crs = self.qgs_settings.value(config.AUTOMATIC_CRS_SETTINGS_KEY, False, bool)

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
            action = self.main_menu.addAction(self.qgs_settings.value(config.CURRENT_CATALOG_SETTINGS_KEY)["titel"])
            self.main_menu.addSeparator()

            # ------- Favoriten-Menü erstellen ---------------------------
            favorites_menu = self._build_favorites_menu()
            if favorites_menu is not None:
                self.main_menu.addMenu(favorites_menu)
                self.main_menu.addSeparator()

            # ------- Menübaum bauen und einfügen ------------------------
            for state in self.services:
                # Falls der zweite Eintrag kein Dictionary ist, überspringen, da es Metadata ist
                if not isinstance(state[1], dict) or not state[1][config.InternalProperties.VISIBILITY]:
                    continue
                menu = self.gui_for_one_topic(state[1]['themen'], state[0])
                
                # Compatibility, can be removed later
                if "menu" in state[1]:
                    action = self.main_menu.addAction(state[1]['menu'])
                else:
                    action = self.main_menu.addAction(state[1]['bundeslandname'])
                action.setMenu(menu)
                if state[0] == 'de':
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
        
        self.main_menu.addAction("Einstellungen (Aktueller Katalog)", self.open_settigs)
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
        
    def _build_favorites_menu(self) -> Union[QMenu, None]:
        """Collect all favorited entries from the current catalog into a menu."""
        favorites = CatalogManager.properties.get(config.InternalProperties.FAVORITE, {})
        if not any(favorites.values()):
            return None

        catalog_dict = dict(self.services)
        entries: list[tuple[str, str]] = []  # (name, path)

        def _collect(data: dict, path_prefix: str = ""):
            for key, value in data.items():
                if not isinstance(value, dict):
                    continue
                path = f"{path_prefix}/{key}" if path_prefix else key
                if key in ("themen", "layers"):
                    _collect(value, path)
                    continue
                if favorites.get(path, False) and "name" in value:
                    entries.append((value["name"], path))
                _collect(value, path)

        _collect(catalog_dict)

        if not entries:
            return None

        menu = QMenu(STAR_PREFIX + "Favoriten", self.main_menu)
        menu.setObjectName("favorites-menu")
        menu.setToolTipsVisible(True)

        for name, path in entries:
            action = QAction(STAR_PREFIX + name, menu)
            action.setData(path)
            action.triggered.connect(self.add_topic)
            menu.addAction(action)

        return menu

    def gui_for_one_topic(self, topic_dict: dict, topic_abbreviation: str) -> QMenu:
        favorites = CatalogManager.properties.get(config.InternalProperties.FAVORITE, {})

        def _create_action(name: str, parent: QMenu, path: str, tip: str = "Thema hinzufügen", slot = self.add_topic) -> QAction:
            display_name = STAR_PREFIX + name if favorites.get(path, False) else name
            action = QAction(display_name, parent)
            action.setObjectName(name)
            action.setStatusTip(tip)
            action.setToolTip(tip)
            action.setData(path)
            action.triggered.connect(slot)
            return action
        
        menu = QMenu(topic_abbreviation, self.main_menu)
        menu.setObjectName('loader-' + topic_abbreviation)
        menu.setToolTipsVisible(True)
        
        for baseLayer in topic_dict.values():
            if not baseLayer[config.InternalProperties.VISIBILITY]:
                continue
            
            if baseLayer.get("type", "").lower() == "web":
                action = _create_action(baseLayer["name"], menu, baseLayer["uri"], "Informationen öffnen", self.open_web_site)
                menu.addAction(action)
                continue
            
            if isinstance(baseLayer.get("layers", []), dict):
                layergroup_menu = QMenu(baseLayer["name"], menu)
                layergroup_menu.setToolTipsVisible(True)
                
                add_all_action = _create_action("Alle laden", layergroup_menu, baseLayer[config.InternalProperties.PATH], "Alle Themen der Gruppe laden")
                layergroup_menu.addAction(add_all_action)
                layergroup_menu.addSeparator()

                for _, layer in baseLayer["layers"].items():
                    if not layer[config.InternalProperties.VISIBILITY]:
                        continue
                    
                    if layer.get("type", "").lower() == "web":
                        sublayer_action = _create_action(layer["name"], layergroup_menu, layer["uri"], "Informationen öffnen", self.open_web_site)
                    else:
                        sublayer_action = _create_action(layer["name"], layergroup_menu, layer[config.InternalProperties.PATH])
                    layergroup_menu.addAction(sublayer_action)

                menu.addMenu(layergroup_menu)
            else:        
                action = _create_action(baseLayer['name'], menu, baseLayer[config.InternalProperties.PATH])            
                menu.addAction(action)
                
            if "seperator" in baseLayer:
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

    def open_settigs(self) -> None:
        status = self.settings_dialog.exec()
        # Abbruch
        if status == 0:
            return
        
        self.automatic_crs = self.qgs_settings.value(config.AUTOMATIC_CRS_SETTINGS_KEY, False, bool)
        
        self.iface.messageBar().pushMessage(config.PLUGIN_NAME_AND_VERSION, 'Einstellungen erfolgreich gespeichert', level=Qgis.MessageLevel.Success, duration=3)
        self.initGui()

    def toggle_automatic_crs(self) -> None:
        new_state = not self.automatic_crs
        
        self.automatic_crs = new_state
        self.qgs_settings.setValue(config.AUTOMATIC_CRS_SETTINGS_KEY, new_state)

    def open_web_site(self):
        sender = self.sender()
        if not sender or not isinstance(sender, QAction):
            return
        
        data = sender.data() # type: ignore
        url = QUrl(data)
        
        # Opens webpage in the standard browser
        QDesktopServices.openUrl(url)
        
    def change_current_catalog(self, catalog: dict):
        self.qgs_settings.setValue(config.CURRENT_CATALOG_SETTINGS_KEY, catalog)
        CatalogManager.get_catalog(catalog["titel"], callback=self.set_services)
        
    def set_services(self, services: Dict):
        current_catalog = self.qgs_settings.value(config.CURRENT_CATALOG_SETTINGS_KEY)
        titel = current_catalog["titel"]
        name = current_catalog["name"]
        version = re.findall(r'v\d+', name)[0]
        self.iface.messageBar().pushMessage(config.PLUGIN_NAME_AND_VERSION, 'Lese '+ titel + ", Version " + version + ' ...', level=Qgis.MessageLevel.Success, duration=3)
        
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
            catalog_title = self.qgs_settings.value(config.CURRENT_CATALOG_SETTINGS_KEY)["titel"]

        catalog: dict = dict(CatalogManager.get_catalog(catalog_title)) # type: ignore
        topic = catalog
        for key in path.split("/"):
            topic = topic[key]
        
        if "layers" not in topic:
            self.addLayer(topic, None)
            return
        
        layers = topic["layers"]
        if isinstance(layers, list):
            combination_layers = []
            group_key = path.split("/")[0]
            for layer in layers:
                sub_topic = catalog[group_key]["themen"][layer]
                combination_layers.append(sub_topic)
            self.addLayerCombination(combination_layers)
        else:
            self.addLayerGroup(None, layers, topic["name"])
    
    def addLayer(self, attributes: Dict, crs: Union[str, None], standalone: bool = True):
        if not attributes.get(config.InternalProperties.LOADING, True):
            return None
        
        layerType = attributes.get('type', 'ogc_wms').lower()
        if layerType == "web":
            return None
        
        uri: str = attributes.get('uri', "n.n.")
        valid_epsg_codes: list[str] = attributes.get('valid_epsg', [])
       
        if crs not in valid_epsg_codes or crs is None:       
            crs = self.get_crs(valid_epsg_codes, attributes.get('name', "Fehler"))
            if crs is None:
                return
        
        # if crs == "OGC:CRS84":
        #     crs = "CRS:84"
        
        uri = re.sub(r'EPSG:placeholder', crs, uri)

        if layerType != "ogc_wfs" and layerType != "ogc_api_features":
            uri += "&stepHeight=3000&stepWidth=3000"
        
        opacity = attributes.get('opacity', 1)
        maxScale = attributes.get('maxScale', None)
        minScale = attributes.get('minScale', None)

        fillColor = attributes.get('fillColor', [220,220,220])
        strokeColor = attributes.get('strokeColor', 'black')
        strokeWidth = attributes.get('strokeWidth', 0.3)
        
        if uri == "n.n.":
            self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + f", URL des Themas derzeit unbekannt.{'&nbsp;'}Falls gültige/aktuelle URL bekannt,{'&nbsp;'}bitte dem Autor melden.")
            return
        
        if layerType == "ogc_wfs":
            layer = QgsVectorLayer(uri, attributes['name'], 'wfs')
        elif layerType == "ogc_api_features":
            layer = QgsVectorLayer(uri, attributes['name'], 'oapif')
        elif layerType == "ogc_vectortiles":
            layer = QgsVectorTileLayer(uri, attributes['name'])
            layer.loadDefaultStyle()
        elif layerType == "ogc_wcs":
            layer = QgsRasterLayer(uri, attributes['name'], 'wcs')
        else:
            layer = QgsRasterLayer(uri, attributes['name'], 'wms')

        if not layer.isValid():
            self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + config.MY_CRITICAL_2)
            return
        
        if hasattr(layer, 'setOpacity'):
            layer.setOpacity(opacity)
            
        if isinstance(layer, QgsVectorLayer):
            if maxScale is None:
                maxScale = 1.0
            if minScale is None:
                minScale = 25000
        
        if minScale is not None and maxScale is not None:
            if minScale < maxScale:
                self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + "; Skalenwerte vertauscht oder fehlerhaft")
            elif minScale == maxScale: 
                self.iface.messageBar().pushCritical(config.PLUGIN_NAME_AND_VERSION, config.MY_CRITICAL_1 + attributes['name'] + "; Skalenwerte gleich")   
            elif minScale > maxScale:
                layer.setMinimumScale(minScale)
                layer.setMaximumScale(maxScale)
                layer.setScaleBasedVisibility(True)
        
        if isinstance(layer, QgsVectorLayer):
            fill_color: QColor = QColor(*[int(c) for c in fillColor]) if isinstance(fillColor, list) else QColor(fillColor)
            strokeColor: QColor = QColor(*[int(c) for c in strokeColor]) if isinstance(strokeColor, list) else QColor(strokeColor)
            
            symbol_layer: QgsSymbolLayer = layer.renderer().symbol().symbolLayer(0)
            symbol_layer.setColor(fill_color)
            
            geom_type = QgsWkbTypes.singleType(QgsWkbTypes.flatType(layer.wkbType()))
            if geom_type == geometry_types.LineString:
                symbol_layer.setWidth(strokeWidth)  
            elif geom_type == geometry_types.Polygon:
                symbol_layer.setStrokeColor(strokeColor)
                symbol_layer.setStrokeWidth(strokeWidth)
            elif geom_type == geometry_types.Point:
                symbol_layer.setSize(strokeWidth)
            else:
                QgsMessageLog.logMessage("Fehler bei Bestimmung der Geometrieart; Bestimmte Geometrie " + QgsWkbTypes.displayString(geom_type), config.PLUGIN_NAME, level=Qgis.MessageLevel.Warning)
                        
        self.iface.messageBar().pushMessage(config.PLUGIN_NAME_AND_VERSION, config.MY_INFO_1 + attributes['name'] + config.MY_INFO_2, level=Qgis.MessageLevel.Success, duration=1)
        # Ebene zum Projekt hinzufügen aber nicht automatisch zum Ebenenbaum
        QgsProject.instance().addMapLayer(layer, False) # type: ignore

        if standalone:
            root: QgsLayerTree = QgsProject.instance().layerTreeRoot()
            ltl = root.insertLayer(0, layer)
            if ltl:
                ltl.setExpanded(False)
                visible = attributes.get(config.InternalProperties.VISIBILITY, True)
                ltl.setItemVisibilityChecked(visible)

        if isinstance(layer, QgsVectorLayer):
            layer.triggerRepaint()
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())

        return layer
    
    def _first_non_web_layer(self, layers: dict) -> Union[dict, None]:
        """Return the first layer entry whose type is not 'web', or None."""
        for layer in layers.values():
            if layer.get('type', 'ogc_wms') != 'web':
                return layer
        return None

    def _resolve_crs(self, layers: dict) -> Union[str, None]:
        """Determine CRS from the first non-web layer via user dialog."""
        first_layer = self._first_non_web_layer(layers)
        if first_layer is None:
            return None
        return self.get_crs(first_layer.get('valid_epsg', None), first_layer.get('name', "Fehler"))

    def addLayerGroup(self, preferred_crs: Union[str, None], layers: dict, name: str) -> None:
        layerTreeRoot = QgsProject.instance().layerTreeRoot()
        newLayerGroup = layerTreeRoot.insertGroup(0, name)
        if newLayerGroup is None:
            return

        if preferred_crs is None:
            preferred_crs = self._resolve_crs(layers)
            if preferred_crs is None:
                return

        for layerKey in layers:
            sub_layer = self.addLayer(layers[layerKey], preferred_crs, False)
            if sub_layer is None:
                continue
            ltl = newLayerGroup.insertLayer(0, sub_layer)
            if ltl:
                ltl.setExpanded(False)
                visible = layers[layerKey].get(config.InternalProperties.VISIBILITY, True)
                ltl.setItemVisibilityChecked(visible)

    def addLayerCombination(self, layers) -> None:
        preferred_crs = None

        if "layers" not in layers[0]:
            layer = layers[0]
            preferred_crs = self.get_crs(layer.get('valid_epsg', None), layer.get('name', "Fehler"))
        else:
            preferred_crs = self._resolve_crs(layers[0]['layers'])

        if preferred_crs is None:
            return

        for layer in layers:
            if "layers" not in layer:
                self.addLayer(layer, preferred_crs)
            else:
                self.addLayerGroup(preferred_crs, layer['layers'], layer['name'])