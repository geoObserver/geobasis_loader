"""QGIS locator filter for searching topics in the GeoBasis_Loader catalog.

Integrates with the QGIS locator bar to let users search for geodata
topics by name or keyword across all loaded catalogs.
"""

from typing import Optional

from qgis.core import QgsFeedback, QgsLocatorContext, QgsLocatorFilter, QgsLocatorResult

from . import config
from .catalog_manager import CatalogManager

# Strings wie Beschreibung und Name werden nicht übersetzt und sind momentan nur in Deutsch

class SearchFilter(QgsLocatorFilter):
    """Locator filter that searches GeoBasis_Loader catalog topics.

    Allows users to find geodata topics by name or keyword via the QGIS
    locator bar (prefix ``gbl``). Selecting a result loads the
    corresponding topic into the map.
    """

    def __init__(self, gbl):
        """Initialize the search filter.

        Args:
            gbl: The main ``GeoBasis_Loader`` plugin instance, used to
                trigger topic loading on result selection.

        """
        super().__init__()
        self.setUseWithoutPrefix(True)
        # Not pretty but it is what it is
        self.gbl = gbl

    # @override
    def name(self) -> str:
        """Return the unique internal name of this filter.

        Overrides ``QgsLocatorFilter.name``.

        Returns:
            The filter's internal identifier string.

        """
        return self.tr("GeoBasis_Loader Search")

    # @override
    def displayName(self) -> str:
        """Return the human-readable display name shown in the locator bar.

        Overrides ``QgsLocatorFilter.displayName``.

        Returns:
            The display name (delegates to ``name``).

        """
        return self.name()

    # @override
    def description(self) -> str:
        """Return a short description of what this filter does.

        Overrides ``QgsLocatorFilter.description``.

        Returns:
            A user-facing description string (in German).

        """
        return self.tr("Search for a topic in GeoBasis_Loader")

    # @override
    def prefix(self) -> str:
        """Return the prefix that activates this filter in the locator bar.

        Overrides ``QgsLocatorFilter.prefix``.

        Returns:
            The prefix string ``"gbl"``.

        """
        return "gbl"

    # @override
    def clone(self) -> Optional[QgsLocatorFilter]:
        """Create a clone of this filter for use in background threads.

        Overrides ``QgsLocatorFilter.clone``.

        Returns:
            A new ``SearchFilter`` instance sharing the same plugin reference.

        """
        return self.__class__(self.gbl)

    # @override
    def fetchResults(self, string: Optional[str], context: QgsLocatorContext, feedback: Optional[QgsFeedback]) -> None:
        """Search all loaded catalogs for topics matching the query string.

        Overrides ``QgsLocatorFilter.fetchResults``. Matches against
        topic names and keywords (case-insensitive, minimum 3 characters).
        Emits ``resultFetched`` for each hit.

        Args:
            string: The user's search query from the locator bar.
            context: The locator context (unused but required by API).
            feedback: Feedback object used to check for cancellation.

        """
        if string is None:
            return

        string = string.lower()
        string = string.removeprefix(self.prefix())
        if len(string) < 3 or not feedback or feedback.isCanceled():
            return

        for catalog_name, catalog in CatalogManager.catalogs.items():
            for group_key, group in catalog:
                if feedback.isCanceled():
                    return

                for topic_key, topic in group["themen"].items():
                    hit = (
                        string in topic["name"].lower()
                        or ("keywords" in topic and any(
                            string in keyword.lower() for keyword in topic["keywords"]
                        ))
                    )

                    # Momentan werden nur Knoten zurueckgegeben aber nicht
                    # die Ebenen darin. So lassen oder wirklich alle Ebenen
                    # anzeigen? Kann bei Knoten die Resultate stark
                    # vergroessern (bspw. bei Verwaltungsgrenzen)

                    if hit:
                        data = {
                            "catalog_name": catalog_name,
                            "path": topic[config.InternalProperties.PATH],
                        }
                        result = QgsLocatorResult(self, topic["name"], data)
                        self.resultFetched.emit(result)

    # @override
    def triggerResult(self, result: QgsLocatorResult):
        """Handle selection of a search result by loading the topic.

        Overrides ``QgsLocatorFilter.triggerResult``. Extracts the
        catalog name and topic path from the result and delegates to
        ``GeoBasis_Loader.add_topic``.

        Args:
            result: The locator result the user selected.

        """
        data = result.userData()
        self.gbl.add_topic(data["catalog_name"], data["path"])
