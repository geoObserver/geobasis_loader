import json, os, re, pathlib
from functools import partial
from typing import Optional, Union, Callable
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QUrl, QObject, QDateTime, pyqtSignal, QVersionNumber, QT_VERSION_STR
from qgis.core import QgsNetworkAccessManager, QgsSettings
from qgis.gui import QgisInterface
from . import config
from . import custom_logger
from .topic_search import SearchFilter

logger = custom_logger.get_logger(__file__)

if QVersionNumber(6) > QVersionNumber.fromString(QT_VERSION_STR)[0]:
    no_error = 0
    netowrk_request_attributes = QNetworkRequest
    network_request_cache = QNetworkRequest
else:
    no_error = QNetworkReply.NetworkError.NoError
    netowrk_request_attributes = QNetworkRequest.Attribute
    network_request_cache = QNetworkRequest.CacheLoadControl


class NetworkHandler(QObject):
    _manager: QgsNetworkAccessManager
    _reply: QNetworkReply
    
    finished = pyqtSignal(str, str, float)
    error_occurred = pyqtSignal(str, str)
    
    def __init__(self, manager: Union[QgsNetworkAccessManager, None]) -> None:
        super().__init__()
        if not manager:
            logger.critical(f"Netzwerkanfrage hat keinen Netzwerkmanager, Bitte starten Sie QGIS neu oder kontaktieren Sie den Autor")
            raise ValueError("No QgsNetworkAccessManager recieved")
        
        self._manager = manager
        self._server_list = config.ServerHosts.get_enabled_servers()
        self._server = self._server_list[0]
        self.done = False
        self.successful = False
        
    def _fetch_data(self, url: str = '') -> Optional[QNetworkReply]:
        q_url = QUrl(url)
        request = QNetworkRequest(q_url)
        request.setAttribute(netowrk_request_attributes.CacheLoadControlAttribute, network_request_cache.AlwaysNetwork)
        request.setTransferTimeout(config.REQUEST_TIMEOUT_MS)
        # if self._server == config.ServerHosts.GITHUB:
        #     mediatype = "application/vnd.github.raw+json"
        # else:
        #     mediatype = "application/json"
        request.setRawHeader(
            bytearray("Accept", "utf-8"),  
            bytearray("gzip, deflate", "utf-8")
        )
        return self._manager.get(request)
  
    def fetch_catalog_overview(self) -> None:
        url = self._server.format(name=config.CATALOG_OVERVIEW)
        reply = self._fetch_data(url=url)
        if not reply:
            logger.critical("Die Netzwerkantwort für die Katalogübersicht konnte nicht erstellt werden")
            return
        
        self._reply = reply
        self._reply.finished.connect(partial(self._handle_response, config.CATALOG_OVERVIEW, config.CATALOG_OVERVIEW_NAME, True))
  
    def fetch_catalog(self, catalog_name: str, catalog_title: str) -> None:
        if not catalog_name.endswith(".json"):
            catalog_name += ".json"
        url = self._server.format(name=catalog_name)
        reply = self._fetch_data(url=url)
        if not reply:
            logger.critical(f"Die Netzwerkantwort für den Katalog '{catalog_name}' konnte nicht erstellt werden")
            return
        
        self._reply = reply
        self._reply.finished.connect(partial(self._handle_response, catalog_name, catalog_title, False))
        
    def _handle_response(self, catalog_name: str, catalog_title: str, is_overview_response: bool):
        error = self._reply.error()
        status_code: int = self._reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        
        if error == no_error and status_code == 200:
            json_string = self._reply.readAll().data().decode('utf-8')
     
            # Holt sich die Timestamps der letzten Modifikationen der lokalen JSON-Datei und der JSON-Datei aus dem Internet
            # (Über-)Schreibt dann die loakle JSON-Datei, wenn die Datei im Internet neuer ist
            # Sozusagen eigene Cache-Implementation
            network_last_modified_raw_value: QDateTime = self._reply.header(QNetworkRequest.KnownHeaders.LastModifiedHeader)
            if network_last_modified_raw_value.isValid():
                network_last_modified = network_last_modified_raw_value.toMSecsSinceEpoch() / 1000      # ??????????
            else:
                network_last_modified = 0.0
            self.successful = True
            self.done = True
            self.finished.emit(json_string, catalog_title, network_last_modified)
            
            total_server_list = config.ServerHosts.get_all_servers()
            index = total_server_list.index(self._server)
            logger.info(f"Katalog '{catalog_name}' erfolgreich von Server {index + 1} geladen")
            return
        
        # TODO: LOGGING
        # Different code per status code
        
        curr_server_index = self._server_list.index(self._server)
        if curr_server_index == len(self._server_list) - 1:
            self.error_occurred.emit("Netzwerkfehler beim Laden der URL's", catalog_title)
            self.done = True
            logger.warning(f"Katalog '{catalog_name}' konnte nicht von einem Server geladen werden")
        else:
            self._server = self._server_list[curr_server_index + 1]
            if is_overview_response:
                self.fetch_catalog_overview()
            else:
                self.fetch_catalog(catalog_name, catalog_title)


