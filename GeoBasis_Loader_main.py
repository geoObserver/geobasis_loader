import re, os
from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QUrl
# from PyQt5.QtWebKitWidgets import QWebView # type: ignore
from .dialog import EpsgDialog
from qgis.core import QgsSettings, QgsProject, QgsNetworkAccessManager, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer
from qgis.utils import *
from qgis._gui import QgisInterface
from typing import Dict, Union
from .GeoBasis_Loader_Network import NetworkHandler

class GeoBasis_Loader:
    version = u'1.2_dev'
    myPlugin = u'GeoBasis Loader'
    myPluginGB = myPlugin + u' >>>>>'
    myPluginV = myPlugin + u' (v' + version + ')'
    myCritical_1 = u'Layerladefehler '
    myCritical_2 = u', Dienst nicht verfügbar (URL?)'
    myInfo_1 = u'Layer '
    myInfo_2 = u' erfolgreich geladen.'
    
    plugin_dir = os.path.dirname(__file__)
    user_settings = QgsSettings()
    current_catalog_settings_key = 'geobasis_loader/current_catalog'
    automatic_crs_settings_key = 'geobasis_loader/automatic_crs'
    
    catalog_network_handler = None
    overview_network_handler = None
    services = None
    catalogs = None

# =========================================================================
    def __init__(self, iface: QgisInterface) -> None:   
        # ------- Network Handler für die einzelnen Kataloge erstellen -------------
        self.catalog_network_handler = NetworkHandler(self.myPluginV, iface, QgsNetworkAccessManager.instance())
        self.catalog_network_handler.finished.connect(self.set_services)
        # ------- Network Handler für die Katalog Übersicht erstellen --------------
        self.overview_network_handler = NetworkHandler(self.myPluginV, iface, QgsNetworkAccessManager.instance())
        self.overview_network_handler.finished.connect(self.set_catalogs)
        self.overview_network_handler.fetch_catalog_overview()
        
        # ------- Dialog für die EPSG-Auswahl erstellen
        self.epsg_dialog = EpsgDialog(parent=iface.mainWindow())

        # ------- Letzten Katalog laden --------------------------------------------
        current_catalog = self.user_settings.value(self.current_catalog_settings_key)
        if current_catalog is not None:
            self.catalog_network_handler.fetch_catalog(current_catalog["url"])
            
        # ------- Letzte Einstellung für automatisches Koordinatensystem laden -----
        saved_option = self.user_settings.value(self.automatic_crs_settings_key, "false")
        self.automatic_crs = False if saved_option == "false" else True

        self.iface = iface
        icon = QIcon(self.plugin_dir + "/GeoBasis_Loader_icon.png")
        self.main_menu = QMenu(self.myPluginV)
        self.main_menu.setIcon(icon)
        self.iface.pluginMenu().addMenu(self.main_menu)
        # self.fetchUrlJSON()       
        #self.iface.messageBar().pushMessage(self.myPluginV,f'Sollte Euch das Plugin gefallen,{"&nbsp;"}könnt Ihr es gern mit Eurer Mitarbeit,{"&nbsp;"}einem Voting und ggf.{"&nbsp;"}einem kleinen Betrag unterstützen ...{"&nbsp;"}Danke!!', 3, 8)     
    
    def initGui(self) -> None:
        # if self.main_menu 
        
        self.main_menu.clear()
        
        if self.services is not None:
            # ------- Name des Katalogs einfügen -------------------------
            action = self.main_menu.addAction(self.user_settings.value(self.current_catalog_settings_key)["titel"])
            self.main_menu.addSeparator()
            # ------- Menübaum bauen und einfügen ------------------------
            for state in self.services:                
                
                menu = self.gui_for_one_topic(state[1]['themen'], state[0])
                action = self.main_menu.addAction(state[1]['bundeslandname'])
                action.setMenu(menu)
                if state[0] == 'de':
                    self.main_menu.addSeparator()
            
            self.main_menu.addSeparator()
            

        if self.catalogs is not None:
            # ------- Katalogmenü erstellen ------------------------------------
            menu = QMenu('catalogs')
            menu.setObjectName('catalog-overview')
            
            # ------- Einträge im Katalogmenü erstellen ------------------------
            for catalog in self.catalogs:
                action = menu.addAction(catalog["titel"], partial(self.change_current_catalog, catalog))
                action.setObjectName("open-" + catalog["titel"])
                
            # ------- Katalogmenü tum Hauptmenü hinzufügen ---------------------
            action = self.main_menu.addAction("Weitere Kataloge (Other Catalogs)")
            action.setMenu(menu)
            
            self.main_menu.addSeparator()
                
        # ------- Über-Schaltfläche für die JSON-Datei ------------------------
        action = QAction(text="Wenn möglich, Dienste automatisch im KBS laden", parent=self.main_menu, checkable=True, checked=self.automatic_crs)
        action.toggled.connect(self.toggle_automatic_crs)
        self.main_menu.addAction(action)
        self.main_menu.addSeparator()
        
        # ------- Spenden-Schaltfläche für #geoObserver ------------------------
        self.main_menu.addAction("Den GeoBasis_Loader mit einer Spende unterstützen ...", partial(self.open_web_site, 'https://geoobserver.de/support_geobasis_loader/'))
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        self.main_menu.addAction("Über ...", partial(self.open_web_site, 'https://geoobserver.de/qgis-plugin-geobasis-loader/'))

        # ------- Status-Schaltfläche für #geoObserver ------------------------
        # self.mainMenu.addAction("Status ...", partial(self.openWebSite, 'https://geoobserver.de/qgis-plugin-geobasis-loader/#statustabelle'))        
        
        # ------- Status-Schaltfläche für #geoObserver ------------------------
        # self.mainMenu.addAction("FAQs ...", partial(self.openWebSite, 'https://geoobserver.de/qgis-plugin-geobasis-loader/#faq'))
        
    def gui_for_one_topic(self, topic_dict: dict, topic_abbreviation: str) -> QMenu:        
        menu = QMenu(topic_abbreviation)
        menu.setObjectName('loader-' + topic_abbreviation)
        for baseLayer in topic_dict:
            if "layers" not in topic_dict[baseLayer]:
                action = menu.addAction(topic_dict[baseLayer]['name'], partial(self.addLayer, topic_dict[baseLayer], None))
            else:
                layers = topic_dict[baseLayer]["layers"]
                if type(layers) == list:
                    combinationLayers = []
                    for layer in layers:
                        combinationLayers.append(topic_dict[layer])
                    action = menu.addAction(topic_dict[baseLayer]['name'], partial(self.addLayerCombination, combinationLayers))
                else:
                    action = menu.addAction(topic_dict[baseLayer]['name'], partial(self.addLayerGroup, None, layers, topic_dict[baseLayer]['name']))
            action.setObjectName(topic_dict[baseLayer]['name'])
            if "seperator" in topic_dict[baseLayer]:
                menu.addSeparator()
        return menu     
    
