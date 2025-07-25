import json, os, re, pathlib
from functools import partial
import email.utils
from typing import Optional, Union
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl, QObject, pyqtSignal
from qgis.core import QgsNetworkAccessManager, QgsSettings
from qgis._gui import QgisInterface
from . import config

class NetworkHandler(QObject):
    __manager: QgsNetworkAccessManager
    __reply: QNetworkReply
    _server: str = config.ServerHosts.get_servers()[0]
    
    done = False
    successful = False
    
    finished = pyqtSignal(str, str, float)
    error_occurred = pyqtSignal(str, str)
    
    def __init__(self, manager: QgsNetworkAccessManager) -> None:
        super().__init__()
        self.__manager = manager
        
    def __fetch_data(self, url: str = '') -> QNetworkReply:
        q_url = QUrl(url)
        request = QNetworkRequest(q_url)
        request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
        if self._server == config.ServerHosts.GITHUB:
            mediatype = "application/vnd.github.raw+json"
        else:
            mediatype = "application/json"
        request.setRawHeader(bytearray("Accept", "utf-8"), bytearray(mediatype, "utf-8"))
        return self.__manager.get(request)
  
    def fetch_catalog_overview(self) -> None:
        url = self._server.format(name=config.CATALOG_OVERVIEW)
        self.__reply = self.__fetch_data(url=url)
        self.__reply.finished.connect(partial(self.__handle_response, config.CATALOG_OVERVIEW, config.CATALOG_OVERVIEW_NAME, True))
  
    def fetch_catalog(self, catalog_name: str, catalog_title: str) -> None:
        if not catalog_name.endswith(".json"):
            catalog_name += ".json"
        url = self._server.format(name=catalog_name)
        self.__reply = self.__fetch_data(url=url)
        self.__reply.finished.connect(partial(self.__handle_response, catalog_name, catalog_title, False))
        
    def __handle_response(self, catalog_name: str, catalog_title: str, is_overview_response: bool):
        error = self.__reply.error()
        
        if error == 0:
            json_string = self.__reply.readAll().data().decode('utf-8')
            
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
            self.successful = True
            self.done = True
            self.finished.emit(json_string, catalog_title, networkLastModified)
            return
        
        server_list = config.ServerHosts.get_servers()
        curr_server_index = server_list.index(self._server)
        if curr_server_index == len(server_list) - 1:
            self.error_occurred.emit("Netzwerkfehler beim Laden der URL's", catalog_title)
            self.done = True
        else:
            self._server = server_list[curr_server_index + 1]
            if is_overview_response:
                self.fetch_catalog_overview()
            else:
                self.fetch_catalog(catalog_name, catalog_title)

