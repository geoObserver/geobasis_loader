import json, os, re
from functools import partial
import email.utils
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QObject, pyqtSignal
from qgis.core import QgsNetworkAccessManager, QgsSettings

CATALOG_OVERVIEW = "https://geoobserver.de/download/GeoBasis_Loader/GeoBasis_Loader_v4_Kataloge.json"
PLUGIN_DIR = os.path.dirname(__file__)

class NetworkHandler(QObject):
    __iface = None
    __manager: QgsNetworkAccessManager = None
    __reply: QNetworkReply = None
    
    finished = pyqtSignal(list)
    
    def __init__(self, pluginName: str, iface, manager: QgsNetworkAccessManager) -> None:
        super().__init__()
        self._pluginName = pluginName
        self.__iface = iface
        self.__manager = manager
        
    def __fetch_data(self, url: str = '') -> QNetworkReply:
        q_url = QUrl(url)
        request = QNetworkRequest(q_url)
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        return self.__manager.get(request)
  
    def fetch_catalog_overview(self) -> None:
        self.__reply = self.__fetch_data(url=CATALOG_OVERVIEW)
        self.__reply.finished.connect(partial(self.__handle_response, True))
        
    def __handle_overview_response(self):
        error = self.__reply.error()
        
        if error == 0:
            json_string = self.__reply.readAll().data().decode()
            
            ################################################################### Temporär
            json_string = json_string.replace('\r\n', '')
            json_string = re.sub(r'^{', '[', json_string)
            json_string = re.sub(r",}$", ']', json_string)
            json_string = re.sub(r"}$", ']', json_string)
            ###################################################################
            
            catalogs = json.loads(json_string)
            self.finished_overview.emit(catalogs)
  
    def fetch_catalog(self, url: str) -> None:
        self.__reply = self.__fetch_data(url=url)
        self.__reply.finished.connect(partial(self.__handle_response, False))
        
    def __handle_response(self, is_overview_response: bool):
        error = self.__reply.error()
        
        settings = QgsSettings()
        current_catalog = settings.value('geobasis_loader/current_catalog')
        file_name = re.sub(r'\ ', '_', current_catalog["titel"].split(':')[0].lower()) if not is_overview_response else 'katalog_overview'
        file_path = f'{PLUGIN_DIR}/{file_name}.json'
        
        if error == 0:
            json_string = self.__reply.readAll().data().decode()
            
            if is_overview_response:
                ################################################################### Temporär
                json_string = json_string.replace('\r\n', '')
                json_string = re.sub(r'^{', '[', json_string)
                json_string = re.sub(r",}$", ']', json_string)
                json_string = re.sub(r"}$", ']', json_string)
                ###################################################################
            
            services = json.loads(json_string)
            if not is_overview_response:
                services = list(services.items())                
                        
            self.finished.emit(services)
     
            # Holt sich die Timestamps der letzten Modifikationen der lokalen JSON-Datei und der JSON-Datei aus dem Internet
            # (Über-)Schreibt dann die loakle JSON-Datei, wenn die Datei im Internet neuer ist
            # Sozusagen eigene Cache-Implementation             
            networkLastModifiedRawValue = self.__reply.rawHeader(bytearray('Last-Modified', "utf-8")).data().decode()
            networkLastModified = email.utils.parsedate_to_datetime(networkLastModifiedRawValue).timestamp()
            localLastModified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0
            if localLastModified < networkLastModified:
                self.__write_json(json_string, file_path)

            return

        if not os.path.exists(file_path):
            self.__iface.messageBar().pushCritical(self._pluginName, "Netzwerkfehler beim Laden der URL's, Überprüfen Sie die Internetverbindung oder kontaktieren Sie den Autor")
            return

        services = self.__read_json(file_path)
        if not is_overview_response:
            services = list(services.items())
        self.finished.emit(services)
        self.__iface.messageBar().pushWarning(self._pluginName, "Netzwerkfehler beim Laden der URL's, Verwendung der gecachten Daten")
        
    def __write_json(self, data: str, file_path: str) -> None:
        mode = "w" if os.path.exists(file_path) else "x"
        
        with open(file_path, mode, encoding="utf-8", newline="\n") as file:
            file.write(data)
            
    def __read_json(self, file_path: str) -> dict:
        services: dict | list = None
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read()
            services = json.loads(data)
        return services