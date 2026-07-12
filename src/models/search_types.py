from dataclasses import dataclass

@dataclass(frozen=True)
class SearchEntry:
    """Immutable snapshot of a searchable catalog node."""

    catalog_name: str
    region_name: str
    name: str
    layer_type: str
    path: str
    name_lower: str
    keywords_lower: frozenset[str]
    group_name: str
    group_path: str
