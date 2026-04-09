"""Async catalog fetching and caching for the GeoBasis Loader plugin.

Provides ``NetworkHandler`` for non-blocking HTTP requests with server
fallback and ``CatalogManager`` as a singleton-style registry that
stores, caches and enriches catalog data.
"""

from __future__ import annotations
import json
import os
import re
import pathlib
import email.utils
from functools import partial
from typing import Callable
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QUrl, QObject, pyqtSignal
from qgis.core import QgsNetworkAccessManager, QgsSettings, QgsMessageLog, Qgis
from qgis.gui import QgisInterface
from . import config


class NetworkHandler(QObject):
    """Performs async HTTP fetches for catalog JSON files.

    Tries each enabled server in order and falls back to the next one on
    failure. Emits ``finished`` on success or ``error_occurred`` when all
    servers have been exhausted.
    """

    __manager: QgsNetworkAccessManager
    __reply: QNetworkReply

    done = False
    successful = False

    finished = pyqtSignal(str, str, float)
    error_occurred = pyqtSignal(str, str)

    def __init__(self, manager: QgsNetworkAccessManager | None) -> None:
        """Initialize the handler with a QGIS network access manager.

        Args:
            manager: The shared ``QgsNetworkAccessManager`` instance.
                If ``None``, the handler is left in an inert state.
        """
        super().__init__()
        if not manager:
            return

        self.__manager = manager
        self._server_list = config.ServerHosts.get_enabled_servers()
        self._server = self._server_list[0]

    def __fetch_data(self, url: str = '') -> QNetworkReply:
        q_url = QUrl(url)
        request = QNetworkRequest(q_url)
        request.setAttribute(
            QNetworkRequest.Attribute.CacheLoadControlAttribute,
            QNetworkRequest.CacheLoadControl.AlwaysNetwork,
        )
        if self._server == config.ServerHosts.GITHUB:
            mediatype = "application/vnd.github.raw+json"
        else:
            mediatype = "application/json"
        request.setRawHeader(bytearray("Accept", "utf-8"), bytearray(mediatype, "utf-8"))
        return self.__manager.get(request)

    def fetch_catalog_overview(self) -> None:
        """Fetch the catalog overview file from the current server."""
        url = self._server.format(name=config.CATALOG_OVERVIEW)
        self.__reply = self.__fetch_data(url=url)
        self.__reply.finished.connect(
            partial(self.__handle_response,
                    config.CATALOG_OVERVIEW,
                    config.CATALOG_OVERVIEW_NAME, True),
        )

    def fetch_catalog(self, catalog_name: str, catalog_title: str) -> None:
        """Fetch a single regional catalog by name.

        Args:
            catalog_name: File name of the catalog (with or without ``.json``).
            catalog_title: Human-readable title used for signal callbacks.
        """
        if not catalog_name.endswith(".json"):
            catalog_name += ".json"
        url = self._server.format(name=catalog_name)
        self.__reply = self.__fetch_data(url=url)
        self.__reply.finished.connect(partial(self.__handle_response, catalog_name, catalog_title, False))

    def __handle_response(self, catalog_name: str, catalog_title: str, is_overview_response: bool):
        """Process the network reply: cache-compare via Last-Modified, emit signals, or retry next server."""
        error = self.__reply.error()

        if error == QNetworkReply.NetworkError.NoError:
            json_string = self.__reply.readAll().data().decode('utf-8')

            if is_overview_response:
                # WORKAROUND: Server liefert Overview als {…} mit trailing comma
                # statt als valides JSON-Array […]. Kann entfernt werden, sobald
                # das serverseitige Format korrigiert ist.
                json_string = json_string.replace('\r\n', '')
                json_string = re.sub(r'^{', '[', json_string)
                json_string = re.sub(r",}$", ']', json_string)
                json_string = re.sub(r"}$", ']', json_string)

            # Timestamps der letzten Modifikationen (lokal vs. Internet)
            # vergleichen und lokale Datei ueberschreiben, wenn Internet
            # neuer ist (eigene Cache-Implementation)
            networkLastModifiedRawValue = (
                self.__reply.rawHeader(
                    bytearray('Last-Modified', "utf-8"),
                ).data().decode()
            )
            try:
                networkLastModified = email.utils.parsedate_to_datetime(networkLastModifiedRawValue).timestamp()
            except (ValueError, TypeError):
                networkLastModified = 0.0
                QgsMessageLog.logMessage(
                    f"Invalid Last-Modified header: "
                    f"'{networkLastModifiedRawValue}'",
                    config.PLUGIN_NAME,
                    level=Qgis.MessageLevel.Warning,
                )
            self.successful = True
            self.done = True
            self.finished.emit(json_string, catalog_title, networkLastModified)

            total_server_list = config.ServerHosts.get_all_servers()
            index = total_server_list.index(self._server)
            QgsMessageLog.logMessage(
                f"Katalog '{catalog_name}' erfolgreich von "
                f"Server {index + 1} geladen",
                config.PLUGIN_NAME,
                level=Qgis.MessageLevel.Info,
            )
            return

        curr_server_index = self._server_list.index(self._server)
        if curr_server_index == len(self._server_list) - 1:
            self.error_occurred.emit("Netzwerkfehler beim Laden der URL's", catalog_title)
            self.done = True
            QgsMessageLog.logMessage(
                f"Katalog '{catalog_name}' konnte nicht von "
                "einem Server geladen werden",
                config.PLUGIN_NAME,
                level=Qgis.MessageLevel.Warning,
            )
        else:
            self._server = self._server_list[curr_server_index + 1]
            if is_overview_response:
                self.fetch_catalog_overview()
            else:
                self.fetch_catalog(catalog_name, catalog_title)

