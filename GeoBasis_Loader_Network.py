import os
import json
import email.utils
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QObject, pyqtSignal
from qgis.core import *

class NetworkHandler(QObject):
    __JSON_URL = "https://geoobserver.de/download/GeoBasis_Loader_v2_dev.json"
    __PLUGIN_DIR = os.path.dirname(__file__)
    __JSON_FILE_PATH = __PLUGIN_DIR + "/" + "Data.json"
    
    __iface = None
    __manager: QgsNetworkAccessManager = None
    __reply: QNetworkReply = None
    
    finished = pyqtSignal(dict)
    
    def __init__(self, pluginName, iface, manager) -> None:
        super().__init__()
        self.__pluginName = pluginName
        self.__iface = iface
        self.__manager = manager
        
    def fetchUrlJSON(self):
        url = QUrl(self.__JSON_URL)
        request = QNetworkRequest(url)
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)   
        self.__reply = self.__manager.get(request)      
        self.__reply.finished.connect(self.__handleResponse)
        
    def __handleResponse(self):
        error = self.__reply.error()
        
        if error == 0:
            jsonString = self.__reply.readAll().data().decode()
            services = json.loads(jsonString)
            self.finished.emit(services)
            
            # Holt sich die Timestamps der letzten Modifikationen der lokalen JSON-Datei und der JSON-Datei aus dem Internet
            # (Über-)Schreibt dann die loakle JSON-Datei, wenn die Datei im Internet neuer ist
            # Sozusagen eigene Cache-Implementation 
            networkLastModifiedRawValue = self.__reply.rawHeader(bytearray('Last-Modified', "utf-8")).data().decode()
            networkLastModified = email.utils.parsedate_to_datetime(networkLastModifiedRawValue).timestamp()
            localLastModified = os.path.getmtime(self.__JSON_FILE_PATH) if os.path.exists(self.__JSON_FILE_PATH) else 0.0
            
            if localLastModified < networkLastModified:
                self.__writeJson(jsonString)
                
            return

        if os.path.exists(self.__JSON_FILE_PATH):
            self.__iface.messageBar().pushWarning(self.__pluginName, "Netzwerkfehler beim Laden der URL's, Verwendung der gecachten Daten")
            services = self.__readJson()
            self.finished.emit(services)
        else:
            self.__iface.messageBar().pushCritical(self.__pluginName, "Netzwerkfehler beim Laden der URL's, Überprüfen Sie die Internetverbindung oder kontaktieren Sie den Autor")
        
    def __writeJson(self, data: str):
        mode = "w" if os.path.exists(self.__JSON_FILE_PATH) else "x"
        
        with open(self.__JSON_FILE_PATH, mode, encoding="utf-8", newline="\n") as file:
            file.write(data)
            
    def __readJson(self):
        services = None
        with open(self.__JSON_FILE_PATH, "r", encoding="utf-8") as file:
            data = file.read()
            services = json.loads(data)
        return services

    def getURL(self):
        return self.__JSON_URL
