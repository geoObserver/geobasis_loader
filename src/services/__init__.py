"""Service package.

Exports a lazy registry to access singletons without eager imports.
"""

from .registry import Registry

registry = Registry()

__all__ = ["Registry", "registry"]
