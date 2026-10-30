from typing import Union
from copy import copy
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsTask, QgsVectorLayer, QgsRasterLayer, QgsVectorTileLayer, Qgis, QgsWkbTypes, QgsSymbolLayer, QgsProject, QgsApplication, QgsMessageLog
from qgis.gui import QgisInterface
from qgis.utils import iface
from ..models import ServiceType, Topic
from ....core import config
from ....core.types import CustomLayerProperty
from ....core.utils import custom_logger


class LayerLoaderTask(QgsTask):
    def __init__(
        self,
        topic: Topic,
        crs: str,
        standalone: bool = True
    ):
        super().__init__(f"Laden des Themas: {topic.name}", QgsTask.Flag.CanCancel | QgsTask.Flag.Silent) # type: ignore
        self.topic = topic
        self.crs = crs
        self.standalone = bool(standalone)
        
        self.layer = None
        self.exception = None
        self.logger = custom_logger.get_logger(__name__)
    
    def run(self) -> bool:
        if self.topic.uri == "n.n." or not self.topic.uri:
            self.exception = ValueError(f"Ladefehler Thema '{self.topic.title}': URL des Themas derzeit unbekannt. Falls gültige/aktuelle URL bekannt, bitte dem Autor melden.")
            return False
        
        uri = self.topic.uri.format(crs=self.crs)
        
        if not self.topic.is_vector():
            uri += "&stepHeight=3000&stepWidth=3000"
        
        if self.topic.service_type == ServiceType.WFS:
            layer = QgsVectorLayer(uri, self.topic.title, 'wfs')
        elif self.topic.service_type == ServiceType.APIF:
            layer = QgsVectorLayer(uri, self.topic.title, 'oapif')
        elif self.topic.service_type == ServiceType.ARCGIS_FEATURE_SERVER:
            layer = QgsVectorLayer(uri, self.topic.title, 'arcgisfeatureserver')
        elif self.topic.service_type == ServiceType.VECTORTILES:
            layer = QgsVectorTileLayer(uri, self.topic.title)
            layer.loadDefaultStyle()
        elif self.topic.service_type == ServiceType.WCS:
            layer = QgsRasterLayer(uri, self.topic.title, 'wcs')
        elif self.topic.service_type in (ServiceType.WMS, ServiceType.WMTS):
            layer = QgsRasterLayer(uri, self.topic.title, 'wms')
        elif self.topic.service_type == ServiceType.ARCGIS_MAP_SERVER:
            layer = QgsRasterLayer(uri, self.topic.title, 'arcgismapserver')
        else:
            self.exception = ValueError(f"Unknown layer type: {self.topic.service_type}")
            return False
        
        if self.isCanceled():
            return False
    
        if not layer.isValid():
            provider = layer.dataProvider()
            layer_error = layer.error().summary() if hasattr(layer, 'error') else "Unbekannter Fehler mit Layer"
            provider_error = provider.error().summary() if provider is not None and hasattr(provider, 'error') else "Unbekannter Fehler mit Datenanbieter"
            
            detail = " | ".join([msg for msg in (layer_error, provider_error) if msg])
            self.exception = RuntimeError(
                f"Layerladefehler {self.topic.title}, Dienst nicht verfügbar (URL?) - Details: {detail}",
            )
            return False
        
        if hasattr(layer, 'setOpacity'):
            layer.setOpacity(self.topic.opacity)

        max_scale = float(self.topic.max_scale) if self.topic.max_scale is not None else None
        min_scale = float(self.topic.min_scale) if self.topic.min_scale is not None else None

        if isinstance(layer, QgsVectorLayer):
            # Fallback: If not set the layer could stop loading due t the sheer number of features (e.g. 1000) in the layer. This is a QGIS default setting.
            if max_scale is None:
                max_scale = 1.0
            if min_scale is None:
                min_scale = 25000
        
        if min_scale is not None and max_scale is not None:
            if min_scale < max_scale:
                self.logger.warning(f"Thema '{self.topic.title}': Skalenwerte vertauscht, werden getauscht")
                min_scale, max_scale = max_scale, min_scale
            elif min_scale == max_scale:
                self.logger.warning(f"Thema '{self.topic.title}': minScale == maxScale, Grenzen ignoriert")
                min_scale = max_scale = None
        
        if min_scale is not None or max_scale is not None:
            layer.setMinimumScale(float(min_scale) if min_scale is not None else 0.0)
            layer.setMaximumScale(float(max_scale) if max_scale is not None else 0.0)
            layer.setScaleBasedVisibility(True)
        
        layer.setCustomProperty(CustomLayerProperty.GBL_NAME.value, self.topic.title)
        layer.setCustomProperty(CustomLayerProperty.GBL_ID.value, self.topic.id)
        layer.setCustomProperty(CustomLayerProperty.GBL_CRS.value, self.crs)
        
        if isinstance(layer, QgsVectorLayer):
            if isinstance(self.fill_color, list) and len(self.fill_color) >= 3:
                fill_color = QColor(*self.fill_color[:4])  # RGB oder RGBA
            elif isinstance(self.fill_color, str):
                fill_color = QColor(self.fill_color)
            else:
                self.logger.warning(f"Ungültige Füllfarbe mit dem Wert '{self.fill_color}' für das Thema '{self.topic.title}'")
                fill_color = QColor(220, 220, 220)
            
            if isinstance(self.stroke_color, list) and len(self.stroke_color) >= 3:
                stroke_color = QColor(*self.stroke_color[:4])  # RGB oder RGBA
            elif isinstance(self.stroke_color, str):
                stroke_color = QColor(self.stroke_color)
            else:
                self.logger.warning(f"Ungültige Strichfarbe mit dem Wert '{self.stroke_color}' für das Thema '{self.layer_name}', verwende Schwarz")
                stroke_color = QColor(0, 0, 0)
            
            if not (renderer := layer.renderer()):
                self.logger.warning("Renderer ist None für Layer: " + self.layer_name)
            else:
                symbol = renderer.symbol() # type: ignore
                if symbol is None or symbol.symbolLayerCount() == 0:
                    self.logger.warning("Symbol ist None oder leer für Layer: " + self.layer_name)
                else:
                    symbol_layer: QgsSymbolLayer = symbol.symbolLayer(0)
                    symbol_layer.setColor(fill_color)
                    geom_type = QgsWkbTypes.singleType(QgsWkbTypes.flatType(layer.wkbType()))
                    if geom_type == Qgis.WkbType.LineString:
                        symbol_layer.setWidth(self.stroke_width)
                    elif geom_type == Qgis.WkbType.Polygon:
                        symbol_layer.setStrokeColor(stroke_color)
                        symbol_layer.setStrokeWidth(self.stroke_width)
                    elif geom_type == Qgis.WkbType.Point:
                        symbol_layer.setSize(self.stroke_width)
                    else:
                        self.logger.critical(f"Fehler bei Bestimmung der Geometrieart, Bestimmte Geometrie: {QgsWkbTypes.displayString(geom_type)}")
        
        layer.moveToThread(QgsApplication.instance().thread())
        self.layer = layer
        return True
    
    def finished(self, result: bool) -> None:
        if not result or self.layer is None:
            if self.exception:
                self.logger.error(str(self.exception))
            else:
                # The task was manuelly canceled
                # self.logger.info(f"Laden des Themas '{self.layer_name}' wurde abgebrochen.")
                pass
            return
        
        if not isinstance(iface, QgisInterface):
            return

        self.layer.triggerRepaint()
        if (layer_tree_view := iface.layerTreeView()) is None:
            self.logger.warning(f"Symbologie des Themas '{self.layer_name}' nicht aktualisert, da Zugriff auf Ebenenbaum nicht erfolgreich")
        else:
            layer_tree_view.refreshLayerSymbology(self.layer.id())
        
        if (current_qgis_project := QgsProject.instance()) is None:
            self.logger.error(f"Thema '{self.layer_name}' kann nicht zum Projekt hinzugefügt werden")
            return
        
        current_qgis_project.addMapLayer(self.layer, False)
    
        # Ebene zum Projekt hinzufügen aber nicht automatisch zum Ebenenbaum
        if self.standalone and current_qgis_project is not None:
            root = current_qgis_project.layerTreeRoot()
            if root is None:
                self.logger.error(f"Thema '{self.layer_name}' kann nicht zum Ebenenbaum hinzugefügt werden")
                return
            else:    
                ltl = root.insertLayer(0, self.layer)
                # if ltl is not None:
                #     ltl.setCustomProperty("gbl_name", topic.name)
                #     ltl.setCustomProperty("gbl_path", topic.path)
                #     ltl.setCustomProperty("gbl_crs", crs)
                #     ltl.setExpanded(False)
                #     ltl.setItemVisibilityChecked(visible)
    
    def cancel(self) -> None:
        self.logger.info(f"Laden des Themas '{self.layer_name}' wurde abgebrochen.")
        super().cancel()
