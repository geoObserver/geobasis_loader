from dataclasses import dataclass, field
from typing import Optional, Union

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
    
    opacity: Optional[float] = None
    minScale: Optional[float] = None
    maxScale: Optional[float] = None
    fillColor: Optional[Union[str, list[int]]] = None
    strokeWidth: Optional[float] = None
    separator: Optional[bool] = False
    
@dataclass
class LayerGroup:
    """A data class to represent a LayerGroup with various attributes. A LayerGroup is a collection of Layers."""
    
    name: str
    layers: dict[str, Layer]
    
    separator: Optional[bool] = False
    
@dataclass
class LayerCombination:
    """A data class to represent a LayerCombination with various attributes. A LayerCombination references existing Layers."""
    
    name: str
    layers: list[str]
    
    separator: Optional[bool] = False

@dataclass
class LayerTheme:
    """A data class to represent a LayerTheme with various attributes. A LayerTheme is a collection of Layers, LayerGroups and LayerCombinations."""
    
    kategorie: str
    themen: dict[str, Union[Layer, LayerGroup, LayerCombination]]