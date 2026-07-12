from typing import Generator

from ..models.search_types import SearchEntry
from ..models import catalog_types
from ..services import registry

class SearchIndex:
    def __init__(self):
        self._index = None
    
    def build(self) -> None:
        search_index = ()
        # Only offical catalogs, later tuple with official-user catalogs
        catalogs = registry.catalog_manager.get_all_catalogs()
        
        for catalog in catalogs:
            if not catalog:
                continue
            
            for region in catalog.get_regions():
                for topic in region.get_topics():
                    entry = SearchEntry(
                        catalog_name=catalog.name,
                        region_name=region.name,
                        name=topic.name,
                        layer_type=topic.topic_type if isinstance(topic, catalog_types.Topic) else "",
                        path=topic.path,
                        name_lower=topic.name.casefold(),
                        keywords_lower=frozenset(kw.casefold() for kw in topic.keywords if isinstance(kw, str)),
                        group_name="",
                        group_path=""
                    )
                    search_index += (entry,)
                    
                    if isinstance(topic, catalog_types.TopicGroup):
                        for subtopic in topic.get_subtopics():
                            entry = SearchEntry(
                                catalog_name=catalog.name,
                                region_name=region.name,
                                name=subtopic.name,
                                layer_type=subtopic.topic_type,
                                path=subtopic.path,
                                name_lower=subtopic.name.casefold(),
                                keywords_lower=frozenset(kw.casefold() for kw in subtopic.keywords if isinstance(kw, str)),
                                group_name=topic.name,
                                group_path=topic.path
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
    
    def find(self, tokens: tuple[str, ...]) -> Generator[SearchEntry, None, None]:
        if not tokens:
            yield from ()
        
        for entry in self.peek_entries():
            if all(token in entry.name_lower or any(token in kw for kw in entry.keywords_lower) for token in tokens):
                yield entry
    
    def score(self, entry: SearchEntry, tokens: tuple[str, ...]) -> int:
        score = 0
        for token in tokens:
            if entry.name_lower.startswith(token):
                score += 150
            elif token in entry.name_lower:
                score += 50
            if any(token in kw for kw in entry.keywords_lower):
                score += 25
        return score