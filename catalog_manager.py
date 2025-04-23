import json, os, re
from functools import partial
import email.utils
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QObject, pyqtSignal
from qgis.core import QgsNetworkAccessManager, QgsSettings
from qgis._gui import QgisInterface
from . import config

class NetworkHandler(QObject):
    __iface = None
    __manager: QgsNetworkAccessManager = None
    __reply: QNetworkReply = None
    
    finished = pyqtSignal(list, str, float)
    error_occurred = pyqtSignal(str, str)
    
    def __init__(self, iface: QgisInterface, manager: QgsNetworkAccessManager) -> None:
        super().__init__()
        self.__iface = iface
        self.__manager = manager
        
    def __fetch_data(self, url: str = '') -> QNetworkReply:
        q_url = QUrl(url)
        request = QNetworkRequest(q_url)
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        return self.__manager.get(request)
  
    def fetch_catalog_overview(self) -> None:
        self.__reply = self.__fetch_data(url=config.CATALOG_OVERVIEW)
        self.__reply.finished.connect(partial(self.__handle_response, "overview", True))
  
    def fetch_catalog(self, url: str, catalog_name: str) -> None:
        self.__reply = self.__fetch_data(url=url)
        self.__reply.finished.connect(partial(self.__handle_response, catalog_name, False))
        
    def __handle_response(self, catalog_name: str, is_overview_response: bool):
        error = self.__reply.error()
        
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
                        
     
            # Holt sich die Timestamps der letzten Modifikationen der lokalen JSON-Datei und der JSON-Datei aus dem Internet
            # (Über-)Schreibt dann die loakle JSON-Datei, wenn die Datei im Internet neuer ist
            # Sozusagen eigene Cache-Implementation             
            networkLastModifiedRawValue = self.__reply.rawHeader(bytearray('Last-Modified', "utf-8")).data().decode()
            networkLastModified = email.utils.parsedate_to_datetime(networkLastModifiedRawValue).timestamp()
            self.finished.emit(services, catalog_name, networkLastModified)

            return

        self.error_occurred.emit("Netzwerkfehler beim Laden der URL's", catalog_name)

class CatalogManager:
    overview = None
    catalogs = None
    catalog_path = f'{config.PLUGIN_DIR}/catalogs/'
    
    catalog_network_handler: NetworkHandler = None
    
    @classmethod
    def setup(cls, iface: QgisInterface) -> None:
        # ------- Network Handler für die einzelnen Kataloge erstellen -------------
        cls.catalog_network_handler = NetworkHandler(iface,  QgsNetworkAccessManager.instance())
        cls.catalog_network_handler.finished.connect(cls.add_catalog)
        cls.catalog_network_handler.error_occurred.connect(cls.handle_fetch_error)
        # ------- Network Handler für die Katalog Übersicht erstellen --------------
        overview_network_handler = NetworkHandler(iface, QgsNetworkAccessManager.instance())
        overview_network_handler.finished.connect(cls.set_overview)
        overview_network_handler.error_occurred.connect(cls.handle_fetch_error)
        overview_network_handler.fetch_catalog_overview()
    
    @classmethod
    def set_overview(cls, overview: dict, catalog_name: str, last_modified: float, fetch_catalogs: bool = True) -> None:
        cls.overview = overview
        file_name = 'katalog_overview'
        file_path = cls.catalog_path + file_name + '.json'
        
        localLastModified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0
        if localLastModified < last_modified:
            cls.write_json(overview, file_path)
        
        if fetch_catalogs:
            for catalog in overview:
                cls.catalog_network_handler.fetch_catalog(catalog["url"])
    
    @classmethod
    def add_catalog(cls, catalog: dict, catalog_name: str, last_modified: float) -> None:
        cls.catalogs = cls.catalogs or {}
        cls.catalogs[catalog_name] = catalog
        
        file_name = re.sub(r'\ ', '_', catalog_name.split(':')[0].lower())
        file_path = cls.catalog_path + file_name + '.json'
        
        localLastModified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0
        if localLastModified < last_modified:
            cls.write_json(catalog, file_path)

    @classmethod
    def handle_fetch_error(cls, error: str, catalog_name: str) -> None:
        is_overview_response = catalog_name == "overview"
        
        file_name = re.sub(r'\ ', '_', catalog_name.split(':')[0].lower()) if not is_overview_response else 'katalog_overview'
        file_path = cls.catalog_path + file_name + '.json'
        if not os.path.exists(file_path):
            error += ", Überprüfen Sie die Internetverbindung oder kontaktieren Sie den Autor"
            cls.catalog_network_handler.__iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, error)
            return

        services = cls.read_json(file_path)
        if not is_overview_response:
            services = list(services.items())
            cls.catalogs = cls.catalogs or {}
            cls.catalogs[catalog_name] = services
        else:
            cls.overview = services
        
        error += ", Verwendung der gecachten Daten"
        cls.catalog_network_handler.__iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, error)
    
    @classmethod
    def write_json(cls, data: str, file_path: str) -> None:
        mode = "w" if os.path.exists(file_path) else "x"
        
        with open(file_path, mode, encoding="utf-8", newline="\n") as file:
            file.write(data)

    @classmethod
    def read_json(cls, file_path: str) -> dict:
        services: dict | list = None
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read()
            services = json.loads(data)
        return services