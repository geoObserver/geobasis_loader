from typing import Optional, override
from .catalog_manager import CatalogManager
from qgis.core import QgsLocatorFilter, QgsLocatorResult, QgsLocatorContext, QgsFeedback

# Strings wie Beschreibung und Name werden nicht übersetzt und sind momentan nur in Deutsch 

# TODO: QGIS crash wenn Plugin neugeladen wird und Locator verwendet wird

class SearchFilter(QgsLocatorFilter):
    def __init__(self):
        super().__init__()
        self.setUseWithoutPrefix(True)

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
        self.clearPreviousResults()
        return self.__class__()
    
    @override
    def fetchResults(self, search_string: str, context: QgsLocatorContext, feedback: QgsFeedback) -> None:
        search_string = search_string.lower()
        search_string.removeprefix(self.prefix())
        if len(search_string) < 3 or feedback.isCanceled():
            return
        
        for _, catalog in CatalogManager.catalogs.items():
            for _, group in catalog:
                if feedback.isCanceled():
                    return
                
                for _, topic in group["themen"].items():
                    hit = False
                    if search_string in topic["name"].lower():
                        hit = True
                    elif "keywords" in topic:
                        if any(search_string in keyword.lower() for keyword in topic["keywords"]):
                            hit = True
                
                    if hit:
                        result = QgsLocatorResult(self, topic["name"])
                        self.resultFetched.emit(result)
    
    @override
    def triggerResult(self, result):
        return super().triggerResult(result)