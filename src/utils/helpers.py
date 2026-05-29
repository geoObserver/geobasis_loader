import os
import tempfile
import json
import pathlib
from typing import Union
from qgis.core import QgsBookmark, QgsCsException, QgsProject, QgsReferencedRectangle
from qgis.gui import QgsMapCanvas
from qgis.utils import iface

def write_json(data: Union[dict, list], file_path: pathlib.Path) -> None:
    """Writes a dictionary to a JSON file atomically. 
    It creates a temporary file in the same directory as the target file, writes the data to it, and then replaces the target file with the temporary file. 
    This ensures that the target file is not left in a corrupted state if an error occurs during writing.

    Args:
        data (dict): The data to be written to the JSON file. Note that the data must be serializable to JSON (preferably a dict or list).
        file_path (pathlib.Path): The path to the JSON file to be written.

    Raises:
        TypeError: If the data is not a dictionary or list, or if the file path is not a pathlib.Path object. Also raised if the data cannot be serialized to JSON.
        OSError: If there is an error creating or writing to the temporary file, or replacing the target file.
    """
    
    if not isinstance(data, (dict, list)):
        raise TypeError("Data must be a dictionary or list")
    
    if not isinstance(file_path, pathlib.Path):
        raise TypeError("file path must be a pathlib.Path object")
    
    file_path = file_path.resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(
            prefix=file_path.name,
            suffix=".tmp",
            dir=file_path.parent,
        )
    except OSError as e:
        raise OSError(f"Failed to create temporary file ({type(e).__name__}): {e}")
    
    try:
        with open(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, file_path)
    except OSError as e:
        raise OSError(f"Failed to write to temporary file ({type(e).__name__}): {e}")
    except TypeError as e:
        raise TypeError(f"Failed to serialize data to JSON: {e}")
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

def read_json(file_path: pathlib.Path) -> Union[dict, list]:
    """Reads a JSON file and returns its contents as a dictionary or list.

    Args:
        file_path (pathlib.Path): The path to the JSON file to be read.

    Raises:
        FileNotFoundError: If the file is not found.
        json.JSONDecodeError: If the file contains invalid JSON.
        PermissionError: If there is a permission error while reading the file.
        OSError: If there is an error reading the file.

    Returns:
        Union[dict, list]: The contents of the JSON file as a dictionary or list.
    """
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            services = json.load(file)
        return services
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Fehler beim Dekodieren der JSON-Datei {file_path}: {e.msg}", e.doc, e.pos)
    except PermissionError as e:
        raise PermissionError(f"Keine Berechtigung zum Lesen der Datei {file_path}: {e}")
    except OSError as e:
        raise OSError(f"Fehler beim Lesen der Datei {file_path} ({type(e).__name__}): {e}")

def apply_spatial_bookmark(bookmark: QgsBookmark) -> None:
    """Applies a spatial bookmark to the current QGIS project.

    Args:
        bookmark (QgsBookmark): The spatial bookmark to be applied.

    Raises:
        TypeError: If the provided bookmark is not an instance of QgsBookmark.
        ValueError: If the bookmark does not contain valid spatial information.
        RuntimeError: If the QGIS interface or map canvas is not available, or if there is an error applying the bookmark.
    """
    
    if not isinstance(bookmark, QgsBookmark):
        raise TypeError("Provided bookmark must be an instance of QgsBookmark")
    
    extent = bookmark.extent()
    if extent.isNull():
        raise ValueError("Provided bookmark extent is null or invalid")
    
    if iface is None or not hasattr(iface, 'mapCanvas'):
        raise RuntimeError("QGIS interface is not available or does not have a map canvas")
    
    canvas: QgsMapCanvas = iface.mapCanvas() # type: ignore
    if canvas is None:
        raise RuntimeError("QGIS map canvas is not available")
    
    try:
        canvas.setReferencedExtent(extent)
    except QgsCsException as e:
        raise RuntimeError(f"Failed to apply spatial bookmark due to transformation error: {e}")
    
    canvas.setRotation(bookmark.rotation())
    canvas.refresh()

def create_spatial_bookmark() -> QgsBookmark:
    
    
    if iface is None or not hasattr(iface, 'mapCanvas'):
        raise RuntimeError("QGIS interface is not available or does not have a map canvas")
    
    canvas: QgsMapCanvas = iface.mapCanvas() # type: ignore
    if canvas is None:
        raise RuntimeError("QGIS map canvas is not available")
    
    project = QgsProject.instance()
    if project is None:
        raise RuntimeError("QGIS project instance is not available")
    
    
    extent = canvas.extent()
    crs = project.crs()
    rotation = canvas.rotation()
    
    referenced_extent = QgsReferencedRectangle(extent, crs)
    bookmark = QgsBookmark()
    bookmark.setExtent(referenced_extent)
    bookmark.setRotation(rotation)
    
    return bookmark
