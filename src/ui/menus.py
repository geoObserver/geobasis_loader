import re
from typing import Optional, Union
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.core import QgsSettings
from qgis.utils import iface
from . import icons
from ..core import events
from .dialogs import SettingsDialog, PresetDialog
from .context_menus import PresetContextMenu, FavoritesContextMenu, TopicContextMenu
from ..services import registry
from ..models import catalog_types
from ..operations import topic_ops as handlers
from .. import config
from ..utils import custom_logger

STAR_PREFIX = "\u2605 "  # ★

logger = custom_logger.get_logger(__name__)

class MainMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(config.PLUGIN_NAME_AND_VERSION, parent)
        self.setObjectName("main-menu")
        icon = QIcon(str(config.PLUGIN_DIR / "GeoBasis_Loader_icon.png"))
        self.setIcon(icon)
        self._qgs_settings = QgsSettings()
        
        # Favorites menu
        self.favorites_menu = FavoritesMenu(self)
        
        # Presets menu
        self.presets_menu = PresetsMenu(self)
        
        events.connect_presets_updated(self.build_presets)
        events.connect_favorites_updated(self.build_favorites)
        events.connect_visibility_updated(self.create_menu)
        events.connect_enabled_updated(self.create_menu)
        events.connect_current_catalog_updated(self.create_menu)
        events.connect_overview_updated(self.create_menu)
    
    def create_menu(self):
        self.clear()
        current_catalog: Optional[catalog_types.Catalog] = registry.catalog_manager.get_current_catalog()
        if not isinstance(current_catalog, catalog_types.Catalog):
            logger.warning("No catalog provided and no current catalog found. Cannot build catalog menu.")
        else:
            # ------- Name des Katalogs einfügen -----------------
            self.addAction(self._qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)["titel"])
            self.addSeparator()
            
            # ------- Favoriten einfügen -------------------------
            self.favorites_menu.build(current_catalog)
            self.addMenu(self.favorites_menu)
            
            # ------- Presets einfügen ---------------------------
            self.presets_menu.build()
            self.addMenu(self.presets_menu)
            
            self.addSeparator()
            
            # ------ Alle Dienste anzeigen -----------------------
            for region in current_catalog.get_regions():
                if not region.properties.visible:
                    continue
                
                region_menu = self._build_region_menu(region)
                self.addMenu(region_menu)
                
                if region.separator:
                    self.addSeparator()
            
            self.addSeparator()
            
            # ------ Kataloge ------------------------------------
            if registry.catalog_manager.overview is not None:
                self._build_catalog_section()
                self.addSeparator()
        
        self._build_end_section()
    
    def build_favorites(self, catalog: Optional[catalog_types.Catalog] = None):
        # FIXME: Not enough since the star prefix needs to be updated as well
        # self.favorites_menu.build(catalog)
        self.create_menu()
    
    def build_presets(self):        
        self.presets_menu.build()
    
    def _build_region_menu(self, region: catalog_types.Region) -> "TopicMenu":
        def _create_action(name: str, path: str, icon: QIcon, parent: QMenu,  tip: str = "Thema hinzufügen", slot = handlers.add_topic) -> QAction:            
            action = QAction(icon, name, parent)
            action.setObjectName(name)
            action.setStatusTip(tip)
            action.setToolTip(tip)
            action.setData(path)
            action.triggered.connect(lambda _: slot(path))
            return action
        
        menu = TopicMenu(region.name, 'region-' + region.name, self)
        
        topics = region.get_topics()        
        for topic in topics:
            if not topic.properties.visible:
                continue
            
            topic_name = topic.name
            if topic.properties.favorite:
                topic_name = STAR_PREFIX + topic_name
            
            if isinstance(topic, catalog_types.Topic) and topic.topic_type == catalog_types.TopicType.WEB:
                icon = icons.get_icon(topic.topic_type)
                action = _create_action(topic_name, topic.uri, icon, menu, "Informationen öffnen", handlers.open_web_site)
                menu.addAction(action)
                continue
            
            if isinstance(topic, catalog_types.TopicGroup):
                topic_group_menu = TopicMenu(topic_name, 'topic-group-' + topic.name, menu)
                topic_group_menu.setIcon(icons.get_icon(icons.IconKey.FOLDER_CLOSED))                
                
                icon = icons.get_icon(icons.IconKey.GROUP_ADD)
                add_all_action = _create_action("Alle laden", topic.path, icon, topic_group_menu, "Alle Themen der Gruppe laden")                    
                topic_group_menu.addAction(add_all_action)
                topic_group_menu.addSeparator()

                for subtopic in topic.get_subtopics():
                    if not subtopic.properties.visible:
                        continue
                    
                    subtopic_name = subtopic.name
                    if subtopic.properties.favorite:
                        subtopic_name = STAR_PREFIX + subtopic_name

                    icon = icons.get_icon(subtopic.topic_type)
                    if subtopic.topic_type == catalog_types.TopicType.WEB:
                        subtopic_action = _create_action(subtopic_name, subtopic.uri, icon, topic_group_menu, "Informationen öffnen", handlers.open_web_site)
                    else:
                        subtopic_action = _create_action(subtopic_name, subtopic.path, icon, topic_group_menu)
                    topic_group_menu.addAction(subtopic_action)

                menu_action = menu.addMenu(topic_group_menu)
                if menu_action is not None:
                    menu_action.setStatusTip("Alle Themen der Gruppe laden")
                    menu_action.setToolTip("Alle Themen der Gruppe laden")
                    menu_action.setData(topic.path)
                    menu_action.triggered.connect(lambda _, p=topic.path: handlers.add_topic(p))
            else:
                if isinstance(topic, catalog_types.TopicCombination):
                    icon = icons.get_icon(icons.IconKey.COMBINATION_ADD)
                    action = _create_action(topic_name, topic.path, icon, menu)
                else:
                    icon = icons.get_icon(topic.topic_type)
                    action = _create_action(topic_name, topic.path, icon, menu)
                menu.addAction(action)
                
            if topic.separator:
                menu.addSeparator()
        return menu

    def _build_catalog_section(self):
        if registry.catalog_manager.overview is None:
            logger.warning("No catalog overview available. Cannot build catalog menu.")
            return
        
        catalogs_menu = self.addMenu("Katalog wechseln (Change Catalogs)")
        if not catalogs_menu:
            logger.error("Menü 'Katalog wechseln' nicht vorhanden")
            return
        
        catalogs_menu.setObjectName('catalog-overview')
        
        # ------- Einträge im Katalogmenü erstellen ------------------------
        for catalog in registry.catalog_manager.overview:
            catalog_action = catalogs_menu.addAction(catalog["titel"], lambda c=catalog: registry.catalog_manager.set_current_catalog(c))
            if not catalog_action:
                logger.warning(f"Eintrag für Katalog '{catalog['titel']}' nicht erstellbar")
                continue
            
            catalog_action.setObjectName("catalog-" + catalog["titel"])
        
        self.addAction("Kataloge neu laden (Reload Catalogs)", lambda: registry.catalog_manager.get_overview(callback=self.create_menu))
        
    def _build_end_section(self):
        self.addSeparator()
        
        qgs_settings = QgsSettings()
        automatic_crs = qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, type=bool)
        action = QAction(text="Wenn möglich, Dienste autom. im KBS laden", parent=self, checkable=True, checked=automatic_crs) # type: ignore
        action.toggled.connect(lambda checked: self._set_automatic_crs(checked))
        self.addAction(action)
        
        settings_icon = icons.get_icon(icons.IconKey.SETTINGS)
        self.addAction(settings_icon, "Einstellungen (Aktueller Katalog)", self._open_settings)
        self.addSeparator()
        
        # ------- Spenden-Schaltfläche für #geoObserver ------------------------
        self.addAction("GeoBasis_Loader per Spende unterstützen ...", lambda: handlers.open_web_site('https://geoobserver.de/support_geobasis_loader/'))
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        self.addAction("Über ...", lambda: handlers.open_web_site('https://geoobserver.de/qgis-plugin-geobasis-loader/'))
    
    # FIXME: Maybe a dedicated settings module/class would be better than local changes
    def _set_automatic_crs(self, enabled: bool):
        self._qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, enabled)
    
    def _changed_current_catalog(self, _: Optional[Union[catalog_types.Catalog, list]] = None):
        current_catalog = self._qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is None or "titel" not in current_catalog:
            logger.warning(f"Momentan ist kein valider Katalog ausgewählt, Bitten wählen Sie einen aus", extra={"show_banner": True})
            return
        
        titel = current_catalog["titel"]
        name = current_catalog["name"]
        version_matches = re.findall(r'v\d+', name)
        version = version_matches[0] if version_matches else "unbekannt"
        logger.success(f'Lese {titel}, Version {version} ...', extra={"show_banner": True})
        
        self.create_menu()
        
    def _open_settings(self):
        current_catalog = registry.catalog_manager.get_current_catalog()
        if not isinstance(current_catalog, catalog_types.Catalog):
            logger.warning("No current catalog found. Cannot open settings dialog.")
            return
        
        if iface is None or hasattr(iface, 'mainWindow') is False:
            logger.error("Kein iface verfügbar (Headless?), Einstellungen können nicht geöffnet werden")
            return
        
        settings_dialog = SettingsDialog(iface.mainWindow())
        settings_dialog.set_settings(current_catalog)
        settings_dialog.accepted.connect(self._accept_settings)
        settings_dialog.open()
    
    def _accept_settings(self):
        logger.success("Einstellungen erfolgreich gespeichert", extra={"show_banner": True})
        self.create_menu()

