from typing import Optional, Union
from functools import singledispatch
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QColor
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer, QgsSymbolLayer, QgsWkbTypes, Qgis, QgsSettings
from qgis.utils import iface
from . import catalog_types, CatalogManager
from ..ui import EpsgDialog
from .. import config
from ..utils import custom_logger

logger = custom_logger.get_logger(__file__)

# Get crs from user
def get_crs(supported_auth_ids: frozenset[str], layer_name: str) -> Union[str, None]:
    if supported_auth_ids is None:
        return None
    
    current_qgis_project = QgsProject.instance()
    if not current_qgis_project:
        logger.error(f"Das aktuelle Projekt kann nicht geladen werden")    
        return None
    
    automatic_crs = QgsSettings().value(config.QgsSettingsKeys.AUTOMATIC_CRS, False, type=bool)
    current_crs = current_qgis_project.crs().authid()
    if current_crs not in supported_auth_ids or not automatic_crs:
        epsg_dialog = EpsgDialog(iface.mainWindow())
        epsg_dialog.set_table_data(supported_auth_ids, layer_name)
        epsg_dialog.exec()
        if epsg_dialog.selected_coord is None:
            return None
        current_crs = epsg_dialog.selected_coord
    
    return current_crs

@singledispatch
def add_topic(topic, crs: Optional[str] = None) -> None:
    logger.error(f"Unsupported topic type: {type(topic)}")

@add_topic.register(str)
def _(path: str, crs: Optional[str] = None) -> None:
    current_catalog = CatalogManager.get_current_catalog()
    if not isinstance(current_catalog, catalog_types.Catalog):
        logger.error("Aktueller Katalog kann nicht geladen werden")
        return
    
    topic = current_catalog.get_entry(path)
    if not topic:
        logger.error(f"Thema mit dem Pfad '{path}' nicht gefunden")
        return
    
    add_topic(topic, crs)

@add_topic.register(catalog_types.Topic)
def _(topic: catalog_types.Topic, crs: Optional[str] = None) -> None:
    add_layer(topic, crs)

@add_topic.register(catalog_types.TopicGroup)
def _(topic_group: catalog_types.TopicGroup, crs: Optional[str] = None) -> None:
    add_layer_group(topic_group, crs)

@add_topic.register(catalog_types.TopicCombination)
def _(topic_combination: catalog_types.TopicCombination, crs: Optional[str] = None) -> None:
    add_layer_combination(topic_combination, crs)

def open_web_site(url: str):
    if not isinstance(url, str):
        return
    
    q_url = QUrl(url)
    
    # Opens webpage in the standard browser
    QDesktopServices.openUrl(q_url)

def add_layer(topic: catalog_types.Topic, crs: Optional[str], standalone: bool = True) -> Optional[Union[QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer]]:
    if not topic.properties.enabled:
        return None
    
    if topic.topic_type == catalog_types.TopicType.WEB:
        return None
    
    if crs is None or crs not in topic.valid_epsg_codes:
        crs = get_crs(topic.valid_epsg_codes, topic.name)
        if crs is None:
            return None

    uri = topic.uri
    layer_type = topic.topic_type
    layer_name = topic.name
    max_scale = topic.max_scale
    min_scale = topic.min_scale

    if uri == "n.n.":
        logger.critical(f"Ladefehler Thema '{layer_name}': URL des Themas derzeit unbekannt.{'&nbsp;'}Falls gültige/aktuelle URL bekannt,{'&nbsp;'}bitte dem Autor melden.", extra={"show_banner": True})
        return None
    
    uri = uri.replace("EPSG:placeholder", crs, 1)
    
    if not topic.is_vector():
        uri += "&stepHeight=3000&stepWidth=3000"
    
    if layer_type == catalog_types.TopicType.WFS:
        layer = QgsVectorLayer(uri, layer_name, 'wfs')
    elif layer_type == catalog_types.TopicType.APIF:
        layer = QgsVectorLayer(uri, layer_name, 'oapif')
    elif layer_type == catalog_types.TopicType.ARCGIS_FEATURE_SERVER:
        layer = QgsVectorLayer(uri, layer_name, 'arcgisfeatureserver')
    elif layer_type == catalog_types.TopicType.VECTORTILES:
        layer = QgsVectorTileLayer(uri, layer_name)
        layer.loadDefaultStyle()
    elif layer_type == catalog_types.TopicType.WCS:
        layer = QgsRasterLayer(uri, layer_name, 'wcs')
    elif layer_type == catalog_types.TopicType.WMS:
        layer = QgsRasterLayer(uri, layer_name, 'wms')
    elif layer_type == catalog_types.TopicType.ARCGIS_MAP_SERVER:
        layer = QgsRasterLayer(uri, layer_name, 'arcgismapserver')
    else:
        raise ValueError(f"Unknown layer type: {layer_type}")

    if not layer.isValid():
        logger.critical(f"Layerladefehler {layer_name}, Dienst nicht verfügbar (URL?)", extra={"show_banner": True})
        return None
    
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
                    symbol_layer.setWidth(topic.stroke_width)
                elif geom_type == Qgis.WkbType.Polygon:
                    symbol_layer.setStrokeColor(stroke_color)
                    symbol_layer.setStrokeWidth(topic.stroke_width)
                elif geom_type == Qgis.WkbType.Point:
                    symbol_layer.setSize(topic.stroke_width)
                else:
                    logger.critical(f"Fehler bei Bestimmung der Geometrieart, Bestimmte Geometrie: {QgsWkbTypes.displayString(geom_type)}")
                    
        layer.triggerRepaint()
        layer_tree_view =  iface.layerTreeView() # type: ignore
        if layer_tree_view is None:
            logger.warning(f"Symbologie nicht aktualisert, da Zugriff auf Ebenenbaum nicht erfolgreich")
        else:
            layer_tree_view.refreshLayerSymbology(layer.id())
    
    current_qgis_project = QgsProject.instance()
    if current_qgis_project is None:
        logger.critical(f"Thema '{layer_name}' kann nicht zum Projekt hinzugefügt werden")
        return layer
    
    current_qgis_project.addMapLayer(layer, False)

    # Ebene zum Projekt hinzufügen aber nicht automatisch zum Ebenenbaum
    if standalone and current_qgis_project is not None:
        root = current_qgis_project.layerTreeRoot()
        if root is None:
            logger.error(f"Thema '{layer_name}' kann nicht zum Ebenenbaum hinzugefügt werden")    
        else:    
            ltl = root.insertLayer(0, layer)
            if ltl is not None:
                ltl.setCustomProperty("gbl_path", topic.path)
                ltl.setCustomProperty("gbl_crs", crs)
                ltl.setExpanded(False)
                ltl.setItemVisibilityChecked(topic.properties.visible)

    logger.success(f"Thema '{layer_name}' erfolgreich geladen")
    return layer

def add_layer_group(topic_group: catalog_types.TopicGroup, preferred_crs: Optional[str]) -> None:
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
        
        preferred_crs = get_crs(priority_subtopic.valid_epsg_codes, priority_subtopic.name)
        if preferred_crs is None:
            return
        
    current_qgis_project = QgsProject.instance()
    if not current_qgis_project:
        logger.error(f"Das aktuelle Projekt kann nicht geladen werden")    
        return
    
    layer_tree_root = current_qgis_project.layerTreeRoot()
    if layer_tree_root is None:
        logger.error("Ebenenbaum kann nicht geladen werden")
        return
    
    new_layer_group = layer_tree_root.insertGroup(0, topic_group.name)
    if new_layer_group is None:
        return
    
    new_layer_group.setCustomProperty("gbl_path", topic_group.path)
    new_layer_group.setCustomProperty("gbl_crs", preferred_crs)
    
    for subtopic in topic_group.get_subtopics():
        sub_layer = add_layer(subtopic, preferred_crs, False)
        if sub_layer is None:
            continue
        ltl = new_layer_group.insertLayer(0, sub_layer)
        if ltl is not None:
            ltl.setCustomProperty("gbl_path", topic_group.path)
            ltl.setCustomProperty("gbl_crs", sub_layer.crs().authid())
            ltl.setExpanded(False)
            ltl.setItemVisibilityChecked(subtopic.properties.visible)
    
    # Leere Gruppe entfernen (wenn alle Sub-Layer fehlgeschlagen)
    if not new_layer_group.children():
        layer_tree_root.removeChildNode(new_layer_group)
        
def add_layer_combination(topic_combination: catalog_types.TopicCombination, preferred_crs: Optional[str]) -> None:
    current_catalog = CatalogManager.get_current_catalog()
    if not isinstance(current_catalog, catalog_types.Catalog):
        logger.error("Aktueller Katalog kann nicht geladen werden")
        return
    
    referenced_topics: list[Union[catalog_types.Topic, catalog_types.TopicGroup]] = []
    for references in topic_combination.topic_paths:
        topic = current_catalog.get_entry(references)
        # FIXME: If reference points towards region, nothing or another topic combination, ignore them
        if not topic or isinstance(topic, (catalog_types.Region, catalog_types.TopicCombination)):
            continue
        referenced_topics.append(topic)
    
    if len(referenced_topics) < 1:
        logger.warning(f"Themenkombination '{topic_combination.name}' besitzt keine validen Einträge. Kontaktieren Sie den Autor", extra={"show_banner": True})
        return
    
    if preferred_crs is None:
        for topic in referenced_topics:
            if isinstance(topic, catalog_types.Topic):               
                preferred_crs = get_crs(topic.valid_epsg_codes, topic.name)
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
                
                preferred_crs = get_crs(priority_subtopic.valid_epsg_codes, priority_subtopic.name)
                break
    
        if preferred_crs is None:
            return
    
    for topic in referenced_topics:
        if isinstance(topic, catalog_types.Topic):
            add_layer(topic, preferred_crs)
        else:
            add_layer_group(topic, preferred_crs)