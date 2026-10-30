from typing import Generator
from qgis.core import QgsStringUtils
from .search_models import SearchEntry
from ..catalog import models as catalog_types
from ..catalog import CatalogManager

SCORE_THRESHOLD = 0.2

class SearchIndex:
    _index = None
    def __init__(self, catalog_manager: CatalogManager):
        self.catalog_manager = catalog_manager
        # FIXME: invalidate index upon adding/removing catalog
    
    def build(self) -> None:
        search_index = ()
        # Only offical catalogs, later tuple with official-user catalogs
        catalogs = self.catalog_manager.get_all_catalogs()
        
        for catalog in catalogs:
            if not catalog:
                continue
            
            for region in catalog.get_regions():
                for topic in region.get_topics():
                    entry = SearchEntry(
                        catalog_title=catalog.title,
                        region_title=region.title,
                        title=topic.title,
                        entry_type=topic.entry_type,
                        service_type=topic.service_type if isinstance(topic, catalog_types.Topic) else "",
                        id=topic.id,
                        name_lower=topic.title.casefold(),
                        keywords_lower=frozenset(kw.casefold() for kw in topic.keywords if isinstance(kw, str)),
                    )
                    search_index += (entry,)
                    
                    if not isinstance(topic, catalog_types.TopicGroup):
                        continue
                    
                    for subtopic in topic.get_subtopics():
                        entry = SearchEntry(
                            catalog_title=catalog.title,
                            region_title=region.title,
                            title=subtopic.title,
                            entry_type=subtopic.entry_type,
                            service_type=subtopic.service_type,
                            id=subtopic.id,
                            name_lower=subtopic.title.casefold(),
                            keywords_lower=frozenset(kw.casefold() for kw in subtopic.keywords if isinstance(kw, str)),
                        )
                        search_index += (entry,)

        self._index = search_index
    
    def clear(self) -> None:
        self._index = None
    
    def get_entries(self) -> tuple[SearchEntry, ...]:
        if self._index is None:
            self.build()
        return self._index or ()
    
    def peek_entries(self) -> tuple[SearchEntry, ...]:
        return self._index or ()
    
    def tokenize(self, search_string: str) -> tuple[str, ...]:
        return tuple(word.casefold() for word in search_string.strip().split() if word)
    
    def find(self, tokens: tuple[str, ...]) -> Generator[tuple[SearchEntry, float], None, None]:
        if not tokens:
            yield from ()
        
        for entry in self.peek_entries():
            score = self.score(entry, tokens)
            if score >= SCORE_THRESHOLD:
                yield entry, score
    
    def score(self, entry: SearchEntry, tokens: tuple[str, ...]) -> float:
        score = 0.0
        for token in tokens:
            score += QgsStringUtils.fuzzyScore(entry.name_lower, token)
            if entry.name_lower.startswith(token):
                score += 0.2
            # elif token in entry.name_lower:
            #     score += 50
            if any(kw.startswith(token) for kw in entry.keywords_lower):
                score += 0.05
        return score