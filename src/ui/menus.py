from typing import Optional, Union

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.core import QgsSettings
from qgis.utils import iface
from . import Icons, SettingsDialog, PresetDialog
from ..services import registry
from ..models import catalog_types
from ..operations import topic_ops as handlers
from .. import config
from ..utils import custom_logger

logger = custom_logger.get_logger(__name__)

class MainMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(config.PLUGIN_NAME_AND_VERSION, parent)
        self.setObjectName("main-menu")
        icon = QIcon(config.PLUGIN_DIR + "/GeoBasis_Loader_icon.png")
        self.setIcon(icon)
        self._qgs_settings = QgsSettings()
        
        # Favorites menu
        self.favorites_menu = QMenu("Favoriten", self)
        self.favorites_menu.setObjectName("favorites-menu")
        self.favorites_menu.setIcon(Icons.get_icon(Icons.IconKey.FAVORITE_STAR))
        self.favorites_menu.setToolTipsVisible(True)
        
        # Presets menu
        self.presets_menu = QMenu("Presets", self)
        self.presets_menu.setObjectName("presets-menu")
        self.presets_menu.setIcon(Icons.get_icon(Icons.IconKey.PRESET_USER))
        self.presets_menu.setToolTipsVisible(True)
    
    def create_menu(self):
        self.clear()
        current_catalog: Optional[Union[catalog_types.Catalog, list]] = registry.catalog_manager.get_current_catalog()
        if not isinstance(current_catalog, catalog_types.Catalog):
            logger.warning("No catalog provided and no current catalog found. Cannot build catalog menu.")
        else:
            # ------- Name des Katalogs einfügen -----------------
            self.addAction(self._qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)["titel"])
            self.addSeparator()
            
            # ------- Favoriten einfügen -------------------------
            self.build_favorites(current_catalog)
            self.addMenu(self.favorites_menu)
            
            # ------- Presets einfügen ---------------------------
            self.build_presets()
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
        self.favorites_menu.clear()
        favorites = registry.property_manager.get_favorites()
        
        if not catalog:
            current_catalog: Optional[Union[catalog_types.Catalog, list]] = registry.catalog_manager.get_current_catalog()
            if not isinstance(current_catalog, catalog_types.Catalog):
                logger.warning("No catalog provided and no current catalog found. Cannot build favorites menu.")
                return
            catalog = current_catalog
        
        if not favorites:
            action = QAction("(Keine)", self.favorites_menu)
            action.setObjectName("no-favorites")
            action.setEnabled(False)
            self.favorites_menu.addAction(action)
        else:
            for key in favorites:
                topic = catalog.get_entry(key)
                if not topic:
                    continue
                
                action = QAction(topic.name, self.favorites_menu)
                action.setObjectName(topic.name)
                action.triggered.connect(lambda t=topic: handlers.add_topic(t.path))
                self.favorites_menu.addAction(action)
    
    def build_presets(self):        
        self.presets_menu.clear()
        user_presets = registry.preset_manager.get_user_presets()
        curated_presets = registry.preset_manager.get_curated_presets()
        
        action = QAction(Icons.get_icon(Icons.IconKey.GROUP_ADD), "Neu vom Projekt", self.presets_menu)
        action.setObjectName("new-preset-from-project")
            
        action.triggered.connect(self._new_preset_from_project)
        self.presets_menu.addAction(action)
        self.presets_menu.addSeparator()
        
        for preset in user_presets:
            action = QAction(preset.title, self.presets_menu)
            action.setObjectName(preset.title)
            action.setToolTip(preset.description)
            action.triggered.connect(lambda p=preset: registry.preset_manager.add_preset_to_project(p.id))
            self.presets_menu.addAction(action)
        
        self.presets_menu.addSeparator()
        
        for preset in curated_presets:
            action = QAction(preset.title, self.presets_menu)
            action.setObjectName(preset.title)
            action.setToolTip(preset.description)
            action.triggered.connect(lambda p=preset: registry.preset_manager.add_preset_to_project(p.id))
            self.presets_menu.addAction(action)
    
    def _build_region_menu(self, region: catalog_types.Region) -> QMenu:
        def _create_action(name: str, path: str, icon: QIcon, parent: QMenu,  tip: str = "Thema hinzufügen", slot = handlers.add_topic) -> QAction:            
            action = QAction(icon, name, parent)
            action.setObjectName(name)
            action.setStatusTip(tip)
            action.setToolTip(tip)
            action.triggered.connect(lambda: slot(path))
            return action
        
        menu = QMenu(region.name, self)
        menu.setObjectName('region-' + region.name)
        menu.setToolTipsVisible(True)
        
        topics = region.get_topics()        
        for topic in topics:
            if not topic.properties.visible:
                continue
            
            if isinstance(topic, catalog_types.Topic) and topic.topic_type == catalog_types.TopicType.WEB:
                icon = Icons.get_icon(topic.topic_type)
                action = _create_action(topic.name, topic.uri, icon, menu, "Informationen öffnen", handlers.open_web_site)
                menu.addAction(action)
                continue
            
            if isinstance(topic, catalog_types.TopicGroup):
                topic_group_menu = QMenu(topic.name, menu)
                topic_group_menu.setIcon(Icons.get_icon(Icons.IconKey.FOLDER_CLOSED))
                topic_group_menu.setToolTipsVisible(True)
                
                icon = Icons.get_icon(Icons.IconKey.GROUP_ADD)
                add_all_action = _create_action("Alle laden", topic.path, icon, topic_group_menu, "Alle Themen der Gruppe laden")
                topic_group_menu.addAction(add_all_action)
                topic_group_menu.addSeparator()

                for subtopic in topic.get_subtopics():
                    if not subtopic.properties.visible:
                        continue
                    
                    icon = Icons.get_icon(subtopic.topic_type)
                    if subtopic.topic_type == catalog_types.TopicType.WEB:
                        subtopic_action = _create_action(subtopic.name, subtopic.uri, icon, topic_group_menu, "Informationen öffnen", handlers.open_web_site)
                    else:
                        subtopic_action = _create_action(subtopic.name, subtopic.path, icon, topic_group_menu)
                    topic_group_menu.addAction(subtopic_action)

                menu.addMenu(topic_group_menu)
            else:
                if isinstance(topic, catalog_types.TopicCombination):
                    icon = Icons.get_icon(Icons.IconKey.COMBINATION_ADD)
                    action = _create_action(topic.name, topic.path, icon, menu)
                else:
                    icon = Icons.get_icon(topic.topic_type)
                    action = _create_action(topic.name, topic.path, icon, menu)
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
            catalog_action = catalogs_menu.addAction(catalog["titel"], lambda c=catalog: self._change_current_catalog(c))
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
        
        self.addAction("Einstellungen (Aktueller Katalog)", self._open_settings)
        self.addSeparator()
        
        # ------- Spenden-Schaltfläche für #geoObserver ------------------------
        self.addAction("GeoBasis_Loader per Spende unterstützen ...", lambda: handlers.open_web_site('https://geoobserver.de/support_geobasis_loader/'))
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        self.addAction("Über ...", lambda: handlers.open_web_site('https://geoobserver.de/qgis-plugin-geobasis-loader/'))
    
    def _new_preset_from_project(self):
        preset_dialog = PresetDialog()
        if preset_dialog.exec() != PresetDialog.DialogCode.Accepted:
            return
        
        title = preset_dialog.preset_title
        description = preset_dialog.preset_description
        save_layer_crs = preset_dialog.save_layer_crs
        registry.preset_manager.create_user_preset_from_project(title, description, save_layer_crs)
        self.build_presets()
    
    # FIXME: Maybe a dedicated settings module/class would be better than local changes
    def _set_automatic_crs(self, enabled: bool):
        self._qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, enabled)
        
    def _change_current_catalog(self, catalog: dict):
        self._qgs_settings.setValue(config.QgsSettingsKeys.CURRENT_CATALOG, catalog)
        registry.catalog_manager.get_catalog(catalog["titel"], callback=self.create_menu)
    
    def _open_settings(self):
        current_catalog = registry.catalog_manager.get_current_catalog()
        if not isinstance(current_catalog, catalog_types.Catalog):
            logger.warning("No current catalog found. Cannot open settings dialog.")
            return
        
        settings_dialog = SettingsDialog(iface.mainWindow())
        settings_dialog.set_settings(current_catalog)
        settings_dialog.accepted.connect(self._accept_settings)
        settings_dialog.open()
    
    def _accept_settings(self):
        logger.success("Einstellungen erfolgreich gespeichert", extra={"show_banner": True})
        self.create_menu()
        