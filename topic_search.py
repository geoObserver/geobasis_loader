from typing import Optional

from . import config
from qgis.core import QgsLocatorFilter, QgsLocatorResult, QgsLocatorContext, QgsFeedback, QgsMessageLog
# Strings wie Beschreibung und Name werden nicht übersetzt und sind momentan nur in Deutsch 

class SearchFilter(QgsLocatorFilter):
    search_index = []
    
    def __init__(self, gbl):
        super().__init__()
        self.setUseWithoutPrefix(True)
        # Not pretty but it is what it is
        self.gbl = gbl
        self._search_index = SearchFilter.search_index

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
        
        # Momentan werden nur Knoten zurückgegeben aber nicht die Ebenen darin. So lassen oder wirklich alle Ebenen anzeigen? Kann halt bei Knoten die Resultate stark vergrößern (bspw. bei Verwaltungsgrenzen)
        search_results = self.search_results(string)
        for search_result in search_results:
            if feedback.isCanceled():
                return
            
            if not search_result["hit"]:
                continue
            
            locator_result = QgsLocatorResult(self, search_result["name"], search_result)
            locator_result.group = search_result["region"]
            locator_result.score = 1.0 if string == search_result["name"].lower() else 0.5
            locator_result.description = f"Katalog: {search_result["catalog_name"]}"
            self.resultFetched.emit(locator_result)

    # @override
    def triggerResult(self, result: QgsLocatorResult):
        # FIXME: Currently private method -> just result.userData according to doc, but property not found in Python or C++
        data = result._userData()
        self.gbl.add_topic(data["catalog_name"], data["path"])
    
    @classmethod
    def build_search_index(cls, catalogs: dict) -> None:
        search_index = []
        
        for catalog_name, catalog in catalogs.items():
            if not catalog:
                continue
            
            for _, region in catalog:
                if not isinstance(region, dict) or "themen" not in region:
                    continue
            
                topics = region.get("themen", {})
                for _, topic in topics.items():
                    if not isinstance(topic, dict):
                        continue
                    
                    name = topic.get("name", "")
                    keywords = topic.get("keywords", [])
                    if not isinstance(keywords, list):
                        keywords = []
                    
                    search_index.append({
                        "name": name,
                        "name_lower": name.lower(),
                        "region": region["menu"],
                        "keywords_lower": [kw.lower() for kw in keywords if isinstance(kw, str)],
                        "catalog_name": catalog_name,
                        "path": topic.get(config.InternalProperties.PATH, ""),
                    })
        
        cls.search_index = search_index

    def search_results(self, search_string: str):
        search_string = search_string.lower().strip()
        
        for index in self._search_index:
            hit = False
            if search_string in index["name_lower"]:
                hit = True
            elif any(search_string in kw for kw in index["keywords_lower"]):
                hit = True

            data = index.copy()
            data["hit"] = hit
            
            yield data