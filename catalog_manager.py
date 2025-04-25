import json, os, re, pathlib
from functools import partial
import email.utils
from typing import Optional
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QObject, pyqtSignal
from qgis.core import QgsNetworkAccessManager, QgsSettings
from qgis._gui import QgisInterface
from . import config

class NetworkHandler(QObject):
    __manager: QgsNetworkAccessManager = None
    __reply: QNetworkReply = None
    
    done = False
    
    finished = pyqtSignal(str, str, float)
    error_occurred = pyqtSignal(str, str)
    
    def __init__(self, manager: QgsNetworkAccessManager) -> None:
        super().__init__()
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
     
            # Holt sich die Timestamps der letzten Modifikationen der lokalen JSON-Datei und der JSON-Datei aus dem Internet
            # (Über-)Schreibt dann die loakle JSON-Datei, wenn die Datei im Internet neuer ist
            # Sozusagen eigene Cache-Implementation             
            networkLastModifiedRawValue = self.__reply.rawHeader(bytearray('Last-Modified', "utf-8")).data().decode()
            networkLastModified = email.utils.parsedate_to_datetime(networkLastModifiedRawValue).timestamp()
            self.finished.emit(json_string, catalog_name, networkLastModified)

        else:
            self.error_occurred.emit("Netzwerkfehler beim Laden der URL's", catalog_name)
        self.done = True

class CatalogManager:
    overview = None
    catalogs = {}
    catalog_path = f'{config.PLUGIN_DIR}/catalogs/'
    
    catalog_network_handlers: list[NetworkHandler] = []
    
    _pending_callbacks: dict[str, callable] = {}
    
    @classmethod
    def setup(cls, iface: QgisInterface) -> None:
        cls.iface = iface
        # ------- Network Handler für die Katalog Übersicht erstellen --------------
        cls.overview_network_handler = NetworkHandler(QgsNetworkAccessManager.instance())
        cls.overview_network_handler.finished.connect(cls.set_overview)
        cls.overview_network_handler.error_occurred.connect(cls.handle_fetch_error)
        cls.overview_network_handler.fetch_catalog_overview()
    
    @classmethod
    def add_network_handler(cls) -> NetworkHandler:
        handler = NetworkHandler(QgsNetworkAccessManager.instance())
        handler.finished.connect(cls.add_catalog)
        handler.error_occurred.connect(cls.handle_fetch_error)
        cls.catalog_network_handlers.append(handler)
        return handler
        
    @classmethod
    def clear_network_handlers(cls) -> None:
        if all(handler.done for handler in cls.catalog_network_handlers):
            cls.catalog_network_handlers.clear()
    
    @classmethod
    def set_overview(cls, overview: str, catalog_name: str, last_modified: float, fetch_catalogs: bool = True) -> None:
        cls.overview = json.loads(overview)
        file_name = 'katalog_overview'
        file_path = pathlib.Path(cls.catalog_path + file_name + '.json')
        
        localLastModified = os.path.getmtime(file_path) if file_path.exists() else 0.0
        if localLastModified < last_modified:
            cls.write_json(overview, file_path)
        
        if fetch_catalogs:
            for catalog in cls.overview:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = cls.add_network_handler()
                handler.fetch_catalog(catalog["url"], catalog["titel"])
    
    @classmethod
    def get_catalog(cls, catalog_name: str, callback: callable = None) -> Optional[dict]:
        if catalog_name == "overview":
            if callback and cls.overview is not None:
                callback(cls.overview)
        
        if catalog_name in cls.catalogs :
            if callback:
                callback(cls.catalogs[catalog_name])
            else:
                return cls.catalogs[catalog_name]
        
        if cls.overview is None:
            cls.iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, "Katalog Übersicht ist nicht geladen, Bitte warten Sie oder kontaktieren Sie den Author")
            return None

        if callback:
            if catalog_name not in cls._pending_callbacks:
                cls._pending_callbacks[catalog_name] = []
            cls._pending_callbacks[catalog_name].append(callback)
    
        handler = cls.add_network_handler()
        catalog_info = list(filter(lambda x: x["titel"] == catalog_name, cls.overview))[0]
        handler.fetch_catalog(catalog_info["url"], catalog_info["titel"])
        
        return None
        
    @classmethod
    def add_catalog(cls, catalog: str, catalog_name: str, last_modified: float) -> None:
        catalog = json.loads(catalog)
        cls.catalogs = cls.catalogs
        cls.catalogs[catalog_name] = list(catalog.items())
        
        file_name = re.sub(r'\ ', '_', catalog_name.split(':')[0].lower())
        file_path = pathlib.Path(cls.catalog_path + file_name + '.json')
        
        localLastModified = os.path.getmtime(file_path) if file_path.exists() else 0.0
        if localLastModified < last_modified:
            cls.write_json(catalog, file_path)
        
        if catalog_name in cls._pending_callbacks:
            for callback in cls._pending_callbacks[catalog_name]:
                callback(cls.catalogs[catalog_name])
            del cls._pending_callbacks[catalog_name]
        
        cls.clear_network_handlers()

    @classmethod
    def handle_fetch_error(cls, error: str, catalog_name: str) -> None:
        is_overview_response = catalog_name == "overview"
        
        file_name = re.sub(r'\ ', '_', catalog_name.split(':')[0].lower()) if not is_overview_response else 'katalog_overview'
        file_path = pathlib.Path(cls.catalog_path + file_name + '.json')
        if not file_path.exists():
            error += ", Überprüfen Sie die Internetverbindung oder kontaktieren Sie den Autor"
            cls.iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, error)
            
            # Notify callbacks with None result for the failed catalog
            if not is_overview_response and catalog_name in cls._pending_callbacks:
                for callback in cls._pending_callbacks[catalog_name]:
                    callback(None)
                del cls._pending_callbacks[catalog_name]
            return

        services = cls.read_json(file_path)
        if not is_overview_response:
            services = list(services.items())
            cls.catalogs = cls.catalogs
            cls.catalogs[catalog_name] = services
        else:
            cls.overview = services
            for catalog in services:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = cls.add_network_handler()
                handler.fetch_catalog(catalog["url"], catalog["titel"])
        
        error += ", Verwendung der gecachten Daten"
        cls.iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, error)
        
        if catalog_name in cls._pending_callbacks:
            for callback in cls._pending_callbacks[catalog_name]:
                callback(services)
            del cls._pending_callbacks[catalog_name]
        
        cls.clear_network_handlers()
    
    @classmethod
    def write_json(cls, data: str, file_path: pathlib.Path) -> None:        
        file_path.parent.mkdir(mode=0o660,parents=True, exist_ok=True)
        mode = "w" if os.path.exists(file_path) else "x"
        
        with open(file_path, mode, encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(data))

    @classmethod
    def read_json(cls, file_path: pathlib.Path) -> dict:
        services: dict | list = None
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read()
            services = json.loads(data)
        return services