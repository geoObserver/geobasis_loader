from ...core.exceptions import DataError, AlreadyExistsError, NotFoundError


class CatalogError(DataError):
    """Base class for catalog-related errors."""
    pass

class CatalogAlreadyExistsError(AlreadyExistsError, CatalogError):
    """Raised when an attempt is made to add a catalog that already exists."""
    def __init__(self, catalog_id: str):
        super().__init__("Catalog", catalog_id)

class CatalogNotFoundError(NotFoundError, CatalogError):
    """Raised when a catalog is not found."""
    def __init__(self, catalog_id: str):
        super().__init__("Catalog", catalog_id)

class EntryAlreadyExistsError(AlreadyExistsError, CatalogError):
    """Raised when an attempt is made to add a catalog entry that already exists."""
    def __init__(self, entry_id: str):
        super().__init__("Catalog entry", entry_id)

class DataSourceAlreadyExistsError(AlreadyExistsError, CatalogError):
    """Raised when an attempt is made to add a data source that already exists."""
    def __init__(self, data_source_name: str):
        super().__init__("Data source", data_source_name)

class NetworkHandlerAlreadyExistsError(AlreadyExistsError, CatalogError):
    """Raised when an attempt is made to add a network handler that already exists."""
    def __init__(self, handler_title: str):
        super().__init__("Network handler", handler_title)