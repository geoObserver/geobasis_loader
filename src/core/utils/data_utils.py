from typing import Optional


def get_index_of_entry_in_dict(data: dict, key: str) -> Optional[int]:
    for index, entry_key in enumerate(data):
        if entry_key == key:
            return index
    return None

def change_dict_order(data: dict, id: str, new_position: int) -> dict:
    entry_index = get_index_of_entry_in_dict(data, id)
    if entry_index is not None:
        entry = data.pop(id)
        entries_list = list(data.items())
        entries_list.insert(new_position, (id, entry))
        data = dict(entries_list)
    return data