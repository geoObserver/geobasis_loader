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
        return self.__class__()
    
    @override
    def fetchResults(self, string: Optional[str], context: QgsLocatorContext, feedback: QgsFeedback) -> None:
        if string is None:
            return
        
        string = string.lower()
        string.removeprefix(self.prefix())
        if len(string) < 3 or feedback.isCanceled():
            return
        
        for catalog_name, catalog in CatalogManager.catalogs.items():
            for group_key, group in catalog:
                if feedback.isCanceled():
                    return
                
                for topic_key, topic in group["themen"].items():
                    hit = False
                    if string in topic["name"].lower():
                        hit = True
                    elif "keywords" in topic:
                        if any(string in keyword.lower() for keyword in topic["keywords"]):
                            hit = True
                
                    if hit:
                        data = {
                            "catalog_name": catalog_name,
                            "group_key": group_key,
                            "topic_key": topic_key
                        }
                        result = QgsLocatorResult(self, topic["name"], data)
                        self.resultFetched.emit(result)
    
    @override
    def triggerResult(self, result: QgsLocatorResult):
        data = result._userData()
        print(result.displayString, data)