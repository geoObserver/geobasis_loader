from typing import Optional, Union
from functools import singledispatch
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QColor
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer, QgsSymbolLayer, QgsWkbTypes, Qgis, QgsSettings
from qgis.utils import iface
from ..models import catalog_types
from ..services import registry
from ..ui.dialogs import EpsgDialog
from .. import config
from ..utils import custom_logger

logger = custom_logger.get_logger(__name__)

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
        if iface is None or hasattr(iface, 'mainWindow') is False:
            logger.warning("Kein iface verfügbar (Headless?), CRS-Dialog übersprungen")
            return None
        
        epsg_dialog = EpsgDialog(iface.mainWindow())
        epsg_dialog.set_table_data(supported_auth_ids, layer_name)
        code = epsg_dialog.exec()
        if code != epsg_dialog.DialogCode.Accepted:
            return None
        current_crs = epsg_dialog.selected_coord
    
    return current_crs

@singledispatch
def add_topic(topic, crs: Optional[str] = None, show_banner: bool = True) -> bool:
    logger.error(f"Unsupported topic type: {type(topic)}", extra={"show_banner": show_banner})
    return False

@add_topic.register(str)
def _(path: str, crs: Optional[str] = None, show_banner: bool = True) -> bool:
    # FIXME: Adequate catalog overview
    catalog_id = path.split(":/")[0] if ":/" in path else ""
    catalog = registry.catalog_manager.catalogs.get(catalog_id)
    if not catalog:
        logger.error(f"Katalog mit der ID '{catalog_id}' nicht gefunden")
        return False
    
    if not isinstance(catalog, catalog_types.Catalog):
        logger.error("Aktueller Katalog kann nicht geladen werden")
        return False
    
    topic = catalog.get_entry(path)
    if not topic:
        logger.error(f"Thema mit dem Pfad '{path}' im Katalog '{catalog.name}' nicht gefunden")
        return False
    
    return add_topic(topic, crs, show_banner)

@add_topic.register(catalog_types.Topic)
def _(topic: catalog_types.Topic, crs: Optional[str] = None, show_banner: bool = True) -> bool:
    try:
        add_layer(topic, crs)
        logger.success(f"Thema '{topic.name}' erfolgreich geladen", extra={"show_banner": show_banner})
        return True
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen des Layers '{topic.name}': {e}")
        return False

@add_topic.register(catalog_types.TopicGroup)
def _(topic_group: catalog_types.TopicGroup, crs: Optional[str] = None, show_banner: bool = True) -> bool:
    return add_layer_group(topic_group, crs, show_banner)

@add_topic.register(catalog_types.TopicCombination)
def _(topic_combination: catalog_types.TopicCombination, crs: Optional[str] = None, show_banner: bool = True) -> bool:
    return add_layer_combination(topic_combination, crs, show_banner)

@add_topic.register(catalog_types.Region)
def _(region: catalog_types.Region, crs: Optional[str] = None, show_banner: bool = True) -> bool:
    logger.warning(
        f"Region '{region.name}' kann nicht direkt geladen werden — bitte ein konkretes Thema auswählen.",
        extra={"show_banner": show_banner},
    )
    return False

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
            raise ValueError(f"CRS für Thema '{topic.name}' konnte nicht bestimmt werden")

    uri = topic.uri
    layer_type = topic.topic_type
    layer_name = topic.name
    max_scale = topic.max_scale
    min_scale = topic.min_scale

    if uri == "n.n.":
        raise ValueError(f"Ladefehler Thema '{layer_name}': URL des Themas derzeit unbekannt. Falls gültige/aktuelle URL bekannt, bitte dem Autor melden.")
    
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
    elif layer_type in (catalog_types.TopicType.WMS, catalog_types.TopicType.WMTS):
        layer = QgsRasterLayer(uri, layer_name, 'wms')
    elif layer_type == catalog_types.TopicType.ARCGIS_MAP_SERVER:
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
        if max_scale is None:
            max_scale = 1.0
        if min_scale is None:
            min_scale = 25000
    
    if min_scale is not None and max_scale is not None:
        if min_scale < max_scale:
            raise RuntimeError(f"Layerladefehler {layer_name}, Skalenwerte vertauscht oder fehlerhaft")
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
        if iface is None or hasattr(iface, 'layerTreeView') is False:
            logger.warning("Kein iface verfügbar (Headless?), Ebenenbaum-Refresh übersprungen")
        else:
            layer_tree_view =  iface.layerTreeView()
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
                ltl.setCustomProperty("gbl_name", topic.name)
                ltl.setCustomProperty("gbl_path", topic.path)
                ltl.setCustomProperty("gbl_crs", crs)
                ltl.setExpanded(False)
                ltl.setItemVisibilityChecked(topic.properties.visible)
    
    return layer

