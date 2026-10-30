import json
import pathlib
import os
from datetime import datetime, timezone
from typing import Any, Iterable, Optional, Union
from functools import singledispatchmethod
from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.core import QgsNetworkAccessManager
from .models import CatalogIndex, Catalog, load_catalog, load_catalog_index
from ...core.data_infrastructure.network_handlers import NetworkHandler
from ...core.data_infrastructure import file_handlers
from .models import DataSource, ServerDataSource, LocalDataSource
from .catalog_exceptions import NetworkHandlerAlreadyExistsError
from ...core.utils import custom_logger
from ...core.utils import signal_utils

logger = custom_logger.get_logger(__name__)

class CatalogDataFetcher(QObject):
    catalog_index_fetched = pyqtSignal(CatalogIndex)
    catalog_fetched = pyqtSignal(Catalog)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.network_handlers: dict[str, NetworkHandler] = {}
        self.last_data_sources: list[DataSource] = []
        self.data_sources: dict[str, DataSource] = {}
    
    def dispose(self) -> None:
        self.clear_network_handlers(force=True)
        self.data_sources.clear()
        signal_utils.disconnect_all_signals(self)
    
    def _add_network_handler(self, title: str, urls: list[str], data_source: ServerDataSource, group: str = "") -> NetworkHandler:
        full_title = NetworkHandler.get_full_title(title, group)
        if full_title in self.network_handlers:
            raise NetworkHandlerAlreadyExistsError(title)
        
        manager = QgsNetworkAccessManager.instance()
        if manager is None:
            raise RuntimeError("QgsNetworkAccessManager instance is not available.")
        
        handler = NetworkHandler(title, urls, manager, parent=self, group=group)      
        handler.error_occurred.connect(self._handle_fetch_error)
        self.network_handlers[handler.full_title] = handler
        self.data_sources[handler.full_title] = data_source
        return handler
    
    def clear_network_handlers(self, force: bool = False) -> None:
        handlers = list(self.network_handlers.values())
        all_done = all(handler.done for handler in handlers)
        
        if all_done and len(handlers) > 0:
            non_index_handlers = [handler for handler in handlers if handler.title != "Index"]
            handler_count = len(non_index_handlers)
            successful_count = sum(handler.successful for handler in non_index_handlers)
            message = f"Es wurden {successful_count} von {handler_count} Kataloge neu geladen"
            
            if handler_count > 0 and successful_count / handler_count >= 0.5:
                logger.success(message, extra={"show_banner": True})
            else:
                logger.warning(message, extra={"show_banner": True})
        
        if not force and not all_done:
            return

        for handler in handlers:
            handler.abort()
            if handler.full_title in self.data_sources:
                del self.data_sources[handler.full_title]
        
        self.network_handlers.clear()
    
    def _parse_data(self, content: str, full_title: str) -> tuple[dict, Union[CatalogIndex, Catalog, None]]:
        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.critical(f"Fehler beim Parsen der Daten: {type(e).__name__}, {e}")
            logger.critical(f"'{full_title}' enthält ungültiges JSON. Bitte prüfen Sie die Internetverbindung oder den Pfad.", extra={"show_banner": True})
            return {}, None
        
        try:
            if "catalogs" in parsed_data:
                return parsed_data, load_catalog_index(parsed_data)
            else:
                return parsed_data, load_catalog(parsed_data)
        except Exception as e:
            logger.critical(f"Fehler beim Laden der Daten: {type(e).__name__}, {e}")
            logger.critical(f"'{full_title}' ist fehlerhaft. Kontaktieren Sie den Autor.", extra={"show_banner": True})
            return {}, None
    
    def _cache_data(self, data: dict, file_name: str, full_title: str, modified: datetime) -> None:
        data_source = self.data_sources[full_title]
        if isinstance(data_source, ServerDataSource) and data_source.cache_path:
            file_path = data_source.cache_path / f"{file_name}"
            self._write_cache_if_stale(data, file_path, modified)
    
    def fetch_data(self, data_sources: Optional[Iterable[DataSource]]) -> None:
        if not data_sources:
            data_sources = self.last_data_sources
            logger.info("Verwende zum Laden die zuletzt verwendeten Datenquellen.")
        if not data_sources:
            logger.warning("Keine Datenquellen zum Abrufen von Katalogdaten angegeben.")
            return
        
        self.last_data_sources = list(data_sources)
        for data_source in data_sources:
            self.fetch_catalog_data(data_source)
    
    @singledispatchmethod
    def fetch_catalog_data(self, data_source) -> Optional[CatalogIndex]:
        raise NotImplementedError(f"Can't fetch catalog data for data source type {type(data_source)}.")
    
    @fetch_catalog_data.register
    def _(self, data_source: ServerDataSource) -> None:
        urls = data_source.get_enabled_urls()
        if not urls:
            logger.warning(f"Keine aktivierten URLs für Datenquelle '{data_source.name}' gefunden. Überspringe Katalogabfrage.")
            return
        
        urls = [url.format(name=data_source.index_name) for url in urls]
        try:
            handler = self._add_network_handler("Index", urls, data_source, group=data_source.name)
        except NetworkHandlerAlreadyExistsError:
            title = NetworkHandler.get_full_title("Index", data_source.name)
            logger.warning(f"Netzwerk-Handler für '{title}' existiert bereits. Überspringe Katalogabfrage.")
            return
        
        handler.finished.connect(self._parse_catalog_index)
        handler.start()
        
    @fetch_catalog_data.register
    def _(self, data_source: LocalDataSource) -> Optional[CatalogIndex]:
        file_path = data_source.base_path / data_source.index_name
        if not file_path.exists():
            logger.warning(f"Lokaler Katalogindex '{file_path}' existiert nicht. Überspringe Katalogabfrage.")
            return None
        
        self.data_sources[str(file_path)] = data_source
        try:
            contents = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.critical(f"Fehler beim Lesen der Datei '{file_path}': {type(e).__name__}, {e}")
            return None
        
        self._parse_catalog_index(contents, str(file_path))
    
    def _parse_catalog_index(self, content: str, full_title: str) -> None:
        parsed_index, catalog_index = self._parse_data(content, full_title)
        if not isinstance(catalog_index, CatalogIndex):
            return
        
        data_source = self.data_sources.get(full_title)
        if isinstance(data_source, ServerDataSource):
            self._cache_data(parsed_index, data_source.index_name, full_title, catalog_index.modified)
        else:
            name = data_source.index_name if data_source else "Unbekannt"
            logger.success(f"Lokaler Katalogindex '{name}' erfolgreich geladen.")
            if full_title in self.data_sources:
                del self.data_sources[full_title]
        self.catalog_index_fetched.emit(catalog_index)
        file_names = [catalog.file for catalog in catalog_index]
        self.fetch_catalogs(data_source, file_names)
        
    @singledispatchmethod
    def fetch_catalogs(self, data_source, file_names) -> None:
        raise NotImplementedError(f"Can't fetch catalogs for data source type {type(data_source)}.")
    
    @fetch_catalogs.register
    def _(self, data_source: ServerDataSource, file_names: list[str]) -> None:
        for file_name in file_names:
            urls = data_source.get_enabled_urls()
            if not urls:
                logger.warning(f"Keine aktivierten URLs für Datenquelle '{data_source.name}' gefunden. Überspringe Katalogabfrage.")
                continue
            
            urls = [url.format(name=file_name) for url in urls]
            try:
                handler = self._add_network_handler(file_name, urls, data_source, group=data_source.name)
            except NetworkHandlerAlreadyExistsError:
                title = NetworkHandler.get_full_title(file_name, data_source.name)
                logger.warning(f"Netzwerk-Handler für '{title}' existiert bereits. Überspringe Katalogabfrage.")
                continue
            
            handler.finished.connect(self._parse_catalog)
            handler.start()
    
    @fetch_catalogs.register
    def _(self, data_source: LocalDataSource, file_names: list[str]) -> None:
        for file_name in file_names:
            file_path = data_source.base_path / file_name
            if not file_path.exists():
                logger.warning(f"Lokaler Katalog '{file_path}' in '{data_source.base_path / data_source.index_name}' existiert nicht. Überspringe Katalogabfrage.")
                continue
            
            self.data_sources[str(file_path)] = data_source
            try:
                contents = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.critical(f"Fehler beim Lesen der Datei '{file_path}': {type(e).__name__}, {e}")
                continue
            
            self._parse_catalog(contents, str(file_path))
    
    def _parse_catalog(self, content: str, full_title: str) -> None:
        parsed_catalog, catalog = self._parse_data(content, full_title)
        if not isinstance(catalog, Catalog):
            return
        
        network_handler = self.network_handlers.get(full_title)
        if network_handler is not None:          # Title should be file name
            self._cache_data(parsed_catalog, network_handler.title, full_title, catalog.modified)
        else:
            logger.success(f"Lokaler Katalog '{full_title}' erfolgreich geladen.")
            if full_title in self.data_sources:
                del self.data_sources[full_title]
        self.catalog_fetched.emit(catalog)
        self.clear_network_handlers()
    
    def _handle_fetch_error(self, error_message: str, full_title: str) -> None:
        network_handler = self.network_handlers.get(full_title)
        data_source = self.data_sources.get(full_title)
        error = f"Fehler beim Abrufen der Daten für '{full_title}': {error_message}\n"
        if data_source is None or network_handler is None or not isinstance(data_source, ServerDataSource):
            logger.critical(error, extra={"show_banner": True})
            return
        
        backup_data_source = data_source.convert_to_local()        
        if network_handler.title == "Index":
            backup_file_path = backup_data_source.base_path / backup_data_source.index_name if backup_data_source else None
        else:
            backup_file_path = backup_data_source.base_path / network_handler.title if backup_data_source else None
            
        if not backup_file_path or not backup_data_source or not backup_file_path.exists():
            error += f"Kein Backup verfügbar"
            error += f" unter '{backup_file_path}'." if backup_file_path else "."
            error += " Laden abgebrochen."
            logger.critical(error, extra={"show_banner": True})
            self.clear_network_handlers()
            return

        error += f"Verwende Backup unter '{backup_file_path}'."
        logger.warning(error, extra={"show_banner": True})
        # TODO: If Index is not fetched it converts to a local source meaning all subsequent catalogs will be fetched from local source.
        if network_handler.title == "Index":
            self.fetch_catalog_data(backup_data_source)
        else:
            self.fetch_catalogs(backup_data_source, [network_handler.title])
        
        self.clear_network_handlers()
    
    def _write_cache_if_stale(self, data: dict, file_path: pathlib.Path, last_modified: datetime) -> None:
        try:
            # FIXME: Timezone
            local_last_modified = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)
        except OSError:
            local_last_modified = None          # fehlt oder unlesbar -> unbekannt

        if local_last_modified is None:         # kein Cache -> immer schreiben
            self.write_json(data, file_path)
        elif local_last_modified < last_modified:
            self.write_json(data, file_path)

    def write_json(self, data: dict, file_path: pathlib.Path) -> None:
        try:
            file_handlers.write_json(data, file_path)
        except Exception as e:
            logger.critical(f"Fehler beim Schreiben der JSON-Datei {file_path}: {type(e).__name__}, {e}")

    def read_json(self, file_path: pathlib.Path) -> dict[str, Any]:
        try:
            return file_handlers.read_json(file_path)
        except Exception as e:
            logger.critical(f"Fehler beim Lesen der JSON-Datei {file_path}: {type(e).__name__}, {e}")
            return {}