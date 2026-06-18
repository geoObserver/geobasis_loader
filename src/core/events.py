from qgis.PyQt.QtCore import QObject, pyqtSignal

class Events(QObject):
    """
    A class to manage events in the application.
    """

    # Define signals for various events
    presets_updated = pyqtSignal()
    favorites_updated = pyqtSignal()
    visibility_updated = pyqtSignal()
    enabled_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
    
    def emit_presets_updated(self):
        """
        Emit the presets_updated signal to notify listeners that presets have been updated.
        """
        self.presets_updated.emit()
        
    def emit_favorites_updated(self):
        """
        Emit the favorites_updated signal to notify listeners that favorites have been updated.
        """
        self.favorites_updated.emit()
    
    def emit_visibility_updated(self):
        """
        Emit a signal to notify listeners that visibility has been updated.
        """
        self.visibility_updated.emit()
    
    def emit_enabled_updated(self):
        """
        Emit a signal to notify listeners that enabled state has been updated.
        """
        self.enabled_updated.emit()
    
    def connect_presets_updated(self, slot):
        """
        Connect a slot to the presets_updated signal.
        
        :param slot: The function to be called when the signal is emitted.
        """
        self.presets_updated.connect(slot)

    def connect_favorites_updated(self, slot):
        """
        Connect a slot to the favorites_updated signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.favorites_updated.connect(slot)
    
    def connect_visibility_updated(self, slot):
        """
        Connect a slot to the visibility_updated signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.visibility_updated.connect(slot)
    
    def connect_enabled_updated(self, slot):
        """
        Connect a slot to the enabled_updated signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.enabled_updated.connect(slot)