class CatalogManager:
    overview = None
    catalogs = {}
    catalog_path = f'{config.PLUGIN_DIR}/catalogs/'
    
    catalog_network_handlers: dict[str, NetworkHandler] = {}
    
    _pending_callbacks: dict[str, callable] = {}
    
    @classmethod
    def setup(cls, iface: QgisInterface) -> None:
        cls.iface = iface
    
    @classmethod
    def add_network_handler(cls, catalog_title: str) -> NetworkHandler:
        if cls.catalog_network_handlers.get(catalog_title, None) is not None:
            handler = cls.catalog_network_handlers[catalog_title]
        else:
            handler = NetworkHandler(QgsNetworkAccessManager.instance())
            handler.finished.connect(cls.add_catalog)
            handler.error_occurred.connect(cls.handle_fetch_error)
            cls.catalog_network_handlers[catalog_title] = handler
        return handler
        
    @classmethod
    def clear_network_handlers(cls) -> None:
        if all(handler.done for handler in cls.catalog_network_handlers.values()):
            successful_count = sum(handler.successful for handler in cls.catalog_network_handlers.values())
            handler_count = len(cls.catalog_network_handlers)
            message = f"Es wurden {successful_count} von {handler_count} Kataloge neu geladen"
            
            if successful_count / handler_count >= 0.5:
                cls.iface.messageBar().pushSuccess(config.PLUGIN_NAME_AND_VERSION, message)
            else:
                cls.iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, message)
            
            cls.catalog_network_handlers.clear()
    
    @classmethod
    def set_overview(cls, overview: str, catalog_name: str, last_modified: float, fetch_catalogs: bool = True) -> None:
        cls.overview = json.loads(overview)
        file_name = 'katalog_overview'
        file_path = pathlib.Path(cls.catalog_path + file_name + '.json')
        
        localLastModified = os.path.getmtime(file_path) if file_path.exists() else 0.0
        if localLastModified < last_modified:
            cls.write_json(cls.overview, file_path)
        
        if fetch_catalogs:
            for catalog in cls.overview:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = cls.add_network_handler(catalog["titel"])
                handler.fetch_catalog(catalog["name"], catalog["titel"])
                
        if config.CATALOG_OVERVIEW_NAME in cls._pending_callbacks:
            for callback in cls._pending_callbacks[config.CATALOG_OVERVIEW_NAME]:
                callback()
            del cls._pending_callbacks[config.CATALOG_OVERVIEW_NAME]
    
    @classmethod
    def get_overview(cls, callback: Optional[callable] = None) -> None:
        # ------- Network Handler für die Katalog Übersicht erstellen --------------
        cls.overview_network_handler = NetworkHandler(QgsNetworkAccessManager.instance())
        cls.overview_network_handler.finished.connect(cls.set_overview)
        cls.overview_network_handler.error_occurred.connect(cls.handle_fetch_error)
        cls.overview_network_handler.fetch_catalog_overview()
        
        if callback:
            if config.CATALOG_OVERVIEW_NAME not in cls._pending_callbacks:
                cls._pending_callbacks[config.CATALOG_OVERVIEW_NAME] = []
            cls._pending_callbacks[config.CATALOG_OVERVIEW_NAME].append(callback)
    
    @classmethod
    def get_catalog(cls, catalog_title: str, catalog_name: Optional[str] = None, callback: Optional[callable] = None) -> Union[None, dict, list]:        
        if catalog_title == config.CATALOG_OVERVIEW_NAME:
            if cls.overview is not None:
                if callback:
                    callback(cls.overview)
                return cls.overview
        
        if catalog_title in cls.catalogs:
            if callback:
                callback(cls.catalogs[catalog_title])
            return cls.catalogs[catalog_title]
            
        if cls.overview_network_handler.done:
            cls.iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, "Katalog Übersicht ist nicht geladen, Bitte warten Sie oder kontaktieren Sie den Author")
        else:
            if callback:
                if catalog_title not in cls._pending_callbacks:
                    cls._pending_callbacks[catalog_title] = []
                cls._pending_callbacks[catalog_title].append(callback)
            
            if cls.overview is not None:
                catalog_info: dict[str, str] = list(filter(lambda x: x["titel"] == catalog_title, cls.overview))[0] # type: ignore
            else:
                if catalog_name is None:
                    raise ValueError("No catalog name provided")
                catalog_info: dict[str, str] = {
                    "titel": catalog_title,
                    "name": catalog_name
                }
            handler = cls.add_network_handler(catalog_info["titel"])
            if handler.done:
                handler.fetch_catalog(catalog_info["name"], catalog_info["titel"])
    
        return None
        
    @classmethod
    def add_catalog(cls, catalog: str, catalog_name: str, last_modified: float) -> None:
        catalog = json.loads(catalog)
        if type(catalog) == dict:
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
        is_overview_response = catalog_name == config.CATALOG_OVERVIEW_NAME
        
        file_name = re.sub(r'\ ', '_', catalog_name.split(':')[0].lower()) if not is_overview_response else 'katalog_overview'
        file_path = pathlib.Path(cls.catalog_path + file_name + '.json')
        if not file_path.exists():
            error += ", Überprüfen Sie die Internetverbindung oder kontaktieren Sie den Autor"
            cls.iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, error)
            
            # Notify callbacks with None result for the failed catalog
            if catalog_name in cls._pending_callbacks:
                for callback in cls._pending_callbacks[catalog_name]:
                    if is_overview_response:
                        callback()
                    else:
                        callback(None)
                del cls._pending_callbacks[catalog_name]
            return

        services = cls.read_json(file_path)
        if not is_overview_response and type(services) == dict:
            services = list(services.items())
            cls.catalogs = cls.catalogs
            cls.catalogs[catalog_name] = services
        else:
            cls.overview = services
            for catalog in cls.overview:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = cls.add_network_handler(catalog["titel"])
                handler.fetch_catalog(catalog["name"], catalog["titel"])
        
        error += ", Verwendung der gecachten Daten"
        cls.iface.messageBar().pushWarning(config.PLUGIN_NAME_AND_VERSION, error)
        
        if catalog_name in cls._pending_callbacks:
            for callback in cls._pending_callbacks[catalog_name]:
                if is_overview_response:
                    callback()
                else:
                    callback(services)
            del cls._pending_callbacks[catalog_name]
        
        cls.clear_network_handlers()
    
    @classmethod
    def write_json(cls, data: str, file_path: pathlib.Path) -> None:        
        file_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        mode = "w" if file_path.exists() else "x"
        
        with open(file_path, mode, encoding="utf-8", newline="\n") as file:
            data = json.dumps(data)
            file.write(data)

    @classmethod
    def read_json(cls, file_path: pathlib.Path) -> Union[dict, list]:
        if not file_path.exists():
            return {}
        
        services: Union[dict, list]
        with open(file_path, "r", encoding="utf-8") as file:
            services = json.load(file)
        return services