class CustomQMenu(QMenu):
    def __init__(self, title: str, object_name: str, parent=None):
        super().__init__(title, parent)
        self.setObjectName(object_name)
        self.setToolTipsVisible(True)
    
    def mouseReleaseEvent(self, a0):
        if a0 is None:
            return
        
        if a0.button() == Qt.MouseButton.RightButton:
            if hasattr(a0, 'globalPosition'):
                global_pos = a0.globalPosition().toPoint()
            else:
                global_pos = a0.globalPos()
            self._init_context_menu(a0.pos(), global_pos)
            return

        super().mouseReleaseEvent(a0)
    
    def build(self):
        ... # To be implemented in subclasses
    
    def _init_context_menu(self, pos, global_pos=None) -> None:
        action = self.actionAt(pos) or self.menuAction()
        if not action:
            return
        
        if global_pos is None:
            global_pos = self.mapToGlobal(pos)
        
        self._show_context_menu(action, global_pos)
        
    def _show_context_menu(self, action: QAction, global_pos) -> None:
        ... # To be implemented in subclasses

class PresetsMenu(CustomQMenu):
    def __init__(self, parent):
        super().__init__("Presets", "presets-menu", parent)
        self.setIcon(icons.get_icon(icons.IconKey.PRESET_USER))
    
    def build(self):
        self.clear()
        user_presets = registry.preset_manager.get_user_presets()
        curated_presets = registry.preset_manager.get_curated_presets()
        
        action = QAction(icons.get_icon(icons.IconKey.GROUP_ADD), "Neu vom Projekt", self)
        action.setObjectName("new-preset-from-project")
            
        action.triggered.connect(self._new_preset_from_project)
        self.addAction(action)
        self.addSeparator()
        
        for preset in user_presets:
            action = QAction(preset.title, self)
            action.setObjectName(preset.title)
            action.setData({"preset_id": preset.id, "preset_type": "user"})
            description = preset.description + "\n\n" if preset.description else ""
            description += preset.topic_description()
            action.setToolTip(description)
            action.triggered.connect(lambda _, p=preset: registry.preset_manager.add_preset_to_project(p.id))
            self.addAction(action)
        
        self.addSeparator()
        
        for preset in curated_presets:
            action = QAction(preset.title, self)
            action.setObjectName(preset.title)
            description = preset.description + "\n\n" if preset.description else ""
            description += preset.topic_description()
            action.setToolTip(description)
            action.triggered.connect(lambda _, p=preset: registry.preset_manager.add_preset_to_project(p.id))
            self.addAction(action)
    
    def _new_preset_from_project(self):
        preset_dialog = PresetDialog()
        if preset_dialog.exec() != PresetDialog.DialogCode.Accepted:
            return
        
        title = preset_dialog.preset_title
        description = preset_dialog.preset_description
        save_layer_crs = preset_dialog.save_layer_crs
        registry.preset_manager.create_user_preset_from_project(title, description, save_layer_crs)
        registry.preset_manager.save_user_presets()
        events.emit_presets_updated()
    
    def _show_context_menu(self, action: QAction, global_pos) -> None:
        data = action.data()
        if not isinstance(data, dict) or data.get("preset_type") != "user":
            return

        preset_id = data.get("preset_id")
        context_menu = PresetContextMenu(preset_id, self)
        context_menu.exec(global_pos)

class FavoritesMenu(CustomQMenu):
    def __init__(self, parent):
        super().__init__("Favoriten", "favorites-menu", parent)
        self.setIcon(icons.get_icon(icons.IconKey.FAVORITE_STAR))
    
    def build(self, catalog: Optional[catalog_types.Catalog] = None):
        self.clear()
        favorites = registry.property_manager.get_favorites()
        
        if not catalog:
            current_catalog: Optional[Union[catalog_types.Catalog, list]] = registry.catalog_manager.get_current_catalog()
            if not isinstance(current_catalog, catalog_types.Catalog):
                logger.warning("No catalog provided and no current catalog found. Cannot build favorites menu.")
                return
            catalog = current_catalog
        
        if not favorites:
            action = QAction("(Keine)", self)
            action.setObjectName("no-favorites")
            action.setEnabled(False)
            self.addAction(action)
        else:
            for key in favorites:
                topic = catalog.get_entry(key)
                if not topic:
                    continue
                
                icon = icons.get_icon_from_entry(topic)
                action = QAction(icon, topic.name, self)
                action.setData(topic.path)
                action.setObjectName(topic.name)
                action.triggered.connect(lambda _, t=topic: handlers.add_topic(t.path))
                self.addAction(action)
    
    def _show_context_menu(self, action: QAction, global_pos) -> None:
        data = action.data()
        if not isinstance(data, str):
            return
        
        context_menu = FavoritesContextMenu(data, self)
        context_menu.exec(global_pos)

class TopicMenu(CustomQMenu):
    def __init__(self, title: str, object_name: str, parent=None):
        super().__init__(title, object_name, parent)
    
    def _show_context_menu(self, action: QAction, global_pos) -> None:
        data = action.data()
        if not isinstance(data, str):
            return
        
        context_menu = TopicContextMenu(data, self)
        context_menu.exec(global_pos)
