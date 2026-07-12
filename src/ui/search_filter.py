from typing import Optional, Union

from qgis.core import QgsLocatorFilter, QgsLocatorResult, QgsLocatorContext, QgsFeedback
from ..operations import topic_ops
from ..core import search_index
# Strings wie Beschreibung und Name werden nicht übersetzt und sind momentan nur in Deutsch 

class SearchFilter(QgsLocatorFilter):
        
    def __init__(self):
        super().__init__()
        self.setUseWithoutPrefix(True)
        # Not pretty but it is what it is

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
        return self.__class__()
    
      # @override
    def prepare(
        self,
        string: Union[str, None],
        context: QgsLocatorContext,
    ) -> list[str]:
        """Stellt den Katalog-Snapshot im Main Thread bereit.

        Laut QgsLocatorFilter-Doku laeuft ``prepare()`` garantiert im Main
        Thread, waehrend ``fetchResults()`` standardmaessig im Hintergrund
        ausgefuehrt wird. Der Modul-Cache in ``search_index`` wird nur bei
        echten Katalog-Mutationen via ``catalog_mutated``-Signal
        invalidiert — nicht bei jedem Tastendruck.
        """
        search_index.get_entries()
        return []
    
    # @override
    def fetchResults(self, string: Optional[str], context: QgsLocatorContext, feedback: Optional[QgsFeedback]) -> None:
        if string is None:
            return
        
        string = string.lower()
        string = string.removeprefix(self.prefix())
        if len(string) < 3 or not feedback or feedback.isCanceled():
            return
        
        # Momentan werden nur Knoten zurückgegeben aber nicht die Ebenen darin. So lassen oder wirklich alle Ebenen anzeigen? Kann halt bei Knoten die Resultate stark vergrößern (bspw. bei Verwaltungsgrenzen)
        tokens = search_index.tokenize(string)
        search_results = search_index.find(tokens)
        for search_result in search_results:
            if feedback.isCanceled():
                return
            
            score = search_index.score(search_result, tokens)
            
            locator_result = QgsLocatorResult(self, search_result.name, search_result.path)
            locator_result.group = search_result.region_name
            locator_result.score = score
            locator_result.description = f"Katalog: {search_result.catalog_name}"
            self.resultFetched.emit(locator_result)

    # @override
    def triggerResult(self, result: QgsLocatorResult):
        # FIXME: result.userData according to doc, but property not found in Python or C++/SIP
        path = result.userData          # type: ignore
        topic_ops.add_topic(path)