#===================================================================================

    def unload(self):
        if self.main_menu:
            self.iface.pluginMenu().removeAction(self.main_menu.menuAction())

#=================================================================================== 

    def toggle_automatic_crs(self) -> None:
        new_state = not self.automatic_crs
        
        self.automatic_crs = new_state
        self.user_settings.setValue(self.automatic_crs_settings_key, new_state)

    def open_web_site(self, url):
        url = QUrl(url)
        
        # Opens webpage in the standard browser
        QDesktopServices.openUrl(url)
       
        # ------ Öffne QGIS Fenster mit WebPage ---------------- 
        # self.webWindow = QWebView(None)
        # self.webWindow.setWindowTitle("GeoObserver")
        # self.webWindow.load(url)
        # self.webWindow.show()
        
    def change_current_catalog(self, catalog: dict):
        self.user_settings.setValue(self.current_catalog_settings_key, catalog)
        self.catalog_network_handler.fetch_catalog(catalog["url"])
        
    def set_catalogs(self, catalogs: list[Dict[str, str]]):
        self.catalogs = catalogs
        self.initGui()
        
    def set_services(self, services: Dict):
        current_catalog = self.user_settings.value(self.current_catalog_settings_key)
        titel = current_catalog["titel"]
        url = current_catalog["url"]
        version = re.findall(r'v\d+', url)[0]
        self.iface.messageBar().pushMessage(self.myPluginV, u'Lese '+ titel + ", Version " + version + ' ...', 3, 3)   
        
        self.services = services       
        self.initGui()
    
    # Get crs from user
    def get_crs(self, supported_auth_ids: list[str], layer_name: str) -> Union[str, None]:
        if supported_auth_ids is None:
            return None
        
        current_crs = QgsProject.instance().crs().authid()          
        if current_crs not in supported_auth_ids or not self.automatic_crs:
            self.epsg_dialog.set_table_data(supported_auth_ids, layer_name)
            self.epsg_dialog.exec_()
            if self.epsg_dialog.selected_coord is None:
                return None
            current_crs = self.epsg_dialog.selected_coord
        
        if current_crs == "OGC:CRS84":
            current_crs = "CRS:84"
            
        return current_crs
    
    def addLayer(self, attributes: Dict, crs: str, standalone: bool = True):
        uri: str = attributes.get('uri', "n.n.")
        layerType = attributes.get('type', 'ogc_wms')
        valid_epsg_codes = attributes.get('valid_epsg', None)
       
        if crs not in valid_epsg_codes or crs is None:       
            crs = self.get_crs(valid_epsg_codes, attributes.get('name', "Fehler"))
            if crs is None:
                return
        
        uri = re.sub(r'EPSG:placeholder', crs, uri)
       
        # if valid_epsg_codes is not None:
        #     current_crs = QgsProject.instance().crs().authid()          
        #     if current_crs not in valid_epsg_codes or not self.automatic_crs:
        #         self.epsg_dialog.set_table_data(valid_epsg_codes, attributes.get('name', "Fehler"))
        #         self.epsg_dialog.exec_()
        #         if self.epsg_dialog.selected_coord is None:
        #             return
        #         current_crs = self.epsg_dialog.selected_coord
                
        #     if current_crs == "OGC:CRS84":
        #         current_crs = "CRS:84"
        #     uri = re.sub(r'EPSG:placeholder', current_crs, uri)

        if layerType != "ogc_wfs":
            uri += "&stepHeight=3000&stepWidth=3000"
        
        opacity = attributes.get('opacity', 1)
        maxScale = attributes.get('maxScale', None)
        minScale = attributes.get('minScale', None)

        fillColor = attributes.get('fillColor', [220,220,220])
        strokeColor = attributes.get('strokeColor', 'black')
        strokeWidth = attributes.get('strokeWidth', 0.3)
        
        if uri == "n.n.":
            self.iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + f", URL des Themas derzeit unbekannt.{'&nbsp;'}Falls gültige/aktuelle URL bekannt,{'&nbsp;'}bitte dem Autor melden.")
            return
        
        if layerType == "ogc_wfs":
            layer = QgsVectorLayer(uri, attributes['name'], 'WFS')
        elif layerType == "ogc_vectorTiles":
            layer = QgsVectorTileLayer(uri, attributes['name'])
            layer.loadDefaultStyle()
        elif layerType == "ogc_wcs":
            layer = QgsRasterLayer(uri, attributes['name'], 'wcs')
        else:
            layer = QgsRasterLayer(uri, attributes['name'], 'wms')

        if not layer.isValid():
            self.iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + self.myCritical_2)
            return
        
        if hasattr(layer, 'setOpacity'):
            layer.setOpacity(opacity)             
            
        if layerType == 'ogc_wfs':
            if maxScale is None:
                maxScale = 1.0
            if minScale is None:
                minScale = 25000
        
        if minScale is not None and maxScale is not None:
            if minScale < maxScale:
                self.iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + "; Skalenwerte vertauscht oder fehlerhaft")
            elif minScale == maxScale: 
                self.iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + "; Skalenwerte gleich")   
            elif minScale > maxScale:
                layer.setMinimumScale(minScale)
                layer.setMaximumScale(maxScale)
                layer.setScaleBasedVisibility(True)
                
        if layerType == 'ogc_wfs':         
            color = QColor(int(fillColor[0]), int(fillColor[1]), int(fillColor[2])) if type(fillColor) == list else QColor(fillColor)
            layer.renderer().symbol().setColor(color)
            color = QColor(int(strokeColor[0]), int(strokeColor[1]), int(strokeColor[2])) if type(strokeColor) == list else QColor(strokeColor)
            layer.renderer().symbol().symbolLayer(0).setStrokeColor(color)
            layer.renderer().symbol().symbolLayer(0).setStrokeWidth(strokeWidth)
            
            layer.triggerRepaint()
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        
        self.iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + attributes['name'] + self.myInfo_2, 3, 1)
        QgsProject.instance().addMapLayer(layer, standalone)
        if not standalone:
            return layer
    
    def addLayerGroup(self, preferred_crs: Union[str, None], layers: dict, name: str) -> None:
        layerTreeRoot = QgsProject.instance().layerTreeRoot()
        newLayerGroup = layerTreeRoot.insertGroup(0, name)
        
        if preferred_crs is None:
            first_layer = next(iter(layers.values()))
            supported_auth_ids = first_layer.get('valid_epsg', None)
            layer_name = first_layer.get('name', "Fehler")
            
            preferred_crs = self.get_crs(supported_auth_ids, layer_name)
            if preferred_crs is None:
                return
        
        for layerKey in layers:
            subLayer = self.addLayer(layers[layerKey], preferred_crs, False)
            newLayerGroup.addLayer(subLayer)
            
    def addLayerCombination(self, layers) -> None:
        preferred_crs = None
        
        if "layers" not in layers[0]:
            layer = layers[0]
            supported_auth_ids = layer.get('valid_epsg', None)
            layer_name = layer.get('name', "Fehler")
            
            preferred_crs = self.get_crs(supported_auth_ids, layer_name)
        else:
            temp_layers = layers[0]['layers']
            first_layer = next(iter(temp_layers.values()))
            supported_auth_ids = first_layer.get('valid_epsg', None)
            layer_name = first_layer.get('name', "Fehler")
            
            preferred_crs = self.get_crs(supported_auth_ids, layer_name)
        
        if preferred_crs is None:
            return
        
        for layer in layers:
            if "layers" not in layer:
                self.addLayer(layer, preferred_crs)
            else:
                self.addLayerGroup(preferred_crs, layer['layers'], layer['name'])