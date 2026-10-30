import pathlib
from typing import Optional
from .models import DataSource, ServerDataSource, LocalDataSource
from ...core import PluginSettings
from ...core import config
from .catalog_exceptions import DataSourceAlreadyExistsError
from ...core.utils import custom_logger

logger = custom_logger.get_logger(__name__)

class DataSourceManager:
    def __init__(self):
        self.data_sources: dict[str, DataSource] = {}
        data_source = self.get_official_data_source()
        # self.data_sources[data_source.name] = data_source
        
        self.add_data_source(LocalDataSource(
            name="Lokale GeoObserver Datenquelle",
            index_name="GeoBasis_Loader_v7_Index.json",
            base_path=pathlib.Path("C:\\Users\\Anton\\AppData\\Roaming\\QGIS\\QGIS4\\profiles\\default\\python\\plugins\\geobasis_loader\\kataloge")
        ))
    
    def add_data_source(self, data_source: DataSource) -> None:
        if data_source.name in self.data_sources:
            raise DataSourceAlreadyExistsError(data_source.name)
        self.data_sources[data_source.name] = data_source

    def get_official_data_source(self) -> ServerDataSource:
        urls = [
            config.GEOOBSERVER_SERVICE,
            config.GITHUB_SERVICE
        ]
        settings = PluginSettings()
        current_server_index = settings.current_server
        service = ServerDataSource(
            name="Offizielle GeoObserver Datenquelle", 
            index_name="GeoBasis_Loader_v7_Kataloge.json", 
            urls=urls,
            cache_path=config.CACHE_DIR
            )
        service.set_enabled_urls_by_indices([current_server_index])
        return service

    def get_data_source(self, name: str) -> Optional[DataSource]:
        return self.data_sources.get(name)
    
    def get_all_data_sources(self) -> list[DataSource]:
        return list(self.data_sources.values())