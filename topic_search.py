from typing import Optional

from .catalog_manager import CatalogManager
from . import config
from qgis.core import QgsLocatorFilter, QgsLocatorResult, QgsLocatorContext, QgsFeedback
# Strings wie Beschreibung und Name werden nicht übersetzt und sind momentan nur in Deutsch 

class SearchFilter(QgsLocatorFilter):
    def __init__(self, gbl):
        super().__init__()
        self.setUseWithoutPrefix(True)
        # Not pretty but it is what it is
        self.gbl = gbl

    # @override
    def name(self) -> str:
        return "GeoBasis_Loader Suche"
    
    # @override
    def displayName(self) -> str:
        return self.name()

    # @override
    def description(self) -> str:
        return "Nach einem Thema im GeoBasis_Loader suchen"
    
    # @override
    def prefix(self) -> str:        
        return "gbl"
    
    # @override
    def clone(self) -> Optional[QgsLocatorFilter]:
        return self.__class__(self.gbl)
    
    # @override
    def fetchResults(self, string: Optional[str], context: QgsLocatorContext, feedback: Optional[QgsFeedback]) -> None:
        if string is None:
            return
        
        string = string.lower()
        string = string.removeprefix(self.prefix())
        if len(string) < 3 or not feedback or feedback.isCanceled():
            return
        
        for catalog_name, catalog in CatalogManager.catalogs.items():
            if not catalog:
                continue
            
            for group_key, group in catalog:
                if feedback.isCanceled():
                    return
                
                if not isinstance(group, dict) or "themen" not in group:
                    continue
                
                topics = group.get("themen", {})
                
                for topic_key, topic in topics.items():
                    if feedback.isCanceled():
                        return
                    
                    hit = False
                    if string in topic["name"].lower():
                        hit = True
                    elif "keywords" in topic:
                        if any(string in keyword.lower() for keyword in topic["keywords"]):
                            hit = True
                
                    # Momentan werden nur Knoten zurückgegeben aber nicht die Ebenen darin. So lassen oder wirklich alle Ebenen anzeigen? Kann halt bei Knoten die Resultate stark vergrößern (bspw. bei Verwaltungsgrenzen)
                
                    if hit:
                        data = {
                            "catalog_name": catalog_name,
                            "path": topic[config.InternalProperties.PATH],
                        }
                        result = QgsLocatorResult(self, topic["name"], data)
                        result.group = group.get("menu", group_key)
                        result.score = 1.0 if string == topic["name"].lower() else 0.5
                        result.description = f"Katalog: {catalog_name}"
                        self.resultFetched.emit(result)

    # @override
    def triggerResult(self, result: QgsLocatorResult):
        # FIXME: Currently private method -> just result.userData according to doc, but property not found in Python or C++
        data = result._userData()
        self.gbl.add_topic(data["catalog_name"], data["path"])