class CatalogManager:
    """Singleton-style registry that manages catalog data, caching and internal properties.

    All methods are classmethods; state is kept on the class itself.
    Coordinates ``NetworkHandler`` instances for async fetching and
    persists catalogs as JSON files for offline/fallback use.
    """

    overview = None
    catalogs = {}
    properties: dict[config.InternalProperties, dict[str, bool]] = {}
    catalog_path = f'{config.PLUGIN_DIR}/catalogs/'

    catalog_network_handlers: dict[str, NetworkHandler] = {}

    _pending_callbacks: dict[str, Callable] = {}

    @classmethod
    def setup(cls, iface: QgisInterface) -> None:
        """Initialize the manager with the QGIS interface and load persisted properties.

        Args:
            iface: The running QGIS application interface.
        """
        cls.iface = iface
        cls.properties = cls.load_internal_properties()

    @classmethod
    def add_network_handler(cls, catalog_title: str) -> NetworkHandler:
        """Return an existing handler for *catalog_title* or create a new one.

        Args:
            catalog_title: Human-readable catalog title used as lookup key.

        Returns:
            A ``NetworkHandler`` wired to ``add_catalog`` and ``handle_fetch_error``.
        """
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
        """Clear all handlers once every fetch has completed and show a summary message."""
        if all(handler.done for handler in cls.catalog_network_handlers.values()):
            successful_count = sum(handler.successful for handler in cls.catalog_network_handlers.values())
            handler_count = len(cls.catalog_network_handlers)
            message = f"Es wurden {successful_count} von {handler_count} Kataloge neu geladen"

            if successful_count / handler_count >= 0.5:
                cls.iface.messageBar().pushMessage(
                    config.PLUGIN_NAME_AND_VERSION, message,
                    level=Qgis.MessageLevel.Success, duration=5,
                )
            else:
                cls.iface.messageBar().pushMessage(
                    config.PLUGIN_NAME_AND_VERSION, message,
                    level=Qgis.MessageLevel.Warning, duration=8,
                )

            cls.catalog_network_handlers.clear()

    @classmethod
    def set_overview(cls, overview: str, catalog_name: str, last_modified: float, fetch_catalogs: bool = True) -> None:
        """Parse and store the catalog overview, optionally triggering individual catalog fetches.

        Args:
            overview: Raw JSON string of the overview.
            catalog_name: Identifier used for cache file naming.
            last_modified: Server-side timestamp for cache comparison.
            fetch_catalogs: If ``True``, immediately fetch every catalog listed in the overview.
        """
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
    def get_overview(cls, callback: Callable | None = None) -> None:
        """Start an async fetch of the catalog overview.

        Args:
            callback: Optional callable invoked (with no arguments) once the overview is available.
        """
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
    def get_catalog(
        cls, catalog_title: str,
        catalog_name: str | None = None,
        callback: Callable | None = None,
    ) -> None | dict | list:
        """Return a catalog by title, fetching it asynchronously if not yet loaded.

        Args:
            catalog_title: Human-readable title of the catalog.
            catalog_name: File name of the catalog (required when overview is not yet loaded).
            callback: Optional callable receiving the catalog data once available.

        Returns:
            The catalog data if already cached, otherwise ``None`` (result
            delivered later via *callback*).
        """
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
            cls.iface.messageBar().pushMessage(
                config.PLUGIN_NAME_AND_VERSION,
                "Katalog Übersicht ist nicht geladen, "
                "Bitte warten Sie oder kontaktieren Sie den Author",
                level=Qgis.MessageLevel.Warning, duration=8,
            )
        else:
            if callback:
                if catalog_title not in cls._pending_callbacks:
                    cls._pending_callbacks[catalog_title] = []
                cls._pending_callbacks[catalog_title].append(callback)

            if cls.overview is not None:
                catalog_info: dict[str, str] = next(x for x in cls.overview if x["titel"] == catalog_title)  # type: ignore
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
    def get_current_catalog(cls, callback: Callable | None = None) -> None | dict | list:
        """Return the catalog selected in QgsSettings, or ``None`` if none is configured.

        Args:
            callback: Optional callable forwarded to ``get_catalog``.

        Returns:
            Catalog data, or ``None`` if no catalog is selected or data is not yet available.
        """
        qgs_settings = QgsSettings()
        current_catalog = qgs_settings.value(config.CURRENT_CATALOG_SETTINGS_KEY)
        if current_catalog is None or "name" not in current_catalog:
            return None

        return cls.get_catalog(current_catalog["titel"], current_catalog["name"], callback)

    @classmethod
    def add_catalog(cls, catalog: str, catalog_name: str, last_modified: float) -> None:
        """Parse, enrich and cache a fetched catalog. Connected as slot to ``NetworkHandler.finished``.

        Args:
            catalog: Raw JSON string of the catalog.
            catalog_name: Human-readable title (used as dict key and for the cache file name).
            last_modified: Server-side timestamp for cache comparison.
        """
        catalog = json.loads(catalog)
        if isinstance(catalog, dict):
            catalog = cls.set_internal_properties(catalog)
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
        """Handle a failed catalog fetch by falling back to the local cache.

        Args:
            error: Human-readable error description.
            catalog_name: Title of the catalog that failed to load.
        """
        is_overview_response = catalog_name == config.CATALOG_OVERVIEW_NAME

        file_name = (
            re.sub(r'\ ', '_', catalog_name.split(':')[0].lower())
            if not is_overview_response
            else 'katalog_overview'
        )
        file_path = pathlib.Path(cls.catalog_path + file_name + '.json')
        if not file_path.exists():
            error += ", Überprüfen Sie die Internetverbindung oder kontaktieren Sie den Autor"
            cls.iface.messageBar().pushMessage(
                config.PLUGIN_NAME_AND_VERSION, error,
                level=Qgis.MessageLevel.Warning, duration=8,
            )

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
        else:
            cls.overview = services
            for catalog in cls.overview:
                # ------- Network Handler für die einzelnen Kataloge erstellen -------------
                handler = cls.add_network_handler(catalog["titel"])
                handler.fetch_catalog(catalog["name"], catalog["titel"])

        error += ", Verwendung der gecachten Daten"
        cls.iface.messageBar().pushMessage(
            config.PLUGIN_NAME_AND_VERSION, error,
            level=Qgis.MessageLevel.Warning, duration=5,
        )

        if catalog_name in cls._pending_callbacks:
            for callback in cls._pending_callbacks[catalog_name]:
                if is_overview_response:
                    callback()
                else:
                    callback(services)
            del cls._pending_callbacks[catalog_name]

        cls.clear_network_handlers()

    @classmethod
    def load_internal_properties(cls) -> dict[config.InternalProperties, dict[str, bool]]:
        """Load internal properties (visibility, loading, favorites) from disk and QgsSettings.

        Performs a one-time migration of legacy favorites from ``settings.json``
        into ``QgsSettings``.

        Returns:
            Mapping of each ``InternalProperties`` member to its per-path boolean state.
        """
        props = config.InternalProperties.get_properties()
        properties = {}

        file_path = pathlib.Path(cls.catalog_path + "settings.json")
        data = cls.read_json(file_path)
        if isinstance(data, dict):
            for prop in props:
                properties[prop] = {}
                if "properties" in data:
                    properties[prop] = data["properties"].get(prop.value, {})

        # Favoriten aus QgsSettings laden
        qgs_settings = QgsSettings()
        favorites = qgs_settings.value(config.FAVORITES_SETTINGS_KEY, {})
        if not isinstance(favorites, dict):
            favorites = {}

        # Einmalige Migration: alte Favoriten aus settings.json übernehmen
        if not favorites and isinstance(data, dict) and "properties" in data:
            old_favorites = data["properties"].get(config.InternalProperties.FAVORITE.value, {})
            if old_favorites:
                favorites = old_favorites
                qgs_settings.setValue(config.FAVORITES_SETTINGS_KEY, favorites)

        properties[config.InternalProperties.FAVORITE] = favorites

        return properties

    @classmethod
    def update_internal_properties(
        cls,
        values: (list[tuple[str, bool]]
                 | dict[config.InternalProperties, dict[str, bool]]),
        property: config.InternalProperties | None = None,
    ) -> None:
        """Merge new property values into the current state and persist them.

        Args:
            values: Either a list of ``(path, state)`` tuples for a single property,
                or a dict mapping multiple ``InternalProperties`` to their updates.
            property: Required when *values* is a list; identifies which property to update.
        """
        if isinstance(values, list):
            if property is None:
                raise ValueError("No property given")
            for path, state in values:
                cls.properties[property][path] = state
        else:
            for property, value in values.items():
                for path, state in value.items():
                    cls.properties[property][path] = state

        current_catalog = cls.get_current_catalog()
        if current_catalog is None:
            return

        current_catalog = dict(current_catalog)
        current_catalog = cls.set_internal_properties(current_catalog)

        qgs_settings = QgsSettings()
        metadata = qgs_settings.value(config.CURRENT_CATALOG_SETTINGS_KEY)
        cls.catalogs[metadata["name"]] = current_catalog

        cls.save_internal_properties()

    @classmethod
    def set_internal_properties(cls, catalog: dict) -> dict:
        """Enrich a catalog dict with visibility, loading, favorite and path flags.

        Args:
            catalog: Raw catalog dictionary to annotate in-place.

        Returns:
            The same *catalog* dict with ``InternalProperties`` keys injected.
        """
        def _apply_properties_flags(data: dict, path_prefix: str = ""):
            for key, value in data.items():
                path = f"{path_prefix}/{key}" if path_prefix else key
                # Default visible if not in map
                visible = cls.properties[config.InternalProperties.VISIBILITY].get(path, True)
                loadable = cls.properties[config.InternalProperties.LOADING].get(path, True)
                favorite = cls.properties[config.InternalProperties.FAVORITE].get(path, False)

                if isinstance(value, dict):
                    if key != "themen" and key != "layers":
                        data[key][config.InternalProperties.VISIBILITY] = visible
                        data[key][config.InternalProperties.LOADING] = loadable
                        data[key][config.InternalProperties.FAVORITE] = favorite
                        data[key][config.InternalProperties.PATH] = path
                    _apply_properties_flags(value, path)

        _apply_properties_flags(catalog)

        return catalog

    @classmethod
    def save_internal_properties(cls) -> None:
        """Persist current properties: favorites to QgsSettings, the rest to ``settings.json``."""
        # Favoriten in QgsSettings speichern
        qgs_settings = QgsSettings()
        qgs_settings.setValue(config.FAVORITES_SETTINGS_KEY, cls.properties.get(config.InternalProperties.FAVORITE, {}))

        # Restliche Properties (Sichtbarkeit, Laden) in settings.json
        file_path = pathlib.Path(cls.catalog_path + "settings.json")
        file_properties = {k.value: v for k, v in cls.properties.items() if k != config.InternalProperties.FAVORITE}
        data = {
            "properties": file_properties
        }
        cls.write_json(data, file_path)

    @classmethod
    def write_json(cls, data: dict | str, file_path: pathlib.Path) -> None:
        """Serialize *data* as pretty-printed JSON and write it to *file_path*.

        Args:
            data: Python object (or already-serialized string) to persist.
            file_path: Destination path; parent directories are created if needed.
        """
        file_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8", newline="\n") as file:
            data = json.dumps(data, indent=2)
            file.write(data)

    @classmethod
    def read_json(cls, file_path: pathlib.Path) -> dict | list:
        """Read and parse a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Parsed JSON content, or an empty dict if the file does not exist.
        """
        if not file_path.exists():
            return {}

        services: dict | list
        with open(file_path, encoding="utf-8") as file:
            services = json.load(file)
        return services
