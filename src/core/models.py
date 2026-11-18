from dataclasses import dataclass
from typing import Optional
from .types import CatalogEntryType, CatalogEntryServiceType


@dataclass(frozen=True)
class BasicCatalogEntry:
    id: str
    title: str
    description: Optional[str] = None
    
    @property
    def entry_type(self) -> CatalogEntryType:
        raise NotImplementedError("Subclasses must implement the entry_type property.")

    def get_summary(self) -> str:
        """Returns a summary of the catalog entry."""
        raise NotImplementedError("Subclasses must implement the get_summary method.")

@dataclass(frozen=True)
class BasicCatalogTopicEntry(BasicCatalogEntry):
    service_type: CatalogEntryServiceType = CatalogEntryServiceType.WMS
