import copy
from typing import Any, Generator, Generic, Optional, Sequence, TypeVar
from ..models import BasicCatalogData, BasicCatalogEntry, BasicCatalogTopicEntry
from ..types import CatalogEntryType
from .. import icons


TNode = TypeVar("TNode", bound="BasicCatalogDataUiModel[Any]")


class BasicCatalogDataUiModel(Generic[TNode]):
    def __init__(self, entry: BasicCatalogData, child_nodes: Optional[Sequence[TNode]] = None):
        self._entry = entry
        self.child_nodes: list[TNode] = list(child_nodes) if child_nodes is not None else []

    def __iter__(self) -> Generator[TNode, None, None]:
        yield from self.child_nodes

    @property
    def entry(self) -> BasicCatalogData:
        return self._entry

    @property
    def id(self) -> str:
        return self.entry.id

    @property
    def title(self) -> str:
        return self.entry.title

    @property
    def tooltip(self) -> str:
        try:
            return self.entry.get_summary()
        except NotImplementedError:
            return self.entry.title

    @property
    def separator(self) -> bool:
        return self.entry.separator_after

    def get_additional_node(self) -> "BasicCatalogDataUiModel[TNode]":
        c: BasicCatalogDataUiModel[TNode] = copy.copy(self)
        c.child_nodes = []
        return c

    def get_icon(self) -> icons.icon_infrastructure.QIcon:
        """Returns the appropriate icon for the topic entry."""

        if len(self.child_nodes) > 0:
            return icons.get_icon(icons.IconKey.FOLDER_CLOSED)

        if not isinstance(self.entry, BasicCatalogEntry):
            return icons.get_icon(icons.IconKey.FOLDER_CLOSED)

        entry_type = self.entry.entry_type
        if entry_type == CatalogEntryType.TOPIC:
            if isinstance(self.entry, BasicCatalogTopicEntry):
                return icons.get_icon(self.entry.service_type)
            else:
                return icons.get_icon(icons.IconKey.GROUP_ADD)
        elif entry_type == CatalogEntryType.TOPIC_GROUP:
            return icons.get_icon(icons.IconKey.GROUP_ADD)
        elif entry_type == CatalogEntryType.TOPIC_COMBINATION:
            return icons.get_icon(icons.IconKey.COMBINATION_ADD)
        else:
            return icons.get_icon(icons.IconKey.FOLDER_CLOSED)