from typing import Optional, Union
import uuid
from qgis.PyQt.QtCore import QObject, pyqtSignal, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import QgsNetworkAccessManager
from ..utils.custom_logger import get_logger

logger = get_logger(__name__)

REQUEST_TIMEOUT_MS = 10000  # Timeout in milliseconds

class NetworkHandler(QObject):
    finished = pyqtSignal(str, str)  # Signal to emit the response data and full title
    error_occurred = pyqtSignal(str, str)  # Signal to emit error messages with full title
    
    def __init__(self, title: str, urls: Union[list[str], str], manager: QgsNetworkAccessManager, parent: Optional[QObject] = None, group: str = ""):
        super().__init__(parent)
        self.title = title
        self.group = group
        urls = urls if isinstance(urls, list) else [urls]
        if len(urls) == 0:
            raise ValueError("At least one URL must be provided")
        self._urls = urls
        self._url_index = 0
        self._network_manager = manager
        self._reply = None
        self.done = False
        self.successful = False
    
    @property
    def full_title(self) -> str:
        return NetworkHandler.get_full_title(self.title, self.group)
    
    @staticmethod
    def get_full_title(title: str, group: str) -> str:
        return title if not group else f"{group} - {title}"
    
    def _fetch_data(self) -> Optional[QNetworkReply]:
        self._cleanup()
        
        url = self._urls[self._url_index]
        q_url = QUrl(url)
        if not q_url.isValid():
            logger.critical(f"Ungültige URL für '{self.title}': {url}")
            return None

        request = QNetworkRequest(q_url)
        request.setAttribute(QNetworkRequest.Attribute.CacheLoadControlAttribute, QNetworkRequest.CacheLoadControl.AlwaysNetwork)
        request.setTransferTimeout(REQUEST_TIMEOUT_MS)
        # FIXME
        if "github" in url:
            mediatype = "application/vnd.github.raw+json"
        else:
            mediatype = "gzip, deflate"
        request.setRawHeader(
            bytearray("Accept", "utf-8"),
            bytearray(mediatype, "utf-8")
        )
        return self._network_manager.get(request)
    
    def _handle_response(self) -> None:
        if self._reply is None:
            logger.critical(f"Keine Netzwerkantwort für '{self.full_title}' zum Verarbeiten vorhanden")
            return
        error = self._reply.error()
        status_code: Optional[int] = self._reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        
        if error == QNetworkReply.NetworkError.NoError and status_code == 200:
            try:
                string = self._reply.readAll().data().decode('utf-8')
            except UnicodeDecodeError as decode_error:
                logger.error(f"Ungültige UTF-8-Antwort für Netzwerkanfrage '{self.full_title}': {decode_error}")
            else:
                self.successful = True
                self.done = True
                self.finished.emit(string, self.full_title)
                
                logger.info(f"'{self.full_title}' erfolgreich von Server {self._url_index + 1} geladen")
                return
        
        if error == QNetworkReply.NetworkError.OperationCanceledError:
            logger.info(f"Netzwerkanfrage für '{self.full_title}' wurde abgebrochen")
            self.done = True
            return
        
        # Differenzierte Fehlerbehandlung
        if not status_code:
            logger.error(f"Kein Internet: '{self.full_title}' auf Server {self._urls[self._url_index]}")
        elif status_code == 200:
            logger.error(f"Unerwarteter Fehler beim Decoden oder Verarbeiten: '{self.full_title}' auf Server {self._urls[self._url_index]}")
        elif status_code == 404:
            logger.warning(f"404 Not Found: '{self.full_title}' auf Server {self._urls[self._url_index]}")
        elif status_code == 429:
            logger.warning(f"429 Rate Limit: Server {self._urls[self._url_index]}")
        elif status_code >= 500:
            logger.warning(f"Server-Fehler {status_code}: '{self.full_title}' auf Server {self._urls[self._url_index]}")
        else:
            logger.warning(f"Unbekannter Statuscode: {status_code} für '{self.full_title}' auf Server {self._urls[self._url_index]}")

        if self._url_index == len(self._urls) - 1:
            self.done = True
            logger.warning(f"'{self.full_title}' konnte nicht von einem Server geladen werden")
            self.error_occurred.emit("Netzwerkfehler beim Laden der URL's", self.full_title)
        else:
            self._url_index += 1
            self.start()  # Versuche die nächste URL
    
    def _cleanup(self) -> bool:
        is_finished = False
        if self._reply is not None:
            try:
                self._reply.finished.disconnect(self._handle_response)
            except (RuntimeError, TypeError):
                # Signal was never connected or already disconnected
                pass

            is_finished = self._reply.isFinished()
            if not is_finished:
                self._reply.abort()
            self._reply.deleteLater()
            self._reply = None
        
        return is_finished
    
    def start(self) -> None:
        self.done = False
        self.successful = False
        reply = self._fetch_data()
        if reply is None:
            return
        self._reply = reply
        self._reply.finished.connect(self._handle_response)
    
    def abort(self):
        was_finished = self._cleanup()
        if not was_finished:
            logger.info(f"Netzwerkanfrage für '{self.full_title}' wurde abgebrochen")
        
        self.done = True
        try:
            self.finished.disconnect()
        except (RuntimeError, TypeError):
            # No connections to disconnect
            pass
        try:
            self.error_occurred.disconnect()
        except (RuntimeError, TypeError):
            # No connections to disconnect
            pass
