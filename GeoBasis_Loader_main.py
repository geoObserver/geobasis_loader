from functools import partial
import json
from typing import Dict
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
#from PyQt5.QtWebKitWidgets import QWebView # type: ignore
from qgis.core import *
from qgis.utils import *
from .GeoBasis_Loader_Network import NetworkHandler

class GeoBasis_Loader:
    version = u'0.8_dev'
    myPlugin = u'GeoBasis Loader'
    myPluginGB = myPlugin + u' >>>>>'
    myPluginV = myPlugin + u' (v' + version + ')'
    myCritical_1 = u'Layerladefehler '
    myCritical_2 = u', Dienst nicht verfügbar (URL?)'
    myInfo_1 = u'Layer '
    myInfo_2 = u' erfolgreich geladen.'
    
    plugin_dir = os.path.dirname(__file__)
    networkHandler = None
    services = None

# =========================================================================
    def __init__(self, iface):   
        self.networkHandler = NetworkHandler(self.myPluginV, iface, QgsNetworkAccessManager.instance())
        self.networkHandler.finished.connect(self.getServices)
        self.networkHandler.fetchUrlJSON()        

        self.iface = iface
        icon = QIcon(self.plugin_dir + "/GeoBasis_Loader_icon.png")
        self.mainMenu = QMenu(self.myPluginV)
        self.mainMenu.setIcon(icon)
        self.iface.pluginMenu().addMenu(self.mainMenu)
        # self.fetchUrlJSON()       
        #self.iface.messageBar().pushMessage(self.myPluginV,f'Sollte Euch das Plugin gefallen,{"&nbsp;"}könnt Ihr es gern mit Eurer Mitarbeit,{"&nbsp;"}einem Voting und ggf.{"&nbsp;"}einem kleinen Betrag unterstützen ...{"&nbsp;"}Danke!!', 3, 8)
        #self.iface.messageBar().pushMessage(self.myPluginV,u'Lese JSON: ' + self.networkHandler.getURL() + ' ...', 3, 8)

    
    def initGui(self):    
        if self.services is None:
            return
        
        # ------- Menübaum bauen und einfügen ------------------------
        for state in self.services:
            menu = self.buildGUIOneState(self.services[state]['themen'], state)
            action = self.mainMenu.addAction(self.services[state]['bundeslandname'])
            action.setMenu(menu)
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        self.mainMenu.addSeparator()
        self.mainMenu.addAction("Über ...", partial(self.openWebSite, 'https://geoobserver.de/qgis-plugin-geobasis-loader/'))        
        
        # ------- Status-Schaltfläche für #geoObserver ------------------------
        self.mainMenu.addAction("Status ...", partial(self.openWebSite, 'https://geoobserver.de/qgis-plugin-geobasis-loader/#statustabelle'))        
        
        # ------- Status-Schaltfläche für #geoObserver ------------------------
        self.mainMenu.addAction("FAQs ...", partial(self.openWebSite, 'https://geoobserver.de/qgis-plugin-geobasis-loader/#faq'))        
        
    def buildGUIOneState(self, stateDict: Dict, stateAbbr):
        menu = QMenu(stateAbbr)
        menu.setObjectName('loader-' + stateAbbr)
        for baseLayer in stateDict:
            if "layers" not in stateDict[baseLayer]:
                action = menu.addAction(stateDict[baseLayer]['name'], partial(self.addLayer, stateDict[baseLayer]))
            else:
                layers = stateDict[baseLayer]["layers"]
                if type(layers) == list:
                    combinationLayers = []
                    for layer in layers:
                        combinationLayers.append(stateDict[layer])
                    action = menu.addAction(stateDict[baseLayer]['name'], partial(self.addLayerCombination, combinationLayers))
                else:
                    action = menu.addAction(stateDict[baseLayer]['name'], partial(self.addLayerGroup, layers, stateDict[baseLayer]['name']))
            action.setObjectName(stateDict[baseLayer]['name'])
            if "seperator" in stateDict[baseLayer]:
                menu.addSeparator()
        return menu     
    
#===================================================================================

    def unload(self):
        if self.mainMenu:
            self.iface.pluginMenu().removeAction(self.mainMenu.menuAction())

#=================================================================================== 

    def openWebSite(self, url):
        url = QUrl(url)
        
        # Opens webpage in the standard browser
        QDesktopServices.openUrl(url)
       
        # ------ Öffne QGIS Fenster mit WebPage ---------------- 
        # self.webWindow = QWebView(None)
        # self.webWindow.setWindowTitle("GeoObserver")
        # self.webWindow.load(url)
        # self.webWindow.show()
        
    def getServices(self, services):
        self.services = services        
        self.initGui()
            
        
    def addLayer(self, attributes: Dict, standalone: bool = True):
        uri = attributes.get('uri', "n.n.")
        layerType = attributes.get('type', 'wms')
        
        opacity = attributes.get('opacity', 1)
        maxScale = attributes.get('maxScale', NULL)
        minScale = attributes.get('minScale', NULL)

        fillColor = attributes.get('fillColor', [220,220,220])
        strokeColor = attributes.get('strokeColor', 'black')
        strokeWidth = attributes.get('strokeWidth', 0.3)
        
        if uri == "n.n.":
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + f", URL des Themas derzeit unbekannt.{'&nbsp;'}Falls gültige/aktuelle URL bekannt,{'&nbsp;'}bitte dem Autor melden.")
            return
        
        if layerType == "wfs":
            layer = QgsVectorLayer(uri, attributes['name'], 'WFS')
        elif layerType == "vectorTiles":
            layer = QgsVectorTileLayer(uri, attributes['name'])
            layer.loadDefaultStyle()
        else:
            layer = QgsRasterLayer(uri, attributes['name'], 'wms')

        if not layer.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + self.myCritical_2)
            return;
        
        layer.setOpacity(opacity) 
        if layerType == 'wfs' and (maxScale == NULL or minScale == NULL):
            maxScale = 1.0
            minScale = 25000    
        
        if minScale < maxScale:
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + "; Skalenwerte vertauscht oder fehlerhaft")
        elif minScale == maxScale and minScale != NULL: 
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + attributes['name'] + "; Skalenwerte gleich")   
        elif minScale > maxScale:
            layer.setMinimumScale(minScale)
            layer.setMaximumScale(maxScale)
            layer.setScaleBasedVisibility(True)
                
        if layerType == 'wfs':         
            color = QColor(int(fillColor[0]), int(fillColor[1]), int(fillColor[2])) if type(fillColor) == list else QColor(fillColor)
            layer.renderer().symbol().setColor(color)
            color = QColor(int(strokeColor[0]), int(strokeColor[1]), int(strokeColor[2])) if type(strokeColor) == tuple else QColor(strokeColor)
            layer.renderer().symbol().symbolLayer(0).setStrokeColor(color)
            layer.renderer().symbol().symbolLayer(0).setStrokeWidth(strokeWidth)
            
            layer.triggerRepaint()
            iface.layerTreeView().refreshLayerSymbology(layer.id())
        
        iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + attributes['name'] + self.myInfo_2, 3, 1)
        QgsProject.instance().addMapLayer(layer, standalone)
        if not standalone:
            return layer
    
    def addLayerGroup(self, layers, name):
        layerTreeRoot = QgsProject.instance().layerTreeRoot()
        newLayerGroup = layerTreeRoot.insertGroup(0, name)
        for layerKey in layers:
            subLayer = self.addLayer(layers[layerKey], False)
            newLayerGroup.addLayer(subLayer)
            
    def addLayerCombination(self, layers):
        for layer in layers:
            if "layers" not in layer:
                self.addLayer(layer)
            else:
                self.addLayerGroup(layer['layers'], layer['name'])  
