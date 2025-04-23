from typing import Optional, override
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
        if len(search_string) < 2 or feedback.isCanceled():
            return
        
        print(search_string, feedback)
        
        result = QgsLocatorResult(self, "Ergebnis" + search_string)
        result.description = "Beschreibung" + search_string
        
        self.resultFetched.emit(result)