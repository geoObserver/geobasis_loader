from typing import Optional, Union

from qgis.core import QgsLocatorFilter, QgsLocatorResult, QgsLocatorContext, QgsFeedback
from ..catalog import models as catalog_types
from ..catalog.topic import topic_app
from .search_repository import SearchIndex
from ...core import icons
# Strings wie Beschreibung und Name werden nicht übersetzt und sind momentan nur in Deutsch 

class SearchFilter(QgsLocatorFilter):
    def __init__(self, search_index: SearchIndex, topic_loader: topic_app.TopicLoader):
        super().__init__()
        self.search_index = search_index
        self.topic_loader = topic_loader
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
        return self.__class__(self.search_index, self.topic_loader)
    
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
        self.search_index.get_entries()
        return []
    
    # @override
    def fetchResults(self, string: Optional[str], context: QgsLocatorContext, feedback: Optional[QgsFeedback]) -> None:
        if string is None:
            return
        
        string = string.lower()
        if len(string) < 2 or not feedback or feedback.isCanceled():
            return
        
        # Momentan werden nur Knoten zurückgegeben aber nicht die Ebenen darin. So lassen oder wirklich alle Ebenen anzeigen? Kann halt bei Knoten die Resultate stark vergrößern (bspw. bei Verwaltungsgrenzen)
        tokens = self.search_index.tokenize(string)
        search_results = self.search_index.find(tokens)
        for search_result, score in search_results:
            if feedback.isCanceled():
                return
            
            locator_result = QgsLocatorResult(self, search_result.title, search_result.id)
            locator_result.group = search_result.region_title
            locator_result.score = score
            locator_result.description = f"Katalog: {search_result.catalog_title}"
            if search_result.entry_type == catalog_types.EntryType.TOPIC:
                locator_result.icon = icons.get_icon(search_result.service_type)
            elif search_result.entry_type == catalog_types.EntryType.TOPIC_GROUP:
                locator_result.icon = icons.get_icon(icons.IconKey.GROUP_ADD)
            elif search_result.entry_type == catalog_types.EntryType.TOPIC_COMBINATION:
                locator_result.icon = icons.get_icon(icons.IconKey.COMBINATION_ADD)
            self.resultFetched.emit(locator_result)

    # @override
    def triggerResult(self, result: QgsLocatorResult):
        # FIXME: result.userData according to doc, but property not found in Python or C++/SIP
        id = result.userData          # type: ignore
        # This sould be fine because if the search result isnt found in the catalog manager of the index, something is wrong
        self.topic_loader.add_topic_by_id(id, self.search_index.catalog_manager)
