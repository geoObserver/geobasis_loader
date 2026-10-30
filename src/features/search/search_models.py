from dataclasses import dataclass

@dataclass(frozen=True)
class SearchEntry:
    """Immutable snapshot of a searchable catalog node."""

    catalog_title: str
    region_title: str
    title: str
    entry_type: str
    service_type: str
    id: str
    name_lower: str
    keywords_lower: frozenset[str]
