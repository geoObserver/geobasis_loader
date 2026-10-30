"""Property models for catalog entries."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Properties:
    enabled: bool = True
    favorite: bool = False
    visible: bool = True
