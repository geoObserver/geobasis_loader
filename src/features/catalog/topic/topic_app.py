from typing import Optional, Union
from functools import singledispatchmethod
from qgis.PyQt.QtCore import QObject, QUrl
from qgis.PyQt.QtGui import QDesktopServices, QColor
from qgis.core import QgsProject, QgsApplication, QgsTask, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer, QgsWkbTypes, QgsSymbolLayer, Qgis, Qgis
from qgis.utils import iface
from .. import models as catalog_types
from ..catalog_manager import CatalogManager
from . import topic_tasks
from ...property.property_manager import PropertyManager
from ..ui import EpsgDialog
from ....core import PluginSettings
from ....core.utils import custom_logger

logger = custom_logger.get_logger(__name__)


class TopicLoader:
    def __init__(self, property_manager: PropertyManager):
        self.property_manager = property_manager
        self._active_tasks: dict[str, QgsTask] = {}
    
    @staticmethod
    def get_crs(supported_auth_ids: frozenset[str], layer_name: str, dialog_parent: Optional[QObject] = None) -> Union[str, None]:
        if not supported_auth_ids:
            return None
        
        current_qgis_project = QgsProject.instance()
        if not current_qgis_project:
            logger.error(f"Das aktuelle Projekt kann nicht geladen werden")    
            return None
        
        automatic_crs = PluginSettings().automatic_crs
        current_crs = current_qgis_project.crs().authid()
        if current_crs not in supported_auth_ids or not automatic_crs:
            epsg_dialog = EpsgDialog(dialog_parent)
            epsg_dialog.set_table_data(supported_auth_ids, layer_name)
            code = epsg_dialog.exec()
            if code != epsg_dialog.DialogCode.Accepted:
                return None
            current_crs = epsg_dialog.selected_coord
        
        return current_crs
    
    @staticmethod
    def open_web_site(url: str):
        if not isinstance(url, str):
            return
        
        q_url = QUrl(url)
        
        # Opens webpage in the standard browser
        QDesktopServices.openUrl(q_url)
    
    @singledispatchmethod
    def add_topic(self, topic, visible: Union[bool, dict[str, bool]] = True, crs: Optional[str] = None, show_banner: bool = True) -> bool:
        logger.error(f"Unsupported topic type: {type(topic).__name__}", extra={"show_banner": show_banner})
        return False

    def add_topic_by_id(self, topic_id: str, catalog_manager: CatalogManager, visible: Union[bool, dict[str, bool]] = True, crs: Optional[str] = None, show_banner: bool = True) -> bool:        
        topic = catalog_manager.get_entry(topic_id)
        if not topic:
            logger.error(f"Thema mit ID '{topic_id}' nicht gefunden. Thema kann nicht geladen werden.", extra={"show_banner": show_banner})
            return False
        
        return self.add_topic(topic, visible, crs, show_banner)

    @add_topic.register(catalog_types.Topic)
    def _(self, topic: catalog_types.Topic, visible: Union[bool, dict[str, bool]] = True, crs: Optional[str] = None, show_banner: bool = True) -> bool:
        if topic.is_web():
            logger.warning(f"Web-Thema '{topic.title}' kann nicht als Layer geladen werden", extra={"show_banner": show_banner})
            return False
        
        # if crs is None or crs not in topic.crs:
        #     crs = self.get_crs(topic.crs, topic.title)
        #     if crs is None:
        #         logger.error(f"CRS für Thema '{topic.title}' konnte nicht bestimmt werden. Thema kann nicht geladen werden.")
        #         return

        if isinstance(visible, dict):
            visible = visible.get(topic.id, True)
        # FIXME: Enabled check
        # TODO: Add option for old version
        try:
            # topic_loading_task = topic_tasks.LayerLoaderTask(
            #     topic=topic,
            #     crs=crs
            # )
            # # topic_loading_task = topic_tasks.TestTask(name=f"TestTask for {topic.title}")
            # if task_manager := QgsApplication.taskManager():
            #     task_id = task_manager.addTask(topic_loading_task)
            #     if task_id == 0:
            #         raise RuntimeError(f"Failed to add task for topic '{topic.title}'")
            #     topic_loading_task.taskCompleted.connect(lambda: self._active_tasks.pop(str(task_id)))
            #     self._active_tasks[str(task_id)] = topic_loading_task
            self.add_layer(topic, visible, crs)
            logger.success(f"Thema '{topic.title}' erfolgreich geladen", extra={"show_banner": show_banner})
            return True
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Layers '{topic.title}': {e}", extra={"show_banner": show_banner})
            return False

    def add_layer(self, topic: catalog_types.Topic, visible: bool = True, crs: Optional[str] = None, standalone: bool = True) -> Optional[Union[QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer]]:
        if not self.property_manager.is_enabled(topic.id):
            return None
        
        if topic.is_web():
            return None
        
        if crs is None or crs not in topic.crs:
            crs = self.get_crs(topic.crs, topic.title)
            if crs is None:
                raise ValueError(f"CRS für Thema '{topic.title}' konnte nicht bestimmt werden")

        uri = topic.uri
        layer_type = topic.service_type
        layer_name = topic.title
        max_scale = topic.max_scale
        min_scale = topic.min_scale

        if uri == "n.n.":
            raise ValueError(f"Ladefehler Thema '{layer_name}': URL des Themas derzeit unbekannt. Falls gültige/aktuelle URL bekannt, bitte dem Autor melden.")
        
        uri = uri.format(crs=crs)
        
        if not topic.is_vector():
            uri += "&stepHeight=3000&stepWidth=3000"
        
        if layer_type == catalog_types.ServiceType.WFS:
            layer = QgsVectorLayer(uri, layer_name, 'wfs')
        elif layer_type == catalog_types.ServiceType.APIF:
            layer = QgsVectorLayer(uri, layer_name, 'oapif')
        elif layer_type == catalog_types.ServiceType.ARCGIS_FEATURE_SERVER:
            layer = QgsVectorLayer(uri, layer_name, 'arcgisfeatureserver')
        elif layer_type == catalog_types.ServiceType.VECTORTILES:
            layer = QgsVectorTileLayer(uri, layer_name)
            layer.loadDefaultStyle()
        elif layer_type == catalog_types.ServiceType.WCS:
            layer = QgsRasterLayer(uri, layer_name, 'wcs')
        elif layer_type in (catalog_types.ServiceType.WMS, catalog_types.ServiceType.WMTS):
            layer = QgsRasterLayer(uri, layer_name, 'wms')
        elif layer_type == catalog_types.ServiceType.ARCGIS_MAP_SERVER:
            layer = QgsRasterLayer(uri, layer_name, 'arcgismapserver')
        else:
            raise ValueError(f"Unknown layer type: {layer_type}")

        if not layer.isValid():
            provider = layer.dataProvider()
            layer_error = layer.error().message() if hasattr(layer, 'error') else "Unbekannter Fehler mit Layer"
            provider_error = provider.error().message() if provider is not None and hasattr(provider, 'error') else "Unbekannter Fehler mit Datenanbieter"
            
            detail = " | ".join([msg for msg in (layer_error, provider_error) if msg])
            raise RuntimeError(
                f"Layerladefehler {layer_name}, Dienst nicht verfügbar (URL?) - Details: {detail}",
            )
        
        if hasattr(layer, 'setOpacity'):
            layer.setOpacity(topic.opacity)
            
        if isinstance(layer, QgsVectorLayer):
            # Fallback: If not set the layer could stop loading due t the sheer number of features (e.g. 1000) in the layer. This is a QGIS default setting.
            if max_scale is None:
                max_scale = 1.0
            if min_scale is None:
                min_scale = 25000
        
        if min_scale is not None and max_scale is not None:
            if min_scale < max_scale:
                logger.warning(f"Thema '{layer_name}': Skalenwerte vertauscht, werden getauscht")
                min_scale, max_scale = max_scale, min_scale
            elif min_scale == max_scale:
                logger.warning(f"Thema '{layer_name}': minScale == maxScale, Grenzen ignoriert")
                min_scale = max_scale = None

        if min_scale is not None or max_scale is not None:
            layer.setMinimumScale(float(min_scale) if min_scale is not None else 0.0)
            layer.setMaximumScale(float(max_scale) if max_scale is not None else 0.0)
            layer.setScaleBasedVisibility(True)
        
        if isinstance(layer, QgsVectorLayer):
            if isinstance(topic.fill_color, list) and len(topic.fill_color) >= 3:
                fill_color = QColor(*topic.fill_color[:4])  # RGB oder RGBA
            elif isinstance(topic.fill_color, str):
                fill_color = QColor(topic.fill_color)
            else:
                logger.warning(f"Ungültiger fillColor-Wert '{topic.fill_color}' für '{layer_name}'")
                fill_color = QColor(220, 220, 220)
            
            if isinstance(topic.stroke_color, list) and len(topic.stroke_color) >= 3:
                stroke_color = QColor(*topic.stroke_color[:4])  # RGB oder RGBA
            elif isinstance(topic.stroke_color, str):
                stroke_color = QColor(topic.stroke_color)
            else:
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
                    symbol_layer.setColor(fill_color)
                    geom_type = QgsWkbTypes.singleType(QgsWkbTypes.flatType(layer.wkbType()))
                    if geom_type == Qgis.WkbType.LineString:
                        symbol_layer.setWidth(topic.stroke_width) # type: ignore
                    elif geom_type == Qgis.WkbType.Polygon:
                        symbol_layer.setStrokeColor(stroke_color)
                        symbol_layer.setStrokeWidth(topic.stroke_width) # type: ignore
                    elif geom_type == Qgis.WkbType.Point:
                        symbol_layer.setSize(topic.stroke_width) # type: ignore
                    else:
                        logger.critical(f"Fehler bei Bestimmung der Geometrieart, Bestimmte Geometrie: {QgsWkbTypes.displayString(geom_type)}")
                        
            layer.triggerRepaint()
            if iface is None or hasattr(iface, 'layerTreeView') is False:
                logger.warning("Kein iface verfügbar (Headless?), Ebenenbaum-Refresh übersprungen")
            else:
                layer_tree_view =  iface.layerTreeView() # type: ignore
                if layer_tree_view is None:
                    logger.warning(f"Symbologie nicht aktualisert, da Zugriff auf Ebenenbaum nicht erfolgreich")
                else:
                    layer_tree_view.refreshLayerSymbology(layer.id())
        
        current_qgis_project = QgsProject.instance()
        if current_qgis_project is None:
            raise RuntimeError(f"Thema '{layer_name}' kann nicht zum Projekt hinzugefügt werden")
        
        current_qgis_project.addMapLayer(layer, False)

        # Ebene zum Projekt hinzufügen aber nicht automatisch zum Ebenenbaum
        if standalone and current_qgis_project is not None:
            root = current_qgis_project.layerTreeRoot()
            if root is None:
                raise RuntimeError(f"Thema '{layer_name}' kann nicht zum Ebenenbaum hinzugefügt werden")
            else:
                ltl = root.insertLayer(0, layer)
                if ltl is not None:
                    # FIXME: Global types
                    ltl.setCustomProperty("gbl_name", topic.title)
                    ltl.setCustomProperty("gbl_path", topic.id)
                    ltl.setCustomProperty("gbl_crs", crs)
                    ltl.setExpanded(False)
                    ltl.setItemVisibilityChecked(visible)
        
        return layer

    @add_topic.register(catalog_types.TopicGroup)
    def add_layer_group(self, topic_group: catalog_types.TopicGroup, visibility: Union[bool, dict[str, bool]] = True, preferred_crs: Optional[str] = None, show_banner: bool = True) -> bool:
        # FIXME: Raise Exceptions
        if not self.property_manager.is_enabled(topic_group.id):
            return True
        
        if preferred_crs is None:        
            preferred_crs = self.get_crs(topic_group.crs, topic_group.title)
            if preferred_crs is None:
                return False
            
        current_qgis_project = QgsProject.instance()
        if not current_qgis_project:
            logger.error(f"Das aktuelle Projekt kann nicht geladen werden")    
            return False
        
        layer_tree_root = current_qgis_project.layerTreeRoot()
        if layer_tree_root is None:
            logger.error("Ebenenbaum kann nicht geladen werden")
            return False
        
        new_layer_group = layer_tree_root.insertGroup(0, topic_group.title)
        if new_layer_group is None:
            return False
        
        if isinstance(visibility, dict):
            group_visibility = visibility.get(topic_group.id, True)
        elif isinstance(visibility, bool):
            group_visibility = visibility
        else:
            group_visibility = True
        
        # FIXME: Global types
        new_layer_group.setCustomProperty("gbl_name", topic_group.title)
        new_layer_group.setCustomProperty("gbl_id", topic_group.id)
        new_layer_group.setCustomProperty("gbl_crs", preferred_crs)
        new_layer_group.setItemVisibilityChecked(group_visibility)
        
        failures = 0
        for subtopic in topic_group.get_subtopics():
            if isinstance(visibility, dict):
                subtopic_visibility = visibility.get(subtopic.id, True)
            else:
                # Always show subtopics when the input is a bool or something else -> Bool only for the group node
                subtopic_visibility = True
                
            try:
                sub_layer = self.add_layer(subtopic, subtopic_visibility, preferred_crs, False)
            except Exception as e:
                logger.error(f"Fehler beim Hinzufügen des Layers '{subtopic.title}' für Thema '{topic_group.title}': {e}")
                failures += 1
                continue
            
            if sub_layer is None:
                continue
            ltl = new_layer_group.insertLayer(0, sub_layer)
            if ltl is not None:
                ltl.setCustomProperty("gbl_name", subtopic.title)
                ltl.setCustomProperty("gbl_id", subtopic.id)
                ltl.setCustomProperty("gbl_crs", sub_layer.crs().authid())
                ltl.setExpanded(False)
                ltl.setItemVisibilityChecked(subtopic_visibility)
            else:
                failures += 1
        
        # Leere Gruppe entfernen (wenn alle Sub-Layer fehlgeschlagen)
        if not new_layer_group.children():
            layer_tree_root.removeChildNode(new_layer_group)
        
        if failures == 0:
            logger.success(f"Themengruppe '{topic_group.title}' erfolgreich geladen", extra={"show_banner": show_banner})
        else:
            logger.warning(f"Themengruppe '{topic_group.title}' teilweise geladen: {failures}/{len(topic_group.get_subtopics())} Einträge konnten nicht geladen werden", extra={"show_banner": show_banner})
        
        return failures == 0
    
    @add_topic.register(catalog_types.TopicCombination)
    def add_layer_combination(self, topic_combination: catalog_types.TopicCombination, visibility: Union[bool, dict[str, bool]] = True, preferred_crs: Optional[str] = None, show_banner: bool = True) -> bool:
        # FIXME: Raise Exceptions
        if not self.property_manager.is_enabled(topic_combination.id):
            return True
        
        if preferred_crs is None:
            preferred_crs = self.get_crs(topic_combination.crs, topic_combination.title)    
            if preferred_crs is None:
                return False
        
        if isinstance(visibility, dict) and len(visibility) == 1:
            visibility = visibility.get(topic_combination.id, True)
        
        failures = 0
        for topic in topic_combination.get_referenced_topics():            
            if isinstance(topic, catalog_types.Topic):
                if isinstance(visibility, dict):
                    subtopic_visibility = visibility.get(topic.id, True)
                elif isinstance(visibility, bool):
                    subtopic_visibility = visibility
                else:
                    subtopic_visibility = True
                
                try:
                    self.add_layer(topic, subtopic_visibility, preferred_crs)
                except Exception as e:
                    logger.error(f"Fehler beim Hinzufügen des Layers '{topic.title}' der Themenkombination '{topic_combination.title}': {e}")
                    failures += 1
            else:
                success = self.add_layer_group(topic, visibility, preferred_crs, show_banner=show_banner)
                if not success:
                    failures += 1
        
        if failures == 0:
            logger.success(f"Themenkombination '{topic_combination.title}' erfolgreich geladen", extra={"show_banner": show_banner})
        else:
            logger.warning(f"Themenkombination '{topic_combination.title}' teilweise geladen: {failures}/{len(topic_combination.get_referenced_topics())} Einträge konnten nicht geladen werden", extra={"show_banner": show_banner})
        
        return failures == 0
