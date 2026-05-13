import os
import tempfile
import json
import pathlib
from typing import Union

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