class CatalogManager:
    overview = None
    catalogs = {}
    catalog_path = f'{config.PLUGIN_DIR}/catalogs/'
    
    catalog_network_handlers: dict[str, NetworkHandler] = {}
    
    _pending_callbacks: dict[str, list[Callable]] = {}
    
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
            
            if handler_count > 0 and successful_count / handler_count >= 0.5:
                logger.success(message, extra={"show_banner": True})
            else:
                logger.warning(message, extra={"show_banner": True})
            
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
    def get_overview(cls, callback: Optional[Callable] = None) -> None:
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
    def get_catalog(cls, catalog_title: str, catalog_name: Optional[str] = None, callback: Optional[Callable] = None) -> Union[None, dict, list]:        
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
            logger.warning("Katalog Übersicht ist nicht geladen, Bitte warten Sie oder kontaktieren Sie den Author")
        else:
            if callback:
                if catalog_title not in cls._pending_callbacks:
                    cls._pending_callbacks[catalog_title] = []
                cls._pending_callbacks[catalog_title].append(callback)
            
            if cls.overview is not None:
                matching_catalogs = [x for x in cls.overview if x.get("titel") == catalog_title]
                if not matching_catalogs:
                    logger.error(f"Kein Katalog mit dem Namen {catalog_title} gefunden, Starten Sie QGIS neu oder kontaktieren Sie den Autor")
                    if callback:
                        callback(None)
                    return None
                
                catalog_info: dict[str, str] = matching_catalogs[0]
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
    def get_current_catalog(cls, callback: Optional[Callable] = None) -> Union[None, dict, list]:
        qgs_settings = QgsSettings()
        current_catalog = qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is None or "name" not in current_catalog:
            return None
        
        return cls.get_catalog(current_catalog["titel"], current_catalog["name"], callback)
        
    @classmethod
    def add_catalog(cls, raw_catalog: str, catalog_name: str, last_modified: float) -> None:
        catalog = json.loads(raw_catalog)
        if isinstance(catalog, dict):
            catalog = cls.set_internal_properties(catalog)
            cls.catalogs[catalog_name] = list(catalog.items())
            SearchFilter.build_search_index(cls.catalogs)
        
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
            logger.warning(error, extra={"show_banner": True})
            
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
        if not is_overview_response and isinstance(services, dict):
            catalog = cls.set_internal_properties(services)
            services = list(services.items())
            cls.catalogs[catalog_name] = services
            SearchFilter.build_search_index(cls.catalogs)
        else:
            cls.overview = services
            for catalog in cls.overview:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = cls.add_network_handler(catalog["titel"])
                handler.fetch_catalog(catalog["name"], catalog["titel"])
        
        error += ", Verwendung der gecachten Daten"
        logger.warning(error, extra={"show_banner": True})
        
        if catalog_name in cls._pending_callbacks:
            for callback in cls._pending_callbacks[catalog_name]:
                if is_overview_response:
                    callback()
                else:
                    callback(services)
            del cls._pending_callbacks[catalog_name]
        
        cls.clear_network_handlers()
    
    @classmethod
    def set_internal_properties(cls, catalog: dict) -> dict:
        def _apply_path_flag(data: dict, path_prefix: str = ""):
            for key, value in data.items():
                path = f"{path_prefix}/{key}" if path_prefix else key
                
                if isinstance(value, dict):
                    if key != "themen" and key != "layers":
                        data[key][config.InternalProperties.PATH] = path
                    _apply_path_flag(value, path)
        
        _apply_path_flag(catalog)
        
        return catalog

    @classmethod
    def write_json(cls, data: Union[dict, str], file_path: pathlib.Path) -> None:
        # Permissions to high (maybe 755) -> 777 used due to access problems on MacOs (I think, already some time ago), tried a few combinations
        file_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, indent=2)

    @classmethod
    def read_json(cls, file_path: pathlib.Path) -> Union[dict, list]:
        if not file_path.exists():
            return {}
        
        services: Union[dict, list]
        with open(file_path, "r", encoding="utf-8") as file:
            services = json.load(file)
        return services