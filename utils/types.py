"""Dataclass definitions for catalog layer structures.

These types model the hierarchy of layers, groups, combinations, and themes
used in the GeoBasis Loader catalog format. They are not yet in active use
but prepared for future type annotations throughout the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Layer:
    """A single map layer with connection URI and display settings."""

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
    """A named collection of layers that are displayed together as a group."""

    name: str
    layers: dict[str, Layer]

    separator: bool | None = False

@dataclass
class LayerCombination:
    """A predefined combination that references existing layers by name."""

    name: str
    layers: list[str]

    separator: bool | None = False

@dataclass
class LayerTheme:
    """A thematic category containing layers, groups, and combinations."""

    kategorie: str
    themen: dict[str, Layer | LayerGroup | LayerCombination]