def add_layer_group(topic_group: catalog_types.TopicGroup, preferred_crs: Optional[str], show_banner: bool = True) -> bool:
    # FIXME: Raise Exceptions
    if preferred_crs is None:
        # Get first non-web layer for crs information
        subtopic_iter = iter(topic_group.get_subtopics())
        priority_subtopic = next(subtopic_iter, None)
        while True:
            if priority_subtopic is None:
                return False
            
            if priority_subtopic.topic_type == catalog_types.TopicType.WEB:
                priority_subtopic = next(subtopic_iter, None)
                continue
            
            break
        
        preferred_crs = get_crs(priority_subtopic.valid_epsg_codes, priority_subtopic.name)
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
    
    new_layer_group = layer_tree_root.insertGroup(0, topic_group.name)
    if new_layer_group is None:
        return False
    
    new_layer_group.setCustomProperty("gbl_name", topic_group.name)
    new_layer_group.setCustomProperty("gbl_path", topic_group.path)
    new_layer_group.setCustomProperty("gbl_crs", preferred_crs)
    
    failures = 0
    for subtopic in topic_group.get_subtopics():
        try:
            sub_layer = add_layer(subtopic, preferred_crs, False)
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Layers '{subtopic.name}' für Thema '{topic_group.name}': {e}")
            failures += 1
            continue
        
        if sub_layer is None:
            continue
        ltl = new_layer_group.insertLayer(0, sub_layer)
        if ltl is not None:
            ltl.setCustomProperty("gbl_name", subtopic.name)
            ltl.setCustomProperty("gbl_path", subtopic.path)
            ltl.setCustomProperty("gbl_crs", sub_layer.crs().authid())
            ltl.setExpanded(False)
            ltl.setItemVisibilityChecked(subtopic.properties.visible)
        else:
            failures += 1
    
    # Leere Gruppe entfernen (wenn alle Sub-Layer fehlgeschlagen)
    if not new_layer_group.children():
        layer_tree_root.removeChildNode(new_layer_group)
    
    if failures == 0:
        logger.success(f"Themengruppe '{topic_group.name}' erfolgreich geladen", extra={"show_banner": show_banner})
    else:
        logger.warning(f"Themengruppe '{topic_group.name}' teilweise geladen: {failures}/{len(topic_group.get_subtopics())} Einträge konnten nicht geladen werden", extra={"show_banner": show_banner})
    
    return failures == 0
        
def add_layer_combination(topic_combination: catalog_types.TopicCombination, preferred_crs: Optional[str], show_banner: bool = True) -> bool:
    # FIXME: Raise Exceptions
    # Resolve the combination's own catalog (its references live in the same
    # catalog), not the currently selected one, so presets referencing a
    # combination from another catalog still resolve.
    catalog_id = topic_combination.path.split(":/")[0] if ":/" in topic_combination.path else ""
    owning_catalog = registry.catalog_manager.catalogs.get(catalog_id)
    if not isinstance(owning_catalog, catalog_types.Catalog):
        logger.error("Katalog der Themenkombination kann nicht geladen werden")
        return False

    referenced_topics: list[Union[catalog_types.Topic, catalog_types.TopicGroup]] = []
    for references in topic_combination.topic_paths:
        topic = owning_catalog.get_entry(references)
        # FIXME: If reference points towards region, nothing or another topic combination, ignore them
        if not topic or isinstance(topic, (catalog_types.Region, catalog_types.TopicCombination)):
            continue
        referenced_topics.append(topic)
    
    if len(referenced_topics) < 1:
        logger.warning(f"Themenkombination '{topic_combination.name}' besitzt keine validen Einträge. Kontaktieren Sie den Autor", extra={"show_banner": show_banner})
        return False
    
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
            return False
    
    failures = 0
    for topic in referenced_topics:
        if isinstance(topic, catalog_types.Topic):
            try:
                add_layer(topic, preferred_crs)
            except Exception as e:
                logger.error(f"Fehler beim Hinzufügen des Layers '{topic.name}' der Themenkombination '{topic_combination.name}': {e}")
                failures += 1
        else:
            success = add_layer_group(topic, preferred_crs, show_banner=show_banner)
            if not success:
                failures += 1
    
    if failures == 0:
        logger.success(f"Themenkombination '{topic_combination.name}' erfolgreich geladen", extra={"show_banner": show_banner})
    else:
        logger.warning(f"Themenkombination '{topic_combination.name}' teilweise geladen: {failures}/{len(referenced_topics)} Einträge konnten nicht geladen werden", extra={"show_banner": show_banner})
    
    return failures == 0