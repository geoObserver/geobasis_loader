from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QUrl
from PyQt5.QtWebKitWidgets import QWebView # type: ignore
from qgis.core import *
from qgis.utils import *
from . import GeoBasis_Loader_Data

class GeoBasis_Loader:
    version = u'0.3'
    myPlugin = u'GeoBasis Loader'
    myPluginGB = myPlugin + u' >>>>>'
    myPluginV = myPlugin + u' (v' + version + ')'
    myCritical_1 = u'Fehler beim Laden des Layers '
    myCritical_2 = u', Dienst nicht verfügbar (URL?)'
    myInfo_1 = u'Layer '
    myInfo_2 = u' erfolgreich geladen.'
    
    plugin_dir = os.path.dirname(__file__)

# =========================================================================
    def __init__(self, iface):
        self.iface = iface
        icon = QIcon(self.plugin_dir + "/GeoBasis_Loader_icon.png")
        self.mainMenu = QMenu(self.myPluginV)
        self.mainMenu.setIcon(icon)
        self.iface.pluginMenu().addMenu(self.mainMenu)
    
    def initGui(self):
        # ------- Menübaum bauen und einfügen ------------------------
        for stateName in GeoBasis_Loader_Data.services:
            menu = self.buildGUIOneState(GeoBasis_Loader_Data.services[stateName]['themen'], stateName)
            action = self.mainMenu.addAction(GeoBasis_Loader_Data.services[stateName]['bundeslandname'])
            action.setMenu(menu)
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        self.mainMenu.addSeparator()
        self.mainMenu.addAction("Über ...", self.openWebSite)        
        
        # ------- Status-Schaltfläche für #geoObserver ------------------------
        self.mainMenu.addAction("Status ...", self.openWebSite2)        
        
        # ------- Status-Schaltfläche für #geoObserver ------------------------
        self.mainMenu.addAction("FAQs ...", self.openWebSite3)        
        
    def buildGUIOneState(self, stateDict: Dict, stateAbbr):
        menu = QMenu("test")
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
            if "seperator" in stateDict[baseLayer] and stateDict[baseLayer]["seperator"]:
                menu.addSeparator()
        return menu     
    
#===================================================================================

    def unload(self):
        if self.mainMenu:
            self.iface.pluginMenu().removeAction(self.mainMenu.menuAction())

#=================================================================================== 

    def openWebSite(self):
        url = QUrl('https://geoobserver.de/qgis-plugin-geobasis-loader/')
        
        # Opens webpage in the standard browser
        QDesktopServices.openUrl(url)
       
        # ------ Öffne QGIS Fenster mit WebPage ---------------- 
        # self.webWindow = QWebView(None)
        # self.webWindow.setWindowTitle("GeoObserver")
        # self.webWindow.load(url)
        # self.webWindow.show()
    
    def openWebSite2(self):
        url = QUrl('https://geoobserver.de/qgis-plugin-geobasis-loader/#statustabelle')
        QDesktopServices.openUrl(url)
        
    def openWebSite3(self):
        url = QUrl('https://geoobserver.de/qgis-plugin-geobasis-loader/#faq')
        QDesktopServices.openUrl(url)
        
    def addLayer(self, attributes: Dict, standalone: bool = True):
        layerType = attributes['type'] if 'type' in attributes else "wms"
        
        opacity = attributes["opacity"] if "opacity" in attributes else 1
        maxScale = attributes["maxScale"] if "maxScale" in attributes else NULL
        minScale = attributes["minScale"] if "minScale" in attributes else NULL
        
        fillColor = attributes["fillColor"] if "fillColor" in attributes else (220,220,220)
        strokeColor = attributes["strokeColor"] if "strokeColor" in attributes else "black"
        strokeWidth = attributes["strokeWidth"] if "strokeWidth" in attributes else 0.3
        
        print(attributes['uri'])
        layer = QgsRasterLayer(attributes['uri'], attributes['name'], 'wms') if layerType == 'wms' else QgsVectorLayer(attributes['uri'], attributes['name'], 'WFS')
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
            color = (0x1000 * fillColor[0] + 0x100 * fillColor[1] + fillColor[2]) if type(fillColor) == tuple else fillColor
            layer.renderer().symbol().setColor(QColor(color))
            color = (0x1000 * strokeColor[0] + 0x100 * strokeColor[1] + strokeColor[2]) if type(strokeColor) == tuple else strokeColor
            layer.renderer().symbol().symbolLayer(0).setStrokeColor(QColor(color))
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
            # print(layer)
            if "layers" not in layer:
                self.addLayer(layer)
            else:
                self.addLayerGroup(layer['layers'], layer['name'])  
            
#Baden-Württemberg	BW
#Bayern (Freistaat)	BY
#Berlin	BE
#Brandenburg	BB
#Bremen (Hansestadt)	HB
#Hamburg (Hansestadt)	HH
#Hessen	HE
#Mecklenburg-Vorpommern	MV
#Niedersachsen	NI
#Nordrhein-Westfalen	NW
#Rheinland-Pfalz	RP
#Saarland	SL
#Schleswig-Holstein	SH