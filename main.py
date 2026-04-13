import re
from functools import partial
from typing import Union, Optional
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtGui import QIcon, QColor, QDesktopServices
from qgis.PyQt.QtCore import QUrl, QObject
from qgis.core import QgsSettings, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer, QgsSymbolLayer, QgsWkbTypes, Qgis
from qgis.gui import QgisInterface
from .topic_search import SearchFilter
from . import config
from .utils import custom_logger
from . import ui as custom_ui
from .catalog_manager import CatalogManager
from .topic_handlers import catalog_types, PropertyManager

logger = custom_logger.get_logger(__file__)

if Qgis.versionInt() < 33000:   # Breaking change in Version 3.30 -> Geometry types now in Qgis instead of QgsWkbTypes
    geometry_types = QgsWkbTypes.Type       # type: ignore
else:
    geometry_types = Qgis.WkbType

STAR_PREFIX = "\u2605 "  # ★

class GeoBasis_Loader(QObject):
    services: Optional[catalog_types.Catalog] = None
    
    search_filter = None
    qgs_settings = QgsSettings()

# =========================================================================
    def __init__(self, iface: QgisInterface, parent=None) -> None:
        super().__init__(parent)
        self.iface = iface
        CatalogManager.setup(iface)
        CatalogManager.get_overview(callback=self.initGui)
        
        # ------- Create dialog variables, create dialogs lazily
        self._epsg_dialog: Optional[custom_ui.EpsgDialog] = None
        self._settings_dialog: Optional[custom_ui.SettingsDialog] = None

        # ------- Letzten Katalog laden --------------------------------------------
        current_catalog = self.qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is not None and "name" in current_catalog:
            CatalogManager.get_catalog(current_catalog["titel"], current_catalog["name"], self.set_services)
            
        # ------- Letzte Einstellung für automatisches Koordinatensystem laden -----
        self.automatic_crs = self.qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, type=bool)

        icon = QIcon(config.PLUGIN_DIR + "/GeoBasis_Loader_icon.png")
        self.main_menu = QMenu(config.PLUGIN_NAME_AND_VERSION)
        self.main_menu.setIcon(icon)
        plugin_menu = self.iface.pluginMenu()
        if plugin_menu:
            plugin_menu.addMenu(self.main_menu)
        
        self.search_filter = SearchFilter(self)
        self.iface.registerLocatorFilter(self.search_filter)    
        #self.iface.messageBar().pushMessage(self.myPluginV,f'Sollte Euch das Plugin gefallen,{"&nbsp;"}könnt Ihr es gern mit Eurer Mitarbeit,{"&nbsp;"}einem Voting und ggf.{"&nbsp;"}einem kleinen Betrag unterstützen ...{"&nbsp;"}Danke!!', 3, 8)     
    
    def initGui(self) -> None:
        self.main_menu.clear()
        
        if self.services is not None:
            # ------- Name des Katalogs einfügen -------------------------
            self.main_menu.addAction(self.qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)["titel"])
            self.main_menu.addSeparator()
            
            # ------- Favoritenmenü ------------------------
            favorite_menu = QMenu(STAR_PREFIX + "Favoriten", self.main_menu)
            favorite_menu.setObjectName('favorites-menu')
            favorite_menu.setToolTipsVisible(True)
            
            for key in PropertyManager._favorite:
                topic = self.services.get_entry(key)
                if not topic:
                    continue
                
                action = QAction(topic.name, favorite_menu)
                action.setObjectName(topic.name)
                action.setData(key)
                action.triggered.connect(self.add_topic)
                favorite_menu.addAction(action)
            
            self.main_menu.addMenu(favorite_menu)
            self.main_menu.addSeparator()
            
            # ------- Menübaum bauen und einfügen ------------------------
            for region in self.services.get_regions():
                if not region.properties.visible:
                    continue
                
                region_menu = self.gui_for_one_region(region.get_topics(), region.name)
                self.main_menu.addMenu(region_menu)
                
                if region.separator:
                    self.main_menu.addSeparator()
            
            self.main_menu.addSeparator()
            
        if CatalogManager.overview is not None:
            # ------- Katalogmenü erstellen ------------------------------------
            catalogs_menu = self.main_menu.addMenu("Katalog wechseln (Change Catalogs)")
            if not catalogs_menu:
                logger.error("Menü 'Katalog wechseln' nicht vorhanden")
                return
            
            catalogs_menu.setObjectName('catalog-overview')
            
            # ------- Einträge im Katalogmenü erstellen ------------------------
            for catalog in CatalogManager.overview:
                catalog_action = catalogs_menu.addAction(catalog["titel"], partial(self.change_current_catalog, catalog))
                if not catalog_action:
                    logger.warning(f"Eintrag für Katalog '{catalog["titel"]}' nicht vorhanden")
                    continue
                
                catalog_action.setObjectName("open-" + catalog["titel"])
            
            action = self.main_menu.addAction("Kataloge neu laden (Reload Catalogs)")
            if action:
                action.triggered.connect(lambda: CatalogManager.get_overview(callback=self.initGui))
            
            self.main_menu.addSeparator()
                
        # ------- Über-Schaltfläche für die JSON-Datei ------------------------
        action = QAction(text="Wenn möglich, Dienste autom. im KBS laden", parent=self.main_menu, checkable=True, checked=self.automatic_crs) # type: ignore
        action.toggled.connect(self.toggle_automatic_crs)
        self.main_menu.addAction(action)
        
        self.main_menu.addAction("Einstellungen (Aktueller Katalog)", self.open_settings)
        self.main_menu.addSeparator()
        
        # ------- Spenden-Schaltfläche für #geoObserver ------------------------
        action = self.main_menu.addAction("GeoBasis_Loader per Spende unterstützen ...", self.open_web_site)
        if action:
            action.setData('https://geoobserver.de/support_geobasis_loader/')
        
        # ------- Über-Schaltfläche für #geoObserver ------------------------
        action = self.main_menu.addAction("Über ...", self.open_web_site)
        if action:
            action.setData('https://geoobserver.de/qgis-plugin-geobasis-loader/')

        # ------- Status-Schaltfläche für #geoObserver ------------------------
        # self.mainMenu.addAction("Status ...", partial(self.openWebSite, 'https://geoobserver.de/qgis-plugin-geobasis-loader/#statustabelle'))
        
    def gui_for_one_region(self, topics: list[catalog_types.TopicLike], region_title: str) -> QMenu:
        def _create_action(name: str, parent: QMenu, path: str, tip: str = "Thema hinzufügen", slot = self.add_topic) -> QAction:
            action = QAction(name, parent)
            action.setObjectName(name)
            action.setStatusTip(tip)
            action.setToolTip(tip)
            action.setData(path)
            action.triggered.connect(slot)
            return action
        
        menu = QMenu(region_title, self.main_menu)
        menu.setObjectName('region-' + region_title)
        menu.setToolTipsVisible(True)
        
        for topic in topics:
            if not topic.properties.visible:
                continue
            
            if isinstance(topic, catalog_types.Topic) and topic.topic_type == catalog_types.TopicType.WEB:
                action = _create_action(topic.name, menu, topic.uri, "Informationen öffnen", self.open_web_site)
                menu.addAction(action)
                continue
            
            if isinstance(topic, catalog_types.TopicGroup):
                topic_group_menu = QMenu(topic.name, menu)
                topic_group_menu.setToolTipsVisible(True)
                
                add_all_action = _create_action("Alle laden", topic_group_menu, topic.path, "Alle Themen der Gruppe laden")
                topic_group_menu.addAction(add_all_action)
                topic_group_menu.addSeparator()

                for subtopic in topic.get_subtopics():
                    if not subtopic.properties.visible:
                        continue
                    
                    if subtopic.topic_type == catalog_types.TopicType.WEB:
                        subtopic_action = _create_action(subtopic.name, topic_group_menu, subtopic.uri, "Informationen öffnen", self.open_web_site)
                    else:
                        subtopic_action = _create_action(subtopic.name, topic_group_menu, subtopic.path)
                    topic_group_menu.addAction(subtopic_action)

                menu.addMenu(topic_group_menu)
            else:
                action = _create_action(topic.name, menu, topic.path)            
                menu.addAction(action)
                
            if topic.separator:
                menu.addSeparator()
        return menu
    
#===================================================================================

    def unload(self):
        self.iface.invalidateLocatorResults()
        self.iface.deregisterLocatorFilter(self.search_filter)
        self.search_filter = None
        plugin_menu = self.iface.pluginMenu()
        if self.main_menu and plugin_menu:
            plugin_menu.removeAction(self.main_menu.menuAction())
        custom_logger.remove_logging()

#===================================================================================

    @property
    def epsg_dialog(self):
        if self._epsg_dialog is None:
            self._epsg_dialog = custom_ui.EpsgDialog(self.iface.mainWindow())
        return self._epsg_dialog
    
    @property
    def settings_dialog(self):
        if self._settings_dialog is None:
            self._settings_dialog = custom_ui.SettingsDialog(self.iface.mainWindow())
        return self._settings_dialog

    def open_settings(self) -> None:
        status = self.settings_dialog.exec()
        # Abbruch
        if status == 0:
            return
        
        self.automatic_crs = self.qgs_settings.value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, bool)
        
        logger.success("Einstellungen erfolgreich gespeichert", extra={"show_banner": True})
        self.initGui()

    def toggle_automatic_crs(self) -> None:
        new_state = not self.automatic_crs
        
        self.automatic_crs = new_state
        self.qgs_settings.setValue(config.QgsSettingsKeys.AUTOMATIC_CRS, new_state)

    def open_web_site(self):
        sender = self.sender()
        if not sender or not isinstance(sender, QAction):
            return
        
        data = sender.data() # type: ignore
        url = QUrl(data)
        
        # Opens webpage in the standard browser
        QDesktopServices.openUrl(url)
        
    def change_current_catalog(self, catalog: dict):
        self.qgs_settings.setValue(config.QgsSettingsKeys.CURRENT_CATALOG, catalog)
        CatalogManager.get_catalog(catalog["titel"], callback=self.set_services)
        
    def set_services(self, services: catalog_types.Catalog):
        current_catalog = self.qgs_settings.value(config.QgsSettingsKeys.CURRENT_CATALOG)
        if current_catalog is None or "titel" not in current_catalog:
            logger.warning(f"Momentan ist kein valider Katalog ausgewählt, Bitten wählen Sie einen aus", extra={"show_banner": True})
            return
        
        titel = current_catalog["titel"]
        name = current_catalog["name"]
        version_matches = re.findall(r'v\d+', name)
        version = version_matches[0] if version_matches else "unbekannt"
        logger.success(f'Lese {titel}, Version {version} ...', extra={"show_banner": True})
        
        self.services = services
        self.initGui()
    
    # Get crs from user
    def get_crs(self, supported_auth_ids: list[str], layer_name: str) -> Union[str, None]:
        if supported_auth_ids is None:
            return None
        
        current_qgis_project = QgsProject.instance()
        if not current_qgis_project:
            logger.error(f"Das aktuelle Projekt kann nicht geladen werden")    
            return None
        
        current_crs = current_qgis_project.crs().authid()          
        if current_crs not in supported_auth_ids or not self.automatic_crs:
            self.epsg_dialog.set_table_data(supported_auth_ids, layer_name)
            self.epsg_dialog.exec()
            if self.epsg_dialog.selected_coord is None:
                return None
            current_crs = self.epsg_dialog.selected_coord
        
        return current_crs
    
    def add_topic(self, path: str):
        if not self.services:
            logger.error(f"No catalog selected")
            return

        if not path:
            sender = self.sender()
            if not sender:
                return

            path = sender.data() # type: ignore

        topic = self.services.get_entry(path)
        if not topic:
            logger.error(f"Topic with path '{path}' not found")
            return
        
        if isinstance(topic, catalog_types.Region):
            logger.warning(f"Can't add a region to the project")
            return
        
        if isinstance(topic, catalog_types.Topic):
            self.add_layer(topic, None)
            return
        
        if isinstance(topic, catalog_types.TopicCombination):
            self.add_layer_combination(topic)
        else:
            self.add_layer_group(topic, None, topic.name)
    
    def add_layer(self, topic: catalog_types.Topic, crs: Union[str, None], standalone: bool = True):
        if not topic.properties.enabled:
            return None
        
        if topic.topic_type == catalog_types.TopicType.WEB:
            return None
       
        if crs is None or crs not in topic.valid_epsg_codes:
            crs = self.get_crs(topic.valid_epsg_codes, topic.name)
            if crs is None:
                return

        uri = topic.uri
        layer_type = topic.topic_type
        layer_name = topic.name
        max_scale = topic.max_scale
        min_scale = topic.min_scale

        if uri == "n.n.":
            logger.critical(f"Ladefehler Thema '{layer_name}': URL des Themas derzeit unbekannt.{'&nbsp;'}Falls gültige/aktuelle URL bekannt,{'&nbsp;'}bitte dem Autor melden.", extra={"show_banner": True})
            return
        
        uri = uri.replace("EPSG:placeholder", crs, 1)
        
        if not topic.is_vector():
            uri += "&stepHeight=3000&stepWidth=3000"
        
        if layer_type == catalog_types.TopicType.WFS:
            layer = QgsVectorLayer(uri, layer_name, 'wfs')
        elif layer_type == catalog_types.TopicType.APIF:
            layer = QgsVectorLayer(uri, layer_name, 'oapif')
        elif layer_type == catalog_types.TopicType.VECTORTILES:
            layer = QgsVectorTileLayer(uri, layer_name)
            layer.loadDefaultStyle()
        elif layer_type == catalog_types.TopicType.WCS:
            layer = QgsRasterLayer(uri, layer_name, 'wcs')
        elif layer_type == catalog_types.TopicType.WMS:
            layer = QgsRasterLayer(uri, layer_name, 'wms')
        else:
            raise ValueError(f"Unknown layer type: {layer_type}")

        if not layer.isValid():
            logger.critical(f"Layerladefehler {layer_name}, Dienst nicht verfügbar (URL?)", extra={"show_banner": True})
            return
        
        if hasattr(layer, 'setOpacity'):
            layer.setOpacity(topic.opacity)
            
        if isinstance(layer, QgsVectorLayer):
            if max_scale is None:
                max_scale = 1.0
            if min_scale is None:
                min_scale = 25000
        
        if min_scale is not None and max_scale is not None:
            if min_scale < max_scale:
                logger.critical(f"Layerladefehler {layer_name}, Skalenwerte vertauscht oder fehlerhaft", extra={"show_banner": True})
            elif min_scale == max_scale: 
                logger.critical(f"Layerladefehler {layer_name}, Skalenwerte gleich", extra={"show_banner": True})
            elif min_scale > max_scale:
                layer.setMinimumScale(min_scale)
                layer.setMaximumScale(max_scale)
                layer.setScaleBasedVisibility(True)
        
        if isinstance(layer, QgsVectorLayer):
            try:
                fill_color: QColor = QColor(*[int(c) for c in topic.fill_color]) if isinstance(topic.fill_color, list) else QColor(topic.fill_color)
            except (TypeError, ValueError):
                logger.warning(f"Ungültiger fillColor-Wert '{topic.fill_color}' für Layer '{layer_name}', verwende Grau")
                fill_color = QColor(220, 220, 220)
            
            try:
                stroke_color: QColor = QColor(*[int(c) for c in topic.stroke_color]) if isinstance(topic.stroke_color, list) else QColor(topic.stroke_color)
            except (ValueError, TypeError):
                logger.warning(f"Ungültiger strokeColor-Wert '{topic.stroke_color}' für Layer '{layer_name}', verwende Schwarz")
                stroke_color = QColor(0, 0, 0)
            
            renderer = layer.renderer()
            if renderer is None:
                logger.warning("Renderer ist None für Layer: " + layer_name)
            else:
                symbol = renderer.symbol() # type: ignore
                if symbol is None or symbol.symbolLayerCount() == 0:
                    logger.warning("Symbol ist None oder leer für Layer: " + layer_name)
                else:
                    symbol_layer: QgsSymbolLayer = symbol.symbolLayer(0)
                    try:
                        symbol_layer.setColor(fill_color)

                        geom_type = QgsWkbTypes.singleType(QgsWkbTypes.flatType(layer.wkbType()))
                        if geom_type == geometry_types.LineString:
                            symbol_layer.setWidth(topic.stroke_width)
                        elif geom_type == geometry_types.Polygon:
                            symbol_layer.setStrokeColor(stroke_color)
                            symbol_layer.setStrokeWidth(topic.stroke_width)
                        elif geom_type == geometry_types.Point:
                            symbol_layer.setSize(topic.stroke_width)
                        else:
                            logger.critical(f"Fehler bei Bestimmung der Geometrieart, Bestimmte Geometrie: {QgsWkbTypes.displayString(geom_type)}")
                    except AttributeError as e:
                        logger.warning(f"Styling für '{layer_name}' fehlgeschlagen: {e}")
                        
            layer.triggerRepaint()
            layer_tree_view =  self.iface.layerTreeView()
            if layer_tree_view is None:
                logger.warning(f"Symbologie nicht aktualisert, da Zugriff auf Ebenenbaum nicht erfolgreich")
            else:
                layer_tree_view.refreshLayerSymbology(layer.id())
        
        current_qgis_project = QgsProject.instance()
        if not current_qgis_project:
            logger.critical(f"Thema '{layer_name}' kann nicht zum Projekt hinzugefügt werden")
            return layer
        
        current_qgis_project.addMapLayer(layer, False)

        # Ebene zum Projekt hinzufügen aber nicht automatisch zum Ebenenbaum
        if standalone and current_qgis_project:
            root = current_qgis_project.layerTreeRoot()
            if root is None:
                logger.error(f"Thema '{layer_name}' kann nicht zum Ebenenbaum hinzugefügt werden")    
            else:    
                ltl = root.insertLayer(0, layer)
                if ltl:
                    ltl.setExpanded(False)
                    ltl.setItemVisibilityChecked(topic.properties.visible)

        logger.success(f"Thema '{layer_name}' erfolgreich geladen")
        return layer
    
    def add_layer_group(self, topic_group: catalog_types.TopicGroup, preferred_crs: Union[str, None], name: str) -> None:
        if preferred_crs is None:
            # Get first non-web layer for crs information
            subtopic_iter = iter(topic_group.get_subtopics())
            priority_subtopic = next(subtopic_iter, None)
            while True:
                if priority_subtopic is None:
                    return
                
                if priority_subtopic.topic_type == catalog_types.TopicType.WEB:
                    priority_subtopic = next(subtopic_iter, None)
                    continue
                
                break
            
            preferred_crs = self.get_crs(priority_subtopic.valid_epsg_codes, priority_subtopic.name)
            if preferred_crs is None:
                return
            
        current_qgis_project = QgsProject.instance()
        if not current_qgis_project:
            logger.error(f"Das aktuelle Projekt kann nicht geladen werden")    
            return
        
        layer_tree_root = current_qgis_project.layerTreeRoot()
        if not layer_tree_root:
            logger.error("Ebenenbaum kann nicht geladen werden")
            return
        
        new_layer_group = layer_tree_root.insertGroup(0, name)
        if new_layer_group is None:
            return
        
        for subtopic in topic_group.get_subtopics():
            sub_layer = self.add_layer(subtopic, preferred_crs, False)
            if sub_layer is None:
                continue
            ltl = new_layer_group.insertLayer(0, sub_layer)
            if ltl:
                ltl.setExpanded(False)
                ltl.setItemVisibilityChecked(subtopic.properties.visible)
        
        # Leere Gruppe entfernen (wenn alle Sub-Layer fehlgeschlagen)
        if not new_layer_group.children():
            layer_tree_root.removeChildNode(new_layer_group)
            
    def add_layer_combination(self, topic_combination: catalog_types.TopicCombination) -> None:
        preferred_crs = None
        if not self.services:
            logger.error(f"No catalog selected")
            return
        
        referenced_topics: list[Union[catalog_types.Topic, catalog_types.TopicGroup]] = []
        for references in topic_combination.topic_paths:
            topic = self.services.get_entry(references)
            # FIXME: If reference points towards region, nothing or another topic combination, ignore them
            if not topic or isinstance(topic, (catalog_types.Region, catalog_types.TopicCombination)):
                continue
            referenced_topics.append(topic)
        
        if len(referenced_topics) < 1:
            logger.warning(f"Themenkombination '{topic_combination.name}' besitzt keine validen Einträge. Kontaktieren Sie den Autor", extra={"show_banner": True})
            return
        
        for topic in referenced_topics:
            if isinstance(topic, catalog_types.Topic):               
                preferred_crs = self.get_crs(topic.valid_epsg_codes, topic.name)
                break
            else:
                subtopic_iter = iter(topic.get_subtopics())
                priority_subtopic = next(subtopic_iter, None)
                while True:
                    if priority_subtopic is None:
                        break
                    
                    if priority_subtopic.topic_type == catalog_types.TopicType.WEB:
                        priority_subtopic = next(subtopic_iter, None)
                        continue
                    
                    break
                
                if not priority_subtopic:
                    continue
                
                preferred_crs = self.get_crs(priority_subtopic.valid_epsg_codes, priority_subtopic.name)
                break
        
        if preferred_crs is None:
            return
        
        for topic in referenced_topics:
            if isinstance(topic, catalog_types.Topic):
                self.add_layer(topic, preferred_crs)
            else:
                self.add_layer_group(topic, preferred_crs, topic.name)