from typing import Optional
from qgis.PyQt import uic, QtWidgets, QtCore
from ...core import events
from ...models import catalog_types
from ...services import registry
from ...operations import preset_ops, topic_ops
from ..dialogs import PresetDialog
from .. import context_menus
from .. import icons
from ... import config
from ...utils import custom_logger

logger = custom_logger.get_logger(__name__)

PRESETS_TAB = uic.loadUiType(config.RESOURCES_DIR / "design_files" / "presets_tab.ui")[0]
TYPE_USER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
TREE_PATH_USER_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2

# FIXME: groups and combinations to presets
# FIXME: Select crs after creation
# FIXME: Drag and drop
# FIXME: Load as group
# FIXME: Objects instead of paths
# FIXME: Icons not sharp
# FIXME: Keep clear focus after button press
class PresetsTab(QtWidgets.QWidget, PRESETS_TAB):
    def __init__(self, parent: QtWidgets.QWidget):
        QtWidgets.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.initialized = False
        self._collapsed_items: set[QtWidgets.QTreeWidgetItem] = set()
        self._expanded_items: set[QtWidgets.QTreeWidgetItem] = set()
        self._selected_item: Optional[QtWidgets.QTreeWidgetItem] = None
        
        # Type hints for UI elements
        self.new_preset_button: QtWidgets.QPushButton = self.new_preset_button
        self.delete_preset_button: QtWidgets.QPushButton = self.delete_preset_button
        self.new_bookmark_button: QtWidgets.QPushButton = self.new_bookmark_button
        self.apply_bookmark_button: QtWidgets.QPushButton = self.apply_bookmark_button
        self.delete_bookmark_button: QtWidgets.QPushButton = self.delete_bookmark_button
        self.presets_tree_widget: QtWidgets.QTreeWidget = self.presets_tree_widget
        self.preset_count: QtWidgets.QLabel = self.preset_count
        self.entry_count: QtWidgets.QLabel = self.entry_count
        self.missing_entries_count: QtWidgets.QLabel = self.missing_entries_count
        self.missing_entries_widget: QtWidgets.QWidget = self.missing_entries_widget
        
        # Set icons for buttons
        self.new_preset_button.setIcon(icons.get_icon(icons.IconKey.ADD_PLUS))
        self.delete_preset_button.setIcon(icons.get_icon(icons.IconKey.REMOVE_MINUS))
        self.new_bookmark_button.setIcon(icons.get_icon(icons.IconKey.SPATIAL_BOOKMARK_NEW))
        self.apply_bookmark_button.setIcon(icons.get_icon(icons.IconKey.SPATIAL_BOOKMARK_ZOOM))
        self.delete_bookmark_button.setIcon(icons.get_icon(icons.IconKey.DELETE))

        # Tree widget default settings
        self.presets_tree_widget.setTreePosition(0)
        tree_header = self.presets_tree_widget.header()
        if tree_header:
            tree_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
            tree_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            tree_header.moveSection(tree_header.visualIndex(1), 0)

        # Connect slots
        self.new_preset_button.clicked.connect(self._on_new_preset)
        self.delete_preset_button.clicked.connect(self._on_delete_preset)
        self.new_bookmark_button.clicked.connect(self._on_create_spatial_bookmark)
        self.apply_bookmark_button.clicked.connect(self._on_apply_spatial_bookmark)
        self.delete_bookmark_button.clicked.connect(self._on_delete_spatial_bookmark)
        
        self.presets_tree_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.presets_tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.presets_tree_widget.itemClicked.connect(self._on_item_clicked)
        self.presets_tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.presets_tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        self.presets_tree_widget.customContextMenuRequested.connect(self._on_presets_tree_context_menu)
        
        events.connect_presets_updated(self.build_presets_tree)
        
        # Settings/Defaults
        self.missing_entries_widget.setVisible(False)
    
    def build_presets_tree(self) -> None:
        def _add_entry(data: catalog_types.BasicEntry, parent: QtWidgets.QTreeWidgetItem) -> QtWidgets.QTreeWidgetItem:            
            item = QtWidgets.QTreeWidgetItem(parent)
            icon = icons.get_icon_from_entry(data)
            item.setIcon(0, icon)
            item.setText(0, data.name)
            # FIXME: Method in BasicEntry to get description
            if isinstance(data, catalog_types.TopicGroup):
                item.setToolTip(0, f"{data.name} [Gruppe, {len(data.get_subtopics())} Themen]")
            elif isinstance(data, catalog_types.TopicCombination):
                item.setToolTip(0, f"{data.name} [Kombination, {len(data.topic_paths)} Themen]")
            else:
                item.setToolTip(0, data.name)
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, data.path)
            item.setData(0, TYPE_USER_ROLE, "entry")
            
            return item

        currently_selected_tree_node_path = self._get_tree_node_path(self._selected_item)
        new_selected_item = None
        self.presets_tree_widget.clear()
        entry_count = 0
        missing = 0
        
        presets = registry.preset_manager.get_user_presets()
        for preset in presets:
            preset_item = QtWidgets.QTreeWidgetItem(self.presets_tree_widget)
            preset_item.setIcon(0, icons.get_icon(icons.IconKey.PRESET_USER))
            preset_item.setText(0, preset.title)
            preset_item.setToolTip(0, preset.complete_description())
            preset_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, preset.id)
            preset_item.setData(0, TYPE_USER_ROLE, "preset")
            preset_item.setData(0, TREE_PATH_USER_ROLE, preset.id)
            if preset.spatial_bookmark_id:
                preset_item.setIcon(1, icons.get_icon(icons.IconKey.SPATIAL_BOOKMARK))
            preset_item.setExpanded(preset.id not in self._collapsed_items)
            path = preset_item.data(0, TREE_PATH_USER_ROLE)
            if currently_selected_tree_node_path == path:
                new_selected_item = preset_item
            
            groups = 0
            combinations = 0
            layers = 0
            
            for entry in preset.entries:
                topic = registry.catalog_manager.get_topic_by_path(entry["path"])
                if not topic:
                    logger.warning(f"Preset entry not found: {entry['path']}")
                    missing += 1
                    continue
                
                entry_count += 1
                topic_item = _add_entry(topic, preset_item)
                init_icon = icons.get_icon(icons.IconKey.BULB_ON_ICON) if entry.get("visible", True) else icons.get_icon(icons.IconKey.BULB_OFF_ICON)
                topic_item.setIcon(1, init_icon)
                
                text = topic_item.text(0)
                crs = entry.get("crs")
                text += f" [{crs}]" if crs else ""
                if isinstance(topic, catalog_types.TopicGroup):
                    group_layer_count = len(topic.get_subtopics())
                    layers += group_layer_count
                    groups += 1
                    text += f" [Gruppe, {group_layer_count} Ebenen]"
                elif isinstance(topic, catalog_types.TopicCombination):
                    combination_layer_count = len(topic.topic_paths)
                    layers += combination_layer_count
                    combinations += 1
                    text += f" [Kombination, {combination_layer_count} Ebenen]"
                else:
                    layers += 1
                topic_item.setText(0, text)
                path += "/" + topic.path
                topic_item.setData(0, TREE_PATH_USER_ROLE, path)
                if currently_selected_tree_node_path == path:
                    new_selected_item = topic_item
                
                if not isinstance(topic, catalog_types.TopicGroup):
                    continue
                
                topic_item.setExpanded(path in self._expanded_items)
                # Reversed so that the list is in the same order as the layers after loading the preset
                for subtopic in reversed(topic.get_subtopics()):
                    subtopic_item = _add_entry(subtopic, topic_item)
                    icon = icons.get_icon(icons.IconKey.BULB_ON_ICON) if entry.get("subtopic_visible", {}).get(subtopic.path, True) else icons.get_icon(icons.IconKey.BULB_OFF_ICON)
                    subtopic_item.setIcon(1, icon)
                    path += "/" + subtopic.path
                    subtopic_item.setData(0, TREE_PATH_USER_ROLE, path)
                    if currently_selected_tree_node_path == path:
                        new_selected_item = subtopic_item
            
            addendum = ""
            addendum += f"{groups} Gruppen, " if groups else ""
            addendum += f"{combinations} Kombinationen, " if combinations else ""
            addendum += f"{layers} Ebenen" if layers else ""
            if addendum:
                preset_item.setText(0, preset_item.text(0) + f" [{addendum}]")
        
        root_item = self.presets_tree_widget.invisibleRootItem()
        if root_item:
            root_item.sortChildren(0, QtCore.Qt.SortOrder.AscendingOrder)
        if new_selected_item:
            self.presets_tree_widget.setCurrentItem(new_selected_item)
        self.preset_count.setText(str(len(presets)))
        self.entry_count.setText(str(entry_count))
        self.missing_entries_count.setText(str(missing))
        self.missing_entries_widget.setVisible(missing > 0)
        self.initialized = missing == 0
    
    def _get_tree_node_path(self, item: Optional[QtWidgets.QTreeWidgetItem]) -> str:
        return item.data(0, TREE_PATH_USER_ROLE) if item else ""
    
    def _on_item_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if column == 0:
            return
        
        item_type = item.data(0, TYPE_USER_ROLE)
        if not item_type or item_type != "entry":
            return
        
        topic_path = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not topic_path or not isinstance(topic_path, str):
            logger.warning(f"Unexpected data type for the clicked item: {type(topic_path)}")
            return
        
        parent_item = item.parent()
        if not parent_item:
            return
        
        if parent_item.data(0, TYPE_USER_ROLE) != "preset":
            preset_item = parent_item.parent()
            subtopic_path = topic_path
            topic_path = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        else:
            preset_item = parent_item
            subtopic_path = ""
            
        if not preset_item:
            logger.warning("Clicked item has no parent preset item.")
            return
        
        preset_id = preset_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not preset_id or not isinstance(preset_id, str):
            logger.warning(f"Unexpected data type for the parent preset item: {type(preset_id)}")
            return
        
        preset = registry.preset_manager.user_presets.get(preset_id)
        if not preset:
            logger.warning(f"Preset with ID '{preset_id}' not found.")
            return
        
        entry = preset.get_entry(topic_path)
        if not entry:
            logger.warning(f"Entry with path '{topic_path}' not found in preset '{preset.title}'.")
            return
        
        if parent_item.data(0, TYPE_USER_ROLE) != "preset":            
            entry = preset.get_entry(topic_path)
            if not entry:
                logger.warning(f"Entry with path '{topic_path}' not found in preset '{preset.title}'.")
                return
            
            visibility = entry.get("subtopic_visible", {})
            new_state = not visibility.get(subtopic_path, True)
            preset_ops.change_subtopic_visibility_in_preset(preset, topic_path, subtopic_path, new_state)
        else: 
            new_state = not entry.get("visible", True)
            preset_ops.change_entry_visibility_in_preset(preset, topic_path, new_state)
    
    def _on_item_double_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if column != 0:
            return
        
        item_type = item.data(0, TYPE_USER_ROLE)
        path = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if path is None:
            return
        
        if not isinstance(path, str):
            logger.warning(f"Unexpected data type for the double-clicked item: {type(path)}")
            return
        
        if item_type == "preset":
            preset_ops.add_preset_to_project(path)
        else:
            # Since subtopics dont have a bulb
            parent_item = item.parent()
            if not parent_item:
                return
            
            if parent_item.data(0, TYPE_USER_ROLE) != "preset":
                preset_item = parent_item.parent()
                subtopic_path = path
                path = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if not preset_item:
                    return
            else:
                preset_item = parent_item
                subtopic_path = ""
            
            preset_id = preset_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            preset = registry.preset_manager.user_presets.get(preset_id)
            if not preset:
                return
            
            if parent_item.data(0, TYPE_USER_ROLE) != "preset":
                preset_ops.load_subtopic_from_preset(preset, path, subtopic_path)
            else:
                preset_ops.load_entry_from_preset(preset, path)
    
    def _on_selection_changed(self) -> None:
        selected_items = self.presets_tree_widget.selectedItems()
        
        self._selected_item = None
        self.delete_preset_button.setEnabled(False)
        self.delete_bookmark_button.setEnabled(False)
        self.apply_bookmark_button.setEnabled(False)
        self.new_bookmark_button.setEnabled(False)
        if not selected_items:
            return
        
        self.delete_preset_button.setEnabled(True)
        selected_item = selected_items[0]
        self._selected_item = selected_item
        item_type = selected_item.data(0, TYPE_USER_ROLE)
        if item_type == "preset":
            self.new_bookmark_button.setEnabled(True)
            preset = registry.preset_manager.user_presets.get(selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole))
            if preset and preset.spatial_bookmark_id:
                self.apply_bookmark_button.setEnabled(True)
                self.delete_bookmark_button.setEnabled(True)
    
    def _on_presets_tree_context_menu(self, position: QtCore.QPoint) -> None:
        item = self.presets_tree_widget.itemAt(position)
        if item is None:
            return
        
        item_type = item.data(0, TYPE_USER_ROLE)
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if data is None:
            return
        if item_type == "preset":
            menu = context_menus.PresetContextMenu(data, self)
        else:
            parent_item = item.parent()
            if not parent_item:
                return
            
            if parent_item.data(0, TYPE_USER_ROLE) != "preset":
                preset_item = parent_item.parent()
                subtopic_path = data
                data = parent_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if not preset_item:
                    return
            else:
                preset_item = parent_item
                subtopic_path = ""
            
            preset_id = preset_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if parent_item.data(0, TYPE_USER_ROLE) != "preset":
                menu = context_menus.PresetEntrySubtopicContextMenu(preset_id, data, subtopic_path, self)
            else:
                menu = context_menus.PresetEntryContextMenu(preset_id, data, self)
        viewport = self.presets_tree_widget.viewport()
        if not viewport:
            logger.warning("Viewport not found for the presets tree widget.")
            return
        
        menu.exec(viewport.mapToGlobal(position))
                 
    # FIXME: Method twice implemented. use dedicated method
    def _on_new_preset(self) -> None:
        preset_dialog = PresetDialog()
        if preset_dialog.exec() != PresetDialog.DialogCode.Accepted:
            return
        
        title = preset_dialog.preset_title
        description = preset_dialog.preset_description
        save_layer_crs = preset_dialog.save_layer_crs
        if preset_dialog.mode == 1:  # from project
            registry.preset_manager.create_user_preset_from_project(title, description, save_layer_crs)
        else:
            registry.preset_manager.create_empty_user_preset(title, description)
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()
    
    def _on_delete_preset(self) -> None:
        if not self._selected_item:
            logger.warning("Kein Preset im Explorer ausgewählt. Preset kann nicht gelöscht werden.")
            return
        
        item_type = self._selected_item.data(0, TYPE_USER_ROLE)
        if item_type == "preset":
            preset_id = self._selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            preset_ops.delete_user_preset(preset_id, self)
        else:
            preset_item = self._selected_item.parent()
            if preset_item and preset_item.data(0, TYPE_USER_ROLE) == "preset":
                preset_id = preset_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                preset = registry.preset_manager.user_presets.get(preset_id)
                if preset:
                    topic_path = self._selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
                    preset.remove_entry(topic_path)
                    registry.preset_manager.save_user_presets()
                    events.emit_presets_updated()
                else:
                    logger.error(f"Preset mit ID '{preset_id}' nicht gefunden. Preset-Eintrag kann nicht entfernt werden.")
    
    def _on_create_spatial_bookmark(self) -> None:
        if not self._selected_item:
            logger.warning("Kein Preset im Explorer ausgewählt. Räumliches Lesezeichen kann nicht erstellt werden.")
            return
        
        preset_id = self._selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        preset_ops.create_spatial_bookmark_from_preset(preset_id)
    
    def _on_apply_spatial_bookmark(self) -> None:
        if not self._selected_item:
            logger.warning("Kein Preset im Explorer ausgewählt. Räumliches Lesezeichen kann nicht angewendet werden.")
            return
        
        preset_id = self._selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        preset_ops.apply_spatial_bookmark_from_preset(preset_id)
    
    def _on_delete_spatial_bookmark(self) -> None:
        if not self._selected_item:
            logger.warning("Kein Preset im Explorer ausgewählt. Räumliches Lesezeichen kann nicht gelöscht werden.")
            return
        
        preset_id = self._selected_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        preset_ops.remove_spatial_bookmark_from_preset(preset_id)

    def _on_item_expanded(self, item: QtWidgets.QTreeWidgetItem) -> None:
        self._collapsed_items.discard(item.data(0, TREE_PATH_USER_ROLE))
        self._expanded_items.add(item.data(0, TREE_PATH_USER_ROLE))
        if item.data(0, TYPE_USER_ROLE) == "entry":
            # Only groups can expand -> not extra check necessary
            item.setIcon(0, icons.get_icon(icons.IconKey.FOLDER_OPEN))
    
    def _on_item_collapsed(self, item: QtWidgets.QTreeWidgetItem) -> None:
        self._collapsed_items.add(item.data(0, TREE_PATH_USER_ROLE))
        self._expanded_items.discard(item.data(0, TREE_PATH_USER_ROLE))
        if item.data(0, TYPE_USER_ROLE) == "entry":
            # Only groups can expand -> not extra check necessary
            item.setIcon(0, icons.get_icon(icons.IconKey.FOLDER_CLOSED))