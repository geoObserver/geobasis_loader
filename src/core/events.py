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
    
    current_catalog_updated = pyqtSignal()
    overview_updated = pyqtSignal()
    
    automatic_crs_changed = pyqtSignal()
    server_selection_changed = pyqtSignal()
    
    display_highlight_favorites_changed = pyqtSignal()
    
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
    
    def emit_current_catalog_updated(self):
        """
        Emit a signal to notify listeners that the current catalog has been updated.
        """
        self.current_catalog_updated.emit()

    def emit_overview_updated(self):
        """
        Emit a signal to notify listeners that the overview has been updated.
        """
        self.overview_updated.emit()
    
    def emit_automatic_crs_changed(self):
        """
        Emit a signal to notify listeners that the automatic CRS setting has changed.

        :param automatic_crs: The new state of the automatic CRS setting.
        """
        self.automatic_crs_changed.emit()

    def emit_server_selection_changed(self):
        """
        Emit a signal to notify listeners that the server selection has changed.

        :param server: The new selected server.
        """
        self.server_selection_changed.emit()
    
    def emit_general_settings_changed(self):
        """
        Emit a signal to notify listeners that general settings have changed.
        """
        self.emit_automatic_crs_changed()
        self.emit_server_selection_changed()
    
    def emit_display_highlight_favorites_changed(self):
        """
        Emit a signal to notify listeners that the display highlight favorites setting has changed.
        """
        self.display_highlight_favorites_changed.emit()

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
    
    def connect_current_catalog_updated(self, slot):
        """
        Connect a slot to the current_catalog_updated signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.current_catalog_updated.connect(slot)
        
    def connect_overview_updated(self, slot):
        """
        Connect a slot to the overview_updated signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.overview_updated.connect(slot)
    
    def connect_automatic_crs_changed(self, slot):
        """
        Connect a slot to the automatic_crs_changed signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.automatic_crs_changed.connect(slot)
    
    def connect_server_selection_changed(self, slot):
        """
        Connect a slot to the server_selection_changed signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.server_selection_changed.connect(slot)
    
    def connect_display_highlight_favorites_changed(self, slot):
        """
        Connect a slot to the display_highlight_favorites_changed signal.

        :param slot: The function to be called when the signal is emitted.
        """
        self.display_highlight_favorites_changed.connect(slot)