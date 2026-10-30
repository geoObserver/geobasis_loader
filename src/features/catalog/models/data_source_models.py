from pathlib import Path
from typing import Optional, Union


class DataSource:
    def __init__(self, name: str, index_name: str):
        self.name = name
        self.index_name = index_name

class ServerDataSource(DataSource):
    def __init__(self, name: str, index_name: str, urls: Union[list[str], list[tuple[str, bool]]], cache_path: Optional[Path] = None):
        super().__init__(name, index_name)
        self.urls = self._convert_url_list(urls)  # List of tuples (url, is_active)
        self.cache_path = cache_path
    
    def _convert_url_list(self, urls: Union[list[str], list[tuple[str, bool]]]) -> list[tuple[str, bool]]:
        result = []
        for url in urls:
            if isinstance(url, str):
                result.append((url, True))  # If only strings are provided, mark all as active
            elif isinstance(url, tuple) and len(url) == 2 and isinstance(url[0], str) and isinstance(url[1], bool):
                result.append(url)  # If tuples are provided, use them as is
            else:
                continue  # Ignore invalid entries
        return result
    
    def get_url(self, index: int) -> Optional[tuple[str, bool]]:
        """Returns the URL at the specified index, otherwise returns None."""
        if 0 <= index < len(self.urls):
            return self.urls[index]
        return None

    def get_urls(self) -> list[str]:
        """Returns a list of all URLs for the server."""
        return [url for url, _ in self.urls]
    
    def get_enabled_urls(self) -> list[str]:
        """Returns a list of enabled URLs for the server."""
        return [url for url, is_active in self.urls if is_active]
    
    def set_enabled_urls(self, enabled_urls: list[str]) -> None:
        """Sets the enabled URLs for the server."""
        self.urls = [(url, url in enabled_urls) for url, _ in self.urls]
    
    def set_enabled_urls_by_indices(self, enabled_indices: list[int]) -> None:
        """Sets the enabled URLs for the server based on their indices."""
        if len(enabled_indices) == 1 and enabled_indices[0] == 0:
            enabled_indices = list(range(1, len(self.urls) + 1))  # Enable all if the first index is 0
        self.urls = [(url, (i+1) in enabled_indices) for i, (url, _) in enumerate(self.urls)]

    def convert_to_local(self) -> Optional['LocalDataSource']:
        """Converts the server data source to a local data source."""
        if self.cache_path is None:
            return None
        return LocalDataSource(self.name, self.index_name, self.cache_path)

class LocalDataSource(DataSource):
    def __init__(self, name: str, index_name: str, base_path: Path):
        super().__init__(name, index_name)
        self.base_path = base_path