from typing import Optional
from .models import Preset


class PresetRepository:
    def __init__(self):
        self._user_presets: dict[str, Preset] = {}

    def add_user_preset(self, preset: Preset) -> None:
        self._user_presets[preset.id] = preset

    def get_user_preset(self, preset_id: str) -> Optional[Preset]:
        return self._user_presets.get(preset_id)

    def remove_user_preset(self, preset_id: str) -> None:
        self._user_presets.pop(preset_id, None)

    def get_user_presets(self) -> list[Preset]:
        return list(self._user_presets.values())
    
    def set_user_presets(self, presets: dict[str, Preset]) -> None:
        self._user_presets.clear()
        self._user_presets.update(presets)