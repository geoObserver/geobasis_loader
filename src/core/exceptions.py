class PluginError(Exception):
    """Base class for plugin-related errors."""
    pass

class DataError(PluginError):
    """Raised when there is an error related to data processing."""
    pass

class InfrastructureError(PluginError):
    """Raised when there is an error related to infrastructure."""
    pass

class AlreadyExistsError(DataError):
    """Raised when an attempt is made to add a data source that already exists."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID '{entity_id}' already exists.")

class NotFoundError(DataError):
    """Raised when a requested entity is not found."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID '{entity_id}' not found.")