import logging
from types import TracebackType
from typing import Mapping
from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface
from .. import config


class GeoBasisLoaderLoggingHandler(logging.Handler):
    def get_qgis_severity(self, level: int) -> tuple[Qgis.MessageLevel, int]:
        if level in (logging.FATAL, logging.CRITICAL, logging.ERROR):
            return Qgis.MessageLevel.Critical, 10
        if level in (logging.WARN, logging.WARNING):
            return Qgis.MessageLevel.Warning, 5
        if level == logging.INFO:
            return Qgis.MessageLevel.Info, 4
        if level == config.LOGGING_SUCCESS_LEVEL:
            return Qgis.MessageLevel.Success, 2
        return Qgis.MessageLevel.NoLevel, 2

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno == logging.NOTSET:
            return

        qgis_message_level, qgis_message_duration = self.get_qgis_severity(record.levelno)
        message = record.getMessage()
        QgsMessageLog.logMessage(message, config.PLUGIN_NAME, qgis_message_level)
        
        if getattr(record, "show_banner", False):
            try:
                iface.messageBar().pushMessage(
                    config.PLUGIN_NAME_AND_VERSION,
                    message,
                    qgis_message_level,
                    qgis_message_duration,
                )
            except AttributeError:
                QgsMessageLog.logMessage(
                    "Messagebar not found during logging",
                    config.PLUGIN_NAME,
                    Qgis.MessageLevel.Critical,
                )


class GeoBasisLogger(logging.LoggerAdapter):
    def success(self,
        msg: object,
        *args: object,
        exc_info: None | bool | tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None] | BaseException = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        self.extra = extra          # Seems unnecessary but doesnt work without it
        self.log(config.LOGGING_SUCCESS_LEVEL, msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra, **kwargs)


def setup_logging() -> None:
    logging.addLevelName(config.LOGGING_SUCCESS_LEVEL, "SUCCESS")

    plugin_logger = logging.getLogger(config.PLUGIN_LOGGER_NAME)
    plugin_logger.setLevel(logging.INFO)
    plugin_logger.propagate = False

    remove_logging()
    plugin_logger.addHandler(GeoBasisLoaderLoggingHandler())


def remove_logging() -> None:
    plugin_logger = logging.getLogger(config.PLUGIN_LOGGER_NAME)
    handlers = [h for h in plugin_logger.handlers if isinstance(h, GeoBasisLoaderLoggingHandler)]
    for handler in handlers:
        plugin_logger.removeHandler(handler)
        handler.close()


def get_logger(name: str) -> GeoBasisLogger:
    child = logging.getLogger(f"{config.PLUGIN_LOGGER_NAME}.{name}")
    return GeoBasisLogger(child, None)

setup_logging()