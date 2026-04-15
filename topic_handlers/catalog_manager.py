import json
import os
import re
import pathlib
from functools import partial
from typing import Optional, Union, Callable
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QUrl, QObject, QDateTime, pyqtSignal, QVersionNumber, QT_VERSION_STR
from qgis.core import QgsNetworkAccessManager, QgsSettings
from .. import config
from ..utils import custom_logger
from . import catalog_types

logger = custom_logger.get_logger(__file__)

if QVersionNumber(6) > QVersionNumber.fromString(QT_VERSION_STR)[0]:
    no_error = 0
    network_request_attributes = QNetworkRequest
    network_request_cache = QNetworkRequest
else:
    no_error = QNetworkReply.NetworkError.NoError
    network_request_attributes = QNetworkRequest.Attribute
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
        request.setAttribute(network_request_attributes.CacheLoadControlAttribute, network_request_cache.AlwaysNetwork)
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
        status_code: int = self._reply.attribute(network_request_attributes.HttpStatusCodeAttribute)
        
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
        
        # Differenzierte Fehlerbehandlung
        if not status_code: 
            logger.error(f"Kein Internet: {catalog_name} auf Server {self._server}")
        elif status_code == 404:
            logger.warning(f"404 Not Found: {catalog_name} auf Server {self._server}")
        elif status_code == 429:
            logger.warning(f"429 Rate Limit: Server {self._server}")
        elif status_code >= 500:
            logger.warning(f"Server-Fehler {status_code}: {catalog_name}")
        else:
            logger.warning(f"Unbekannter Statuscode: {status_code} für {catalog_name} auf {self._server}")

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
    overview: Optional[list[dict[str, str]]] = None
    catalogs: dict[str, catalog_types.Catalog] = {}
    catalog_path = f'{config.PLUGIN_DIR}/catalogs/'
    
    catalog_network_handlers: dict[str, NetworkHandler] = {}
    
    _pending_callbacks: dict[str, list[Callable]] = {}
    
    def __init__(self) -> None:
        self.overview: Optional[list[dict[str, str]]] = None
        self.catalogs: dict[str, catalog_types.Catalog] = {}
        self.catalog_network_handlers: dict[str, NetworkHandler] = {}
        self._pending_callbacks: dict[str, list[Callable]] = {}
    
    def add_network_handler(self, catalog_title: str) -> NetworkHandler:
        if self.catalog_network_handlers.get(catalog_title, None) is not None:
            handler = self.catalog_network_handlers[catalog_title]
        else:
            handler = NetworkHandler(QgsNetworkAccessManager.instance())
            handler.finished.connect(self.add_catalog)
            handler.error_occurred.connect(self.handle_fetch_error)
            self.catalog_network_handlers[catalog_title] = handler
        return handler
        
    def clear_network_handlers(self) -> None:
        if all(handler.done for handler in self.catalog_network_handlers.values()):
            successful_count = sum(handler.successful for handler in self.catalog_network_handlers.values())
            handler_count = len(self.catalog_network_handlers)
            message = f"Es wurden {successful_count} von {handler_count} Kataloge neu geladen"
            
            if handler_count > 0 and successful_count / handler_count >= 0.5:
                logger.success(message, extra={"show_banner": True})
            else:
                logger.warning(message, extra={"show_banner": True})
            
            self.catalog_network_handlers.clear()
    
    def set_overview(self, overview: str, catalog_name: str, last_modified: float, fetch_catalogs: bool = True) -> None:
        try:
            self.overview = json.loads(overview)
        except json.JSONDecodeError as e:
            logger.critical(f"Fehler beim Parsen der Katalogübersicht: {e}")
            logger.critical("Die Katalog-Übersicht enthält ungültiges JSON. Bitte prüfen Sie die Internetverbindung", extra={"show_banner": True})
            return
        
        if not self.overview:
            logger.critical(f"Katalogübersicht fehlerhaft, Bitte starten Sie QGIS neu oder kontaktieren Sie den Autor")
            return
        
        file_name = 'katalog_overview'
        file_path = pathlib.Path(self.catalog_path + file_name + '.json')
        
        localLastModified = os.path.getmtime(file_path) if file_path.exists() else 0.0
        if localLastModified < last_modified:
            self.write_json(self.overview, file_path)
        
        if fetch_catalogs:
            for catalog in self.overview:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = self.add_network_handler(catalog["titel"])
                handler.fetch_catalog(catalog["name"], catalog["titel"])
                
        if config.CATALOG_OVERVIEW_NAME in self._pending_callbacks:
            for callback in self._pending_callbacks[config.CATALOG_OVERVIEW_NAME]:
                callback()
            del self._pending_callbacks[config.CATALOG_OVERVIEW_NAME]
    
    def get_overview(self, callback: Optional[Callable] = None) -> None:
        # ------- Network Handler für die Katalog Übersicht erstellen --------------
        self.overview_network_handler = NetworkHandler(QgsNetworkAccessManager.instance())
        self.overview_network_handler.finished.connect(self.set_overview)
        self.overview_network_handler.error_occurred.connect(self.handle_fetch_error)
        self.overview_network_handler.fetch_catalog_overview()
        
        if callback:
            if config.CATALOG_OVERVIEW_NAME not in self._pending_callbacks:
                self._pending_callbacks[config.CATALOG_OVERVIEW_NAME] = []
            self._pending_callbacks[config.CATALOG_OVERVIEW_NAME].append(callback)
    
    def get_catalog(self, catalog_title: str, catalog_name: Optional[str] = None, callback: Optional[Callable] = None) -> Union[None, catalog_types.Catalog, list]:        
        if catalog_title == config.CATALOG_OVERVIEW_NAME:
            if self.overview is not None:
                if callback:
                    callback(self.overview)
                return self.overview
        
        if catalog_title in self.catalogs:
            if callback:
                callback(self.catalogs[catalog_title])
            return self.catalogs[catalog_title]
            
        if self.overview_network_handler.done:
            logger.warning("Katalog Übersicht ist nicht geladen, Bitte warten Sie oder kontaktieren Sie den Author")
        else:
            if callback:
                if catalog_title not in self._pending_callbacks:
                    self._pending_callbacks[catalog_title] = []
                self._pending_callbacks[catalog_title].append(callback)
            
            if self.overview is not None:
                matching_catalogs = [x for x in self.overview if x.get("titel") == catalog_title]
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
            handler = self.add_network_handler(catalog_info["titel"])
            if handler.done:
                handler.fetch_catalog(catalog_info["name"], catalog_info["titel"])
    
        return None
    
    def get_current_catalog(self, callback: Optional[Callable] = None) -> Union[None, catalog_types.Catalog, list]:
        qgs_settings = QgsSettings()
        current_catalog = qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is None or "name" not in current_catalog:
            return None
        
        return self.get_catalog(current_catalog["titel"], current_catalog["name"], callback)
    
    def add_catalog(self, raw_catalog: str, catalog_name: str, last_modified: float) -> None:
        try:
            parsed_catalog = json.loads(raw_catalog)
        except json.JSONDecodeError as e:
            logger.critical(f"Fehler beim Parsen des Katalogs '{catalog_name}': {e}")
            logger.critical(f"Der Katalog '{catalog_name}' enthält ungültiges JSON. Bitte prüfen Sie die Internetverbindung", extra={"show_banner": True})
            return
        
        if isinstance(parsed_catalog, dict):
            catalog = catalog_types.Catalog.from_dict(parsed_catalog)
            catalog.build_index()
            self.catalogs[catalog_name] = catalog
        
        file_name = re.sub(r'\ ', '_', catalog_name.split(':')[0].lower())
        file_path = pathlib.Path(self.catalog_path + file_name + '.json')
        
        localLastModified = os.path.getmtime(file_path) if file_path.exists() else 0.0
        if localLastModified < last_modified:
            self.write_json(parsed_catalog, file_path)
        
        if catalog_name in self._pending_callbacks:
            for callback in self._pending_callbacks[catalog_name]:
                callback(self.catalogs[catalog_name])
            del self._pending_callbacks[catalog_name]
        
        self.clear_network_handlers()

    def handle_fetch_error(self, error: str, catalog_name: str) -> None:
        is_overview_response = catalog_name == config.CATALOG_OVERVIEW_NAME
        
        file_name = re.sub(r'\ ', '_', catalog_name.split(':')[0].lower()) if not is_overview_response else 'katalog_overview'
        file_path = pathlib.Path(self.catalog_path + file_name + '.json')
        if not file_path.exists():
            error += ", Überprüfen Sie die Internetverbindung oder kontaktieren Sie den Autor"
            logger.warning(error, extra={"show_banner": True})
            
            # Notify callbacks with None result for the failed catalog
            if catalog_name in self._pending_callbacks:
                for callback in self._pending_callbacks[catalog_name]:
                    if is_overview_response:
                        callback()
                    else:
                        callback(None)
                del self._pending_callbacks[catalog_name]
            return

        parsed_services = self.read_json(file_path)
        if not is_overview_response and isinstance(parsed_services, dict):
            catalog = catalog_types.Catalog.from_dict(parsed_services)
            catalog.build_index()
            self.catalogs[catalog_name] = catalog
        else:
            if not isinstance(parsed_services, list):
                error += "Katalogübersicht nicht korrekt geparst"
                logger.warning(error, extra={"show_banner": True})
                return
            
            self.overview = parsed_services
            for catalog in self.overview:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = self.add_network_handler(catalog["titel"])
                handler.fetch_catalog(catalog["name"], catalog["titel"])
        
        error += ", Verwendung der gecachten Daten"
        logger.warning(error, extra={"show_banner": True})
        
        if catalog_name in self._pending_callbacks:
            for callback in self._pending_callbacks[catalog_name]:
                if is_overview_response:
                    callback()
                else:
                    callback(self.catalogs.get(catalog_name, None))
            del self._pending_callbacks[catalog_name]
        
        self.clear_network_handlers()

    def write_json(self, data: Union[dict, list, str], file_path: pathlib.Path) -> None:
        file_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        
        try:
            with open(file_path, "w", encoding="utf-8", newline="\n") as file:
                json.dump(data, file, indent=2)
        except OSError as e:
            logger.critical(f"Fehler beim Schreiben der Datei {file_path}: {e}")
        except TypeError as e:
            logger.critical(f"Nicht-serialisierbares Objekt für {file_path}: {e}")

    def read_json(self, file_path: pathlib.Path) -> Union[dict, list]:
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                services = json.load(file)
            return services
        except json.JSONDecodeError as e:
            logger.critical(f"Ungültiges JSON in Datei {file_path}: {e}")
            return {}
        except OSError as e:
            logger.critical(f"Fehler beim Lesen der Datei {file_path}: {e}")
            return {}

singleton = CatalogManager()