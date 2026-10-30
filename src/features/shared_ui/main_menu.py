from typing import Optional
import weakref
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtGui import QIcon
from ..catalog import models as catalog_types
from ..catalog.topic.topic_app import TopicLoader
from ..catalog.ui import CatalogTreeViewModel, EntryNode, TopicMenu
from ..property.ui import FavoritesMenu, FavoriteViewModel
from ...core import config, settings, icons
from ...core.utils import custom_logger, signal_utils

logger = custom_logger.get_logger(__name__)

# TODO: Context menus

class MainMenu(QMenu):
    def __init__(self, topic_loader: TopicLoader, catalog_model: CatalogTreeViewModel, favorite_view_model: FavoriteViewModel, parent=None):
        super().__init__(config.PLUGIN_NAME_AND_VERSION, parent)
        # This is enough since the model needs to know about every topic and its properties
        # Using a different catalog manager could lead to sync problems
        # If something is wrong with the model this also menas the ui is not working properly
        self.catalog_manager = catalog_model.catalog_manager
        self.catalog_view_model = catalog_model
        self.topic_loader = topic_loader
        self._action_dict: weakref.WeakValueDictionary[str, QAction] = weakref.WeakValueDictionary()
        
        icon = QIcon(str(config.PLUGIN_DIR / "GeoBasis_Loader_icon.png"))
        self.setIcon(icon)
        self.setObjectName(f"{config.PLUGIN_NAME}_main-menu")
        self._plugin_settings = settings.PluginSettings()
        self._dynamic_menus: weakref.WeakValueDictionary[str, QMenu] = weakref.WeakValueDictionary()
        
        # Buttons
        self.automatic_crs_action: Optional[QAction] = None
        
        # Favorites menu
        self._favorites_menu = FavoritesMenu(favorite_view_model, self)
        self._favorites_menu.set_triggered_action_func(self._on_topic_action_triggered)
        
        # Presets menu
        # self.presets_menu = PresetsMenu(self)
        
        self.catalog_view_model.tree_rebuilt.connect(self.create_menu)
        self.catalog_view_model.node_visibility_updated.connect(self._on_node_visibility_updated)
        # self.catalog_model.node_enabled_updated.connect(self._on_node_enabled_updated)
        self.catalog_view_model.node_favorite_updated.connect(self._on_node_favorite_updated)
        # events.connect_presets_updated(self.build_presets)
        self.catalog_view_model.indices_rebuilt.connect(self.create_menu)
        self._plugin_settings.automatic_crs_changed.connect(self._sync_automatic_crs)
    
    def clear_menu(self):
        self.clear()
        for menu in self._dynamic_menus.values():
            if "region-menu" in menu.objectName():
                menu.setParent(None)
            menu.deleteLater()
        self._dynamic_menus.clear()
    
    def dispose(self):
        signal_utils.disconnect_signal(self.catalog_view_model.tree_rebuilt, self.create_menu)
        signal_utils.disconnect_signal(self.catalog_view_model.indices_rebuilt, self.create_menu)
        signal_utils.disconnect_signal(self.catalog_view_model.node_visibility_updated, self._on_node_visibility_updated)
        # self.catalog_model.node_enabled_updated.disconnect(self._on_node_enabled_updated)
        signal_utils.disconnect_signal(self.catalog_view_model.node_favorite_updated, self._on_node_favorite_updated)


        # events.overview_updated.disconnect(self.create_menu)
        # events.presets_updated.disconnect(self.build_presets)
        signal_utils.disconnect_signal(self._plugin_settings.automatic_crs_changed, self._sync_automatic_crs)

        self.clear_menu()
        self._favorites_menu.dispose()
        self.setParent(None)
        self.deleteLater()
    
    def _create_entry_action(self, node: EntryNode, parent_menu: QMenu) -> QAction:
        title = node.title if not node.is_favorite else config.STAR_PREFIX + node.title
        action = QAction(node.get_icon(), title, parent_menu)
        action.setObjectName(f"main-menu-action_{node.id}")
        action.setToolTip(node.tooltip)
        action.setData(node.entry)
        action.setVisible(node.is_visible)
        action.triggered.connect(self._on_topic_action_triggered)
        self._action_dict[node.id] = action
        return action
    
    def create_menu(self):
        self.clear_menu()
        current_catalog = self.catalog_manager.get_current_catalog()
        if current_catalog is None:
            logger.info("Bitte wählen Sie einen Katalog aus.")
        else:
            # ------- Name des Katalogs einfügen -----------------
            self.addAction(current_catalog.title)
            self.addSeparator()
            
        # TODO: Entries are now absolute so favorites and presets should always be built
        # ------- Favoriten einfügen -------------------------
        # self.favorites_menu.build()
        # self.addMenu(self.favorites_menu)
        
        # ------- Presets einfügen ---------------------------
        # self.presets_menu.build()
        # self.addMenu(self.presets_menu)
        
        # self.addSeparator()
            
            # ------ Alle Dienste anzeigen -----------------------
            for node in self.catalog_view_model.root_nodes:
                # if not node.is_visible:
                #     continue
                
                region_menu = self._build_region_menu(node)
                self._dynamic_menus[node.id] = region_menu
                self.addMenu(region_menu)
                
                if node.separator:
                    self.addSeparator()
                
            self.addSeparator()
        
        # ------ Kataloge ------------------------------------
        if not self.catalog_view_model.index_nodes:
            logger.warning("Keine Katalogübersicht verfügbar, Katalogmenü kann nicht erstellt werden.")
        else:
            self._build_catalog_section()
            self.addSeparator()
        
        self._build_end_section()
    
    def build_favorites(self, catalog: Optional[catalog_types.Catalog] = None):
        # FIXME: Not enough since the star prefix needs to be updated as well
        # self.favorites_menu.build(catalog)
        self.create_menu()
    
    def build_presets(self):     
        pass   
        # self.presets_menu.build()
    
    def _build_region_menu(self, node: EntryNode) -> "TopicMenu":
        menu = TopicMenu(node.title, 'region-menu-' + node.id, self)
        menu.setVisible(node.is_visible)
        
        for node_child in node:
            # if not node_child.is_visible:
            #     continue
            
            if len(node_child.child_nodes) > 0:
                topic_group_menu = TopicMenu(node.title, 'topic-group-menu-' + node.id, menu)
                topic_group_menu.setIcon(icons.get_icon(icons.IconKey.FOLDER_CLOSED))
                self._dynamic_menus[node_child.id] = topic_group_menu
                
                # Virtual action to add all topics in the group to the map
                if topic_group_node := node_child.additional_node:
                    all_topics_action = self._create_entry_action(topic_group_node, topic_group_menu)
                    all_topics_action.setText("Alle Laden")
                    # Remove the virtual action from the action dict so changing favorite state doesnt add a star
                    self._action_dict.pop(topic_group_node.id, None)  
                    topic_group_menu.addAction(all_topics_action)
                    topic_group_menu.addSeparator()
                
                for sub_node in node_child:
                    # if not sub_node.is_visible:
                    #     continue
                    
                    action = self._create_entry_action(sub_node, topic_group_menu)
                    topic_group_menu.addAction(action)
            else:
                action = self._create_entry_action(node_child, menu)
                menu.addAction(action)
            
            if node_child.separator:
                menu.addSeparator()
        return menu

    def _build_catalog_section(self):
        if not self.catalog_view_model.index_nodes:
            logger.warning("No catalog overview available. Cannot build catalog menu.")
            return
        
        catalogs_menu = self.addMenu("Katalog wechseln (Change Catalogs)")
        if not catalogs_menu:
            logger.error("Menü 'Katalog wechseln' nicht vorhanden")
            return
        
        catalogs_menu.setObjectName('catalog-overview')
        
        # ------- Einträge im Katalogmenü erstellen ------------------------
        # FIXME: Only one index at the time (official oone) -> Iterating indices unnecessary
        official_index = self.catalog_view_model.index_nodes[0]
        for catalog_node in official_index:
            catalog_action = catalogs_menu.addAction(catalog_node.title, self._on_catalog_action_triggered)
            if not catalog_action:
                logger.warning(f"Eintrag für Katalog '{catalog_node.title}' nicht erstellbar")
                continue
            
            catalog_action.setObjectName("catalog-" + catalog_node.id)
            catalog_action.setData(catalog_node.id)
        
        self.addAction("Kataloge neu laden (Reload Catalogs)", self.catalog_manager.fetch_data)
        
    def _build_end_section(self):
        self.addSeparator()
        
        automatic_crs = self._plugin_settings.automatic_crs
        self.automatic_crs_action = QAction(text="Wenn möglich, Dienste autom. im KBS laden", parent=self, checkable=True, checked=automatic_crs) # type: ignore
        self.automatic_crs_action.triggered.connect(self._set_automatic_crs)
        self.addAction(self.automatic_crs_action)
        
        # settings_icon = icons.get_icon(icons.IconKey.SETTINGS)
        # self.addAction(settings_icon, "Einstellungen (Aktueller Katalog)", open_settings)
        self.addSeparator()
        
        # ------- Spenden-Schaltfläche für #geoObserver ------------------------
        self.addAction("GeoBasis_Loader per Spende unterstützen ...", lambda: self.topic_loader.open_web_site('https://geoobserver.de/support_geobasis_loader/'))
        
        # ------- Andere #geoObserver Plugins Webseite -------------------------
        self.addAction("#geoObserver-Tools", lambda: self.topic_loader.open_web_site('https://geoobserver.de/qgis-plugins/'))
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        self.addAction("Über ...", lambda: self.topic_loader.open_web_site('https://geoobserver.de/qgis-plugin-geobasis-loader/'))
    
    def _on_catalog_action_triggered(self) -> None:
        sender = self.sender()
        if isinstance(sender, QAction):
            catalog_id: str = sender.data()
            if isinstance(catalog_id, str):
                self.catalog_manager.set_current_catalog(catalog_id)
            else:
                logger.warning(f"Ungültige Daten im QAction-Objekt: {catalog_id}")
    
    def _on_topic_action_triggered(self) -> None:
        sender = self.sender()
        if isinstance(sender, QAction):
            entry: catalog_types.TopicEntry = sender.data()
            if isinstance(entry, catalog_types.TopicEntry):
                if isinstance(entry, catalog_types.Topic) and entry.is_web():
                    self.topic_loader.open_web_site(entry.uri)
                else:
                    self.topic_loader.add_topic(entry)
            else:
                logger.warning(f"Ungültige Daten im QAction-Objekt: {sender.objectName()}")
    
    def _on_node_visibility_updated(self, visibility_dict: dict):
        # TODO: Test this functionality
        for node_id, is_visible in visibility_dict.items():
            action = self._action_dict.get(node_id)
            menu = self._dynamic_menus.get(node_id)
            if action:
                action.setVisible(is_visible)
            if menu:
                menu.setVisible(is_visible)
    
    def _on_node_favorite_updated(self, favorite_dict: dict):
        def update_title(current_title: str, is_favorite: bool):
            if is_favorite and not current_title.startswith(config.STAR_PREFIX):
                return config.STAR_PREFIX + current_title
            elif not is_favorite and current_title.startswith(config.STAR_PREFIX):
                return current_title[len(config.STAR_PREFIX):]
            return current_title
        
        for node_id, is_favorite in favorite_dict.items():
            action = self._action_dict.get(node_id)
            menu = self._dynamic_menus.get(node_id)
            
            if action:
                title = action.text()
                new_title = update_title(title, is_favorite)
                action.setText(new_title)
            
            if menu:
                title = menu.title()
                new_title = update_title(title, is_favorite)
                menu.setTitle(new_title)
    
    def _set_automatic_crs(self, enabled: bool):
        self._plugin_settings.automatic_crs = enabled
    
    def _sync_automatic_crs(self):
        if self.automatic_crs_action is None:
            logger.warning("Automatic CRS action not initialized. Cannot sync state.")
            return
        
        automatic_crs = self._plugin_settings.automatic_crs
        self.automatic_crs_action.setChecked(automatic_crs)

