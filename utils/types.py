from __future__ import annotations
from dataclasses import dataclass

#
# Diese Datei und die enthaltenen Klassen werden noch nicht verwendet
# Sie sind aber bereits implementiert und können in Zukunft für Type Annotations verwendet werden
#

@dataclass
class Layer:
    """A data class to represent a Layer with various attributes."""

    name: str
    type: str
    valid_epsg: list[str]
    uri: str

    opacity: float | None = None
    minScale: float | None = None
    maxScale: float | None = None
    fillColor: str | list[int] | None = None
    strokeWidth: float | None = None
    separator: bool | None = False

@dataclass
class LayerGroup:
    """A data class to represent a LayerGroup with various attributes. A LayerGroup is a collection of Layers."""

    name: str
    layers: dict[str, Layer]

    separator: bool | None = False

@dataclass
class LayerCombination:
    """A data class to represent a LayerCombination with various attributes. A LayerCombination references existing Layers."""

    name: str
    layers: list[str]

    separator: bool | None = False

@dataclass
class LayerTheme:
    """A data class to represent a LayerTheme with various attributes. A LayerTheme is a collection of Layers, LayerGroups and LayerCombinations."""

    kategorie: str
    themen: dict[str, Layer | LayerGroup | LayerCombination]
