from typing import Optional, override
from qgis.core import QgsLocatorFilter

# Strings wie Beschreibung und Name werden nicht übersetzt und sind momentan nur in Deutsch 

# TODO: QGIS crash wenn Plugin neugeladen wird und Locator verwendet wird

class SearchFilter(QgsLocatorFilter):
    def __init__(self):
        super().__init__()

    @override
    def name(self) -> str:
        return "GeoBasis_Loader Suche"
    
    @override
    def displayName(self) -> str:
        return self.name()

    @override
    def description(self) -> str:
        return "Nach einem Thema im GeoBasis_Loader suchen"
    
    @override
    def prefix(self) -> str:        
        return "gbl"
    
    @override
    def clone(self) -> Optional[QgsLocatorFilter]:
        return self.__class__()