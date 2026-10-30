from typing import Callable
from qgis.PyQt.QtCore import pyqtBoundSignal, QObject


def disconnect_signal(signal: pyqtBoundSignal, slot: Callable) -> None:
    """Safely disconnect a signal from a slot, ignoring errors if not connected."""
    try:
        signal.disconnect(slot)
    except (TypeError, RuntimeError):
        pass

def disconnect_all_signals(obj: QObject) -> None:
    """Disconnect all signals from a QObject."""
    for signal_name in dir(obj):
        signal = getattr(obj, signal_name)
        if isinstance(signal, pyqtBoundSignal):
            try:
                signal.disconnect()
            except (TypeError, RuntimeError):
                pass