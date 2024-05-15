from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.utils import *
import webbrowser

class GeoBasis_Loader:
    version = u'0.1'
    myPlugin = u'GeoBasis Loader'
    myPluginGB = myPlugin + u' >>>>>'
    myPluginV = myPlugin + u' v' + version
    myCritical_1 = u'Fehler beim Laden des Layers '
    myCritical_2 = u', Dienst nicht verfügbar (URL?)'
    myInfo_1 = u'Layer '
    myInfo_2 = u' erfolgreich geladen.'
    
    plugin_dir = os.path.dirname(__file__)
    
    # ------- DE - Deutschland ---------------------------
    myNameDE01 = 'DE: OpenStreetMap (XYZ)'
    myUriDE01 = '&type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0'
    
    myNameDE02 = 'DE: basemap.de grau (WMS)'
    myUriDE02 = 'crs=EPSG:3857&dpiMode=7&format=image/png&layers=de_basemapde_web_raster_grau&styles&tilePixelRatio=0&url=https://sgx.geodatenzentrum.de/wms_basemapde?REQUEST%3DGetCapabilities%26Version%3D1.3.0'
    
    myNameDE03 = 'DE: basemap.de farbig (WMS)'
    myUriDE03 = 'crs=EPSG:3857&dpiMode=7&format=image/png&layers=de_basemapde_web_raster_farbe&styles&tilePixelRatio=0&url=https://sgx.geodatenzentrum.de/wms_basemapde?REQUEST%3DGetCapabilities%26Version%3D1.3.0'
    
    myNameDE04 = 'DE: Verwaltungsgebiete 1:2 500 000 (WMS)'
    myUriDE04 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=vg2500_lan&styles&tilePixelRatio=0&url=https://sgx.geodatenzentrum.de/wms_vg2500'

    # ------- BB - Brandenburg -------------------------------
    myNameBB01 = u'BB: ALKIS Flurstücke (WMS)'
    myUriBB01 = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=adv_alkis_flurstuecke&styles=Farbe&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://isk.geobasis-bb.de/ows/alkis_wms'
    
    myNameBB02 = u'BB: ALKIS Gebäude (WMS)'
    myUriBB02 = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=adv_alkis_gebaeude&styles=Farbe&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://isk.geobasis-bb.de/ows/alkis_wms'
    
    myNameBB03 = u'BB: ALKIS Tatsächliche Nutzung (WMS)'
    myNameBB03a = u'Gewässer'
    myUriBB03a = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=adv_alkis_gewaesser&styles=Farbe&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://isk.geobasis-bb.de/ows/alkis_wms'
    myNameBB03b = u'Siedlung'
    myUriBB03b = 'ontextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=adv_alkis_siedlung&styles=Farbe&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://isk.geobasis-bb.de/ows/alkis_wms'
    myNameBB03c = u'Vegetation'
    myUriBB03c = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=adv_alkis_vegetation&styles=Farbe&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://isk.geobasis-bb.de/ows/alkis_wms'
    myNameBB03d = u'Verkehr'
    myUriBB03d = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=adv_alkis_verkehr&styles=Farbe&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://isk.geobasis-bb.de/ows/alkis_wms'
    
    myNameBB12 = u'BB: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)'
    
    myNameBB04 = u'BB: Bodenrichtwerte Bauland 2024 (WMS)'
    myUriBB04 = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=bbv_pg_zobau_2024&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://isk.geobasis-bb.de/ows/brw_wms'
 
    
    # ------- SN - Sachsen -------------------------------
    myNameSN01 = u'SN: ALKIS Flurstücke (WMS)'
    myUriSN01 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_flurstuecke&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest'
    
    myNameSN02 = u'SN: ALKIS Gebäude (WMS)'
    myUriSN02 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_gebaeude&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest'
    
    myNameSN03 = u'SN: ALKIS Tatsächliche Nutzung (WMS)'
    myNameSN03a = u'Gewässer'
    myUriSN03a = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_gewaesser&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest'
    myNameSN03b = u'Siedlung'
    myUriSN03b = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_siedlung&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest'
    myNameSN03c = u'Vegetation'
    myUriSN03c = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_vegetation&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest'
    myNameSN03d = u'Verkehr'
    myUriSN03d = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_verkehr&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest'
    
    myNameSN12 = u'SN: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)'
        
    myNameSN04 = u'ST: Bodenrichtwerte Bauland 2024 (WMS)'
    myUriSN04 = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=brw_akt&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.landesvermessung.sachsen.de/fp/http-proxy/svc?cfg%3Dboris'

    # ------- ST - Sachsen-Anhalt ------------------------
    myNameST01 = u'ST: ALKIS Flurstücke (WMS)'
    myUriST01 = 'crs=EPSG:25832&dpiMode=5&format=image/png&layers=adv_alkis_flurstuecke&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest'
    
    myNameST02 = u'ST: ALKIS Gebäude (WMS)'
    myUriST02 = 'crs=EPSG:25832&dpiMode=5&format=image/png&layers=adv_alkis_gebaeude&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest'
    
    myNameST03 = u'ST: ALKIS Tatsächliche Nutzung (WMS)'
    myNameST03a = u'Gewässer'
    myUriST03a = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_gewaesser&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest'
    myNameST03b = u'Siedlung'
    myUriST03b = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_siedlung&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest'
    myNameST03c = u'Vegetation'
    myUriST03c = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_vegetation&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest'
    myNameST03d = u'Verkehr'
    myUriST03d = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_verkehr&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest'
    
    myNameST12 = u'ST: ▶︎ ALKIS Flurstücke + Gebäude + Nutzung (WMS)'
    
    myNameST04 = u'ST: Bodenrichtwerte Bauland 2024 (WMS)'
    myUriST04 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=Bauland&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_BRW2024_gast/guest?VERSION%3D1.3.0'
    
    myNameST05 = u'ST: ALKIS Flurstücke (WFS)'
    myUriST05 = 'https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WFS_OpenData/guest?&service=WFS&BBOX=1332412,6708967,1333423,6709355&restrictToRequestBBOX=1&VERSION=auto&typename=ave:Flurstueck&srsname=EPSG:25832&preferCoordinatesForWfsT11=false&pagingEnabled=true'

    myNameST06 = u'ST: ALKIS Gebäude (WFS)'
    myUriST06 = 'https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WFS_OpenData/guest?&service=WFS&BBOX=1332412,6708967,1333423,6709355&restrictToRequestBBOX=1&VERSION=auto&typename=ave:GebaeudeBauwerk&srsname=EPSG:25832&preferCoordinatesForWfsT11=false&pagingEnabled=true'
    
    myNameST07 = u'ST: Topograf. Karten farbig (WMS)'
    myNameST07a = u'ST: TK 10 farbig (WMS)'
    myUriST07a = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=lsa_lvermgeo_dtk10_col_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST07b = u'ST: TK 25 farbig (WMS)'
    myUriST07b = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dtk25_col_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST07c = u'ST: TK 50 farbig (WMS)'
    myUriST07c = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dtk50_col_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST07d = u'ST: TK 100 farbig (WMS)'
    myUriST07d = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dtk100_col_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST07e = u'ST: TÜK 250 farbig (WMS)'
    myUriST07e = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=TUEK_250_col&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'

    myNameST08 = u'ST: Topograf. Karten grau (WMS)'
    myNameST08a = u'ST: TK 10 grau (WMS)'
    myUriST08a = 'contextualWMSLegend=0&crs=EPSG:25832&dpiMode=7&featureCount=10&format=image/png&layers=lsa_lvermgeo_dtk10_ein_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST08b = u'ST: TK 25 grau (WMS)'
    myUriST08b = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dtk25_ein_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST08c = u'ST: TK 50 grau (WMS)'
    myUriST08c = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dtk50_ein_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST08d = u'ST: TK 100 grau (WMS)'
    myUriST08d = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dtk100_ein_1&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'
    myNameST08e = u'ST: TÜK 250 grau (WMS)'
    myUriST08e = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=TUEK_250_grau&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0'

    myNameST09 = u'ST: Digitale Orthophotos - DOP20 (WMS)'
    myUriST09 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dop20_2&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest'

    myNameST10 = u'ST: Digitale Orthophotos - DOP100 (WMS)'
    myUriST10 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=lsa_lvermgeo_dop100_unbesch&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest'

    myNameST11 = u'BONUS - HAL: Digitale Stadtgrundkarte (WMS)'
    myUriST11 = 'crs=EPSG:2398&dpiMode=7&format=image/png&layers=DSGK&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=http://geodienste.halle.de/opendata/f398a5d8-9dce-cbbc-b7ae-7e1a7f5bf809'


    # ------- TH - Thüringen -----------------------------
    myNameTH01 = u'TH: ALKIS Flurstücke (WMS)'
    myUriTH01 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_flurstuecke&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th'
    
    myNameTH02 = u'TH: ALKIS Gebäude (WMS)'
    myUriTH02 = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_gebaeude&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th'
    
    myNameTH03 = u'TH: ALKIS Tatsächliche Nutzung (WMS)'
    myNameTH03a = u'Gewässer'
    myUriTH03a = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_gewaesser&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th'
    myNameTH03b = u'Siedlung'
    myUriTH03b = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_siedlung&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th'
    myNameTH03c = u'Vegetation'
    myUriTH03c = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_vegetation&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th'
    myNameTH03d = u'Verkehr'
    myUriTH03d = 'crs=EPSG:25832&dpiMode=7&format=image/png&layers=adv_alkis_verkehr&styles&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th'
    
    myNameTH12 = u'TH: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)'


# =========================================================================
    def __init__(self, iface):
        self.iface = iface
    
    def initGui(self):

        # ------- Menü für Deutschland initialisieren ------------------------
        menu = QMenu()
        menu.setObjectName('loader-de')

        action = menu.addAction(self.myNameDE01, self.addWmsDE01)
        action.setObjectName(self.myNameDE01)
        menu.addSeparator()
        action = menu.addAction(self.myNameDE02, self.addWmsDE02)
        action.setObjectName(self.myNameDE02)
        action = menu.addAction(self.myNameDE03, self.addWmsDE03)
        action.setObjectName(self.myNameDE03)
        action = menu.addAction(self.myNameDE04, self.addWmsDE04)
        action.setObjectName(self.myNameDE04)

        self.loadDTActions = QAction("Deutschland", self.iface.mainWindow())
        self.loadDTActions.setMenu(menu)
        self.iface.addPluginToMenu(self.myPlugin, self.loadDTActions)
        
        # ------- Menü für Brandenburg initialisieren ------------------------
        menu = QMenu()
        menu.setObjectName('loader-sn')
        
        action = menu.addAction(self.myNameBB01, self.addWmsBB01)
        action.setObjectName(self.myNameBB01)
        action = menu.addAction(self.myNameBB02, self.addWmsBB02)
        action.setObjectName(self.myNameBB02)
        action = menu.addAction(self.myNameBB03, self.addWmsBB03)
        action.setObjectName(self.myNameBB03)
        action = menu.addAction(self.myNameBB12, self.addWmsBB12)
        action.setObjectName(self.myNameBB12)
#        action = menu.addAction('geoObserver', self.open_website)
#        action.setObjectName('geoObserver')
        menu.addSeparator()
        action = menu.addAction(self.myNameBB04, self.addWmsBB04) # brw
        action.setObjectName(self.myNameBB04)

        self.loadBBActions = QAction("Brandenburg", self.iface.mainWindow())
        self.loadBBActions.setMenu(menu)
        self.iface.addPluginToMenu(self.myPlugin, self.loadBBActions)

        # ------- Menü für Sachsen initialisieren ------------------------
        menu = QMenu()
        menu.setObjectName('loader-sn')
        
        action = menu.addAction(self.myNameSN01, self.addWmsSN01)
        action.setObjectName(self.myNameSN01)
        action = menu.addAction(self.myNameSN02, self.addWmsSN02)
        action.setObjectName(self.myNameSN02)
        action = menu.addAction(self.myNameSN03, self.addWmsSN03)
        action.setObjectName(self.myNameSN03)
        action = menu.addAction(self.myNameSN12, self.addWmsSN12)
        action.setObjectName(self.myNameSN12)
        menu.addSeparator()
        action = menu.addAction(self.myNameSN04, self.addWmsSN04) # brw
        action.setObjectName(self.myNameSN04)

        self.loadSNActions = QAction("Sachsen", self.iface.mainWindow())
        self.loadSNActions.setMenu(menu)
        self.iface.addPluginToMenu(self.myPlugin, self.loadSNActions)

        # ------- Menü für Sachsen-Anhalt initialisieren ------------------------
        menu = QMenu()
        menu.setObjectName('loader-st')

        action = menu.addAction(self.myNameST01, self.addWmsST01) # fst
        action.setObjectName(self.myNameST01)
        action = menu.addAction(self.myNameST02, self.addWmsST02) # geb
        action.setObjectName(self.myNameST02)
        action = menu.addAction(self.myNameST03, self.addWmsST03) # nutz
        action.setObjectName(self.myNameST03)
        action = menu.addAction(self.myNameST12, self.addWmsST12) # fst, geb, nutz
        action.setObjectName(self.myNameST12)
        menu.addSeparator()
        action = menu.addAction(self.myNameST04, self.addWmsST04) # brw
        action.setObjectName(self.myNameST04)
        menu.addSeparator()
        action = menu.addAction(self.myNameST05, self.addWfsST05) # fst wfs
        action.setObjectName(self.myNameST05)
        action = menu.addAction(self.myNameST06, self.addWfsST06) # geb wfs
        action.setObjectName(self.myNameST06)
        menu.addSeparator()
        action = menu.addAction(self.myNameST07, self.addWmsST07) # fst wfs
        action.setObjectName(self.myNameST07)
        action = menu.addAction(self.myNameST08, self.addWmsST08) # geb wfs
        action.setObjectName(self.myNameST08)
        menu.addSeparator()
        action = menu.addAction(self.myNameST09, self.addWmsST09) # fst wfs
        action.setObjectName(self.myNameST09)
        action = menu.addAction(self.myNameST10, self.addWmsST10) # geb wfs
        action.setObjectName(self.myNameST10)
        menu.addSeparator()
        action = menu.addAction(self.myNameST11, self.addWmsST11) # fst wfs
        action.setObjectName(self.myNameST11)

        self.loadSTActions = QAction("Sachsen-Anhalt", self.iface.mainWindow())
        self.loadSTActions.setMenu(menu)
        self.iface.addPluginToMenu(self.myPlugin, self.loadSTActions)

        # ------- Menü für Thüringen initialisieren ------------------------
        menu = QMenu()
        menu.setObjectName('loader-th')
        
        action = menu.addAction(self.myNameTH01, self.addWmsTH01)
        action.setObjectName(self.myNameTH01)
        action = menu.addAction(self.myNameTH02, self.addWmsTH02)
        action.setObjectName(self.myNameTH02)
        action = menu.addAction(self.myNameTH03, self.addWmsTH03)
        action.setObjectName(self.myNameTH03)
        action = menu.addAction(self.myNameTH12, self.addWmsTH12)
        action.setObjectName(self.myNameTH12)

        self.loadTHActions = QAction("Thüringen", self.iface.mainWindow())
        self.loadTHActions.setMenu(menu)
        self.iface.addPluginToMenu(self.myPlugin, self.loadTHActions)
#===================================================================================

    def unload(self):
        self.iface.removePluginMenu(self.myPlugin, self.loadDTActions)
        self.iface.removePluginMenu(self.myPlugin, self.loadBBActions)
        self.iface.removePluginMenu(self.myPlugin, self.loadSTActions)
        self.iface.removePluginMenu(self.myPlugin, self.loadSNActions)
        self.iface.removePluginMenu(self.myPlugin, self.loadTHActions)

#===================================================================================

    # ------- DE - Deutschland ---------------------------
    
    def addWmsDE01(self):
        lyrDE01 = QgsRasterLayer(self.myUriDE01, self.myNameDE01, 'wms')
        if not lyrDE01.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameDE01 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrDE01)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameDE01 + self.myInfo_2, 3, 1)
            
    def addWmsDE02(self):
        lyrDE02 = QgsRasterLayer(self.myUriDE02, self.myNameDE02, 'wms')
        if not lyrDE02.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameDE02 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrDE02)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameDE02 + self.myInfo_2, 3, 1)
           
    def addWmsDE03(self):
        lyrDE03 = QgsRasterLayer(self.myUriDE03, self.myNameDE03, 'wms')
        if not lyrDE03.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameDE03 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrDE03)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameDE03 + self.myInfo_2, 3, 1)
           
    def addWmsDE04(self):
        lyrDE04 = QgsRasterLayer(self.myUriDE04, self.myNameDE04, 'wms')
        if not lyrDE04.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameDE04 + self.myCritical_2)        
        else:
            lyrDE04.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrDE04)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameDE04 + self.myInfo_2, 3, 1)

    # ------- BB - Brandenburg -------------------------------
    def addWmsBB01(self):
        lyrBB01 = QgsRasterLayer(self.myUriBB01, self.myNameBB01, 'wms')
        if not lyrBB01.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameBB01 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrBB01)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameBB01 + self.myInfo_2, 3, 1) 

    def addWmsBB02(self):
        lyrBB02 = QgsRasterLayer(self.myUriBB02, self.myNameBB02, 'wms')
        if not lyrBB02.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameBB02 + self.myCritical_2)        
        else:
            lyrBB02.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrBB02)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameBB02 + self.myInfo_2, 3, 1) 
            
    def addWmsBB03(self):
        myroot = QgsProject.instance().layerTreeRoot()
        mygroup = myroot.insertGroup(0, 'BB: ALKIS Tats. Nutzung (WMS)')
        
        lyrBB03a = QgsRasterLayer(self.myUriBB03a, self.myNameBB03a, 'wms')
        if not lyrBB03a.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameBB03a + self.myCritical_2)        
        else:
            lyrBB03a.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrBB03a, False)
            mygroup.addLayer(lyrBB03a)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameBB03a + self.myInfo_2, 3, 1)  
        
        lyrBB03b = QgsRasterLayer(self.myUriBB03b, self.myNameBB03b, 'wms')
        if not lyrBB03b.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameBB03b + self.myCritical_2)        
        else:
            lyrBB03b.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrBB03b, False)
            mygroup.addLayer(lyrBB03b)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameBB03b + self.myInfo_2, 3, 1)  
        
        lyrBB03c = QgsRasterLayer(self.myUriBB03c, self.myNameBB03c, 'wms')
        if not lyrBB03c.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameBB03c + self.myCritical_2)        
        else:
            lyrBB03c.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrBB03c, False)
            mygroup.addLayer(lyrBB03c)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameBB03c + self.myInfo_2, 3, 1)  
        
        lyrBB03d = QgsRasterLayer(self.myUriBB03d, self.myNameBB03d, 'wms')
        if not lyrBB03d.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameBB03d + self.myCritical_2)        
        else:
            lyrBB03d.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrBB03d, False)
            mygroup.addLayer(lyrBB03d)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameBB03d + self.myInfo_2, 3, 1)  
    
    def addWmsBB04(self):
        lyrBB04 = QgsRasterLayer(self.myUriBB04, self.myNameBB04, 'wms')
        if not lyrBB04.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameBB04 + self.myCritical_2)        
        else:
            lyrBB04.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrBB04)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameBB04 + self.myInfo_2, 3, 1)
        
    def addWmsBB12(self):
        self.addWmsBB03()
        self.addWmsBB02()
        self.addWmsBB01()

    # ------- SN - Sachsen -------------------------------
    def addWmsSN01(self):
        lyrSN01 = QgsRasterLayer(self.myUriSN01, self.myNameSN01, 'wms')
        if not lyrSN01.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameSN01 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrSN01)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameSN01 + self.myInfo_2, 3, 1) 

    def addWmsSN02(self):
        lyrSN02 = QgsRasterLayer(self.myUriSN02, self.myNameSN02, 'wms')
        if not lyrSN02.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameSN02 + self.myCritical_2)        
        else:
            lyrSN02.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrSN02)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameSN02 + self.myInfo_2, 3, 1) 
            
    def addWmsSN03(self):
        myroot = QgsProject.instance().layerTreeRoot()
        mygroup = myroot.insertGroup(0, 'SN: ALKIS Tats. Nutzung (WMS)')
        
        lyrSN03a = QgsRasterLayer(self.myUriSN03a, self.myNameSN03a, 'wms')
        if not lyrSN03a.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameSN03a + self.myCritical_2)        
        else:
            lyrSN03a.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrSN03a, False)
            mygroup.addLayer(lyrSN03a)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameSN03a + self.myInfo_2, 3, 1)  
        
        lyrSN03b = QgsRasterLayer(self.myUriSN03b, self.myNameSN03b, 'wms')
        if not lyrSN03b.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameSN03b + self.myCritical_2)        
        else:
            lyrSN03b.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrSN03b, False)
            mygroup.addLayer(lyrSN03b)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameSN03b + self.myInfo_2, 3, 1)  
        
        lyrSN03c = QgsRasterLayer(self.myUriSN03c, self.myNameSN03c, 'wms')
        if not lyrSN03c.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameSN03c + self.myCritical_2)        
        else:
            lyrSN03c.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrSN03c, False)
            mygroup.addLayer(lyrSN03c)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameSN03c + self.myInfo_2, 3, 1)  
        
        lyrSN03d = QgsRasterLayer(self.myUriSN03d, self.myNameSN03d, 'wms')
        if not lyrSN03d.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameSN03d + self.myCritical_2)        
        else:
            lyrSN03d.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrSN03d, False)
            mygroup.addLayer(lyrSN03d)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameSN03d + self.myInfo_2, 3, 1)  
            
    def addWmsSN12(self):
        self.addWmsSN03()
        self.addWmsSN02()
        self.addWmsSN01()
        
    def addWmsSN04(self):
        lyrSN04 = QgsRasterLayer(self.myUriSN04, self.myNameSN04, 'wms')
        if not lyrSN04.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameSN04 + self.myCritical_2)        
        else:
            lyrSN04.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrSN04)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameSN04 + self.myInfo_2, 3, 1)


    # ------- ST - Sachsen-Anhalt ------------------------
    def addWmsST01(self):
        lyrST01 = QgsRasterLayer(self.myUriST01, self.myNameST01, 'wms')
        if not lyrST01.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + name + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrST01)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST01 + self.myInfo_2, 3, 1) 
        
    def addWmsST02(self):
        lyrST02 = QgsRasterLayer(self.myUriST02, self.myNameST02, 'wms')
        if not lyrST02.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + name + self.myCritical_2)        
        else:
            lyrST02.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST02)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST02 + self.myInfo_2, 3, 1)
            
    def addWmsST03(self):
        myroot = QgsProject.instance().layerTreeRoot()
        mygroup = myroot.insertGroup(0, 'ST: ALKIS Tats. Nutzung (WMS)')
        
        lyrST03a = QgsRasterLayer(self.myUriST03a, self.myNameST03a, 'wms')
        if not lyrST03a.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST03a + self.myCritical_2)        
        else:
            lyrST03a.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST03a, False)
            mygroup.addLayer(lyrST03a)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST03a + self.myInfo_2, 3, 1)  
        
        lyrST03b = QgsRasterLayer(self.myUriST03b, self.myNameST03b, 'wms')
        if not lyrST03b.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST03b + self.myCritical_2)        
        else:
            lyrST03b.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST03b, False)
            mygroup.addLayer(lyrST03b)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST03b + self.myInfo_2, 3, 1)  
        
        lyrST03c = QgsRasterLayer(self.myUriST03c, self.myNameST03c, 'wms')
        if not lyrST03c.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST03c + self.myCritical_2)        
        else:
            lyrST03c.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST03c, False)
            mygroup.addLayer(lyrST03c)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST03c + self.myInfo_2, 3, 1)  
        
        lyrST03d = QgsRasterLayer(self.myUriST03d, self.myNameST03d, 'wms')
        if not lyrST03d.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST03d + self.myCritical_2)        
        else:
            lyrST03d.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST03d, False)
            mygroup.addLayer(lyrST03d)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST03d + self.myInfo_2, 3, 1)  

    def addWmsST12(self):
        self.addWmsST03()
        self.addWmsST02()
        self.addWmsST01()

    def addWmsST04(self):
        lyrST04 = QgsRasterLayer(self.myUriST04, self.myNameST04, 'wms')
        if not lyrST04.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST04 + self.myCritical_2)        
        else:
            lyrST04.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST04)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST04 + self.myInfo_2, 3, 1)

    def addWfsST05(self):
        lyrST05 = QgsVectorLayer(self.myUriST05, self.myNameST05, 'WFS')
        if not lyrST05.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + name + self.myCritical_2)        
        else:
            lyrST05.setOpacity(0.75) 
            lyrST05.setMinimumScale(25000.0)
            lyrST05.setMaximumScale(1.0)
            lyrST05.setScaleBasedVisibility(1)
            # Farbe ändern
            lyrST05.renderer().symbol().setColor(QColor("transparent"))
            lyrST05.renderer().symbol().symbolLayer(0).setStrokeColor(QColor("black"))
            lyrST05.renderer().symbol().symbolLayer(0).setStrokeWidth(0.3)
            lyrST05.triggerRepaint() #braucht es nur wenn schon geladen
            # Legende updaten
            iface.layerTreeView().refreshLayerSymbology(lyrST05.id())
            QgsProject.instance().addMapLayer(lyrST05)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST05 + self.myInfo_2, 3, 1)

    def addWfsST06(self):
        lyrST06 = QgsVectorLayer(self.myUriST06, self.myNameST06, 'WFS')
        if not lyrST06.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST06 + self.myCritical_2)        
        else:
            # Opazität ändern
            lyrST06.setOpacity(0.75)
            # Massstabsklassen/Sichtbarkeit ändern
            lyrST06.setMinimumScale(25000.0)
            lyrST06.setMaximumScale(1.0)
            lyrST06.setScaleBasedVisibility(1)
            # Farbe ändern
            lyrST06.renderer().symbol().setColor(QColor(220,220,220))
            lyrST06.renderer().symbol().symbolLayer(0).setStrokeColor(QColor("black"))
            lyrST06.renderer().symbol().symbolLayer(0).setStrokeWidth(0.1)
            lyrST06.triggerRepaint() #braucht es nur wenn schon geladen
            # Legende updaten
            iface.layerTreeView().refreshLayerSymbology(lyrST06.id())
            QgsProject.instance().addMapLayer(lyrST06)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST06 + self.myInfo_2, 3, 1)

    def addWmsST07(self):
        myroot = QgsProject.instance().layerTreeRoot()
        mygroup = myroot.insertGroup(0, self.myNameST07)
        lyrST07a = QgsRasterLayer(self.myUriST07a, self.myNameST07a, 'wms')
        if not lyrST07a.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST07 + self.myCritical_2)        
        else:
            lyrST07a.setMinimumScale(17500.0)
            lyrST07a.setMaximumScale(1.0)
            lyrST07a.setScaleBasedVisibility(1)
            lyrST07a.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST07a, False)
            mygroup.addLayer(lyrST07a) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST07 + self.myInfo_2, 3, 1)        

        lyrST07b = QgsRasterLayer(self.myUriST07b, self.myNameST07b, 'wms')
        if not lyrST07b.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST07 + self.myCritical_2)        
        else:
            lyrST07b.setMinimumScale(37500.0)
            lyrST07b.setMaximumScale(17500.0)
            lyrST07b.setScaleBasedVisibility(1)
            lyrST07b.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST07b, False)
            mygroup.addLayer(lyrST07b) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST07 + self.myInfo_2, 3, 1)        

        lyrST07c = QgsRasterLayer(self.myUriST07c, self.myNameST07c, 'wms')
        if not lyrST07c.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST07 + self.myCritical_2)        
        else:
            lyrST07c.setMinimumScale(75000.0)
            lyrST07c.setMaximumScale(37500.0)
            lyrST07c.setScaleBasedVisibility(1)
            lyrST07c.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST07c, False)
            mygroup.addLayer(lyrST07c) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST07 + self.myInfo_2, 3, 1)        

        lyrST07d = QgsRasterLayer(self.myUriST07d, self.myNameST07d, 'wms')
        if not lyrST07d.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST07 + self.myCritical_2)        
        else:
            lyrST07d.setMinimumScale(175000.0)
            lyrST07d.setMaximumScale(75000.0)
            lyrST07d.setScaleBasedVisibility(1)
            lyrST07d.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST07d, False)
            mygroup.addLayer(lyrST07d) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST07 + self.myInfo_2, 3, 1)        

        lyrST07e = QgsRasterLayer(self.myUriST07e, self.myNameST07e, 'wms')
        if not lyrST07e.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST07 + self.myCritical_2)        
        else:
            lyrST07e.setMinimumScale(5000000.0)
            lyrST07e.setMaximumScale(175000.0)
            lyrST07e.setScaleBasedVisibility(1)
            lyrST07e.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST07e, False)
            mygroup.addLayer(lyrST07e) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST07 + self.myInfo_2, 3, 1)

    def addWmsST08(self):
        myroot = QgsProject.instance().layerTreeRoot()
        mygroup = myroot.insertGroup(0, self.myNameST08)
        lyrST08a = QgsRasterLayer(self.myUriST08a, self.myNameST08a, 'wms')
        if not lyrST08a.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST08 + self.myCritical_2)        
        else:
            lyrST08a.setMinimumScale(17500.0)
            lyrST08a.setMaximumScale(1.0)
            lyrST08a.setScaleBasedVisibility(1)
            lyrST08a.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST08a, False)
            mygroup.addLayer(lyrST08a) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST08 + self.myInfo_2, 3, 1)        

        lyrST08b = QgsRasterLayer(self.myUriST08b, self.myNameST08b, 'wms')
        if not lyrST08b.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST08 + self.myCritical_2)        
        else:
            lyrST08b.setMinimumScale(37500.0)
            lyrST08b.setMaximumScale(17500.0)
            lyrST08b.setScaleBasedVisibility(1)
            lyrST08b.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST08b, False)
            mygroup.addLayer(lyrST08b) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST08 + self.myInfo_2, 3, 1)        

        lyrST08c = QgsRasterLayer(self.myUriST08c, self.myNameST08c, 'wms')
        if not lyrST08c.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST08 + self.myCritical_2)        
        else:
            lyrST08c.setMinimumScale(75000.0)
            lyrST08c.setMaximumScale(37500.0)
            lyrST08c.setScaleBasedVisibility(1)
            lyrST08c.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST08c, False)
            mygroup.addLayer(lyrST08c) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST08 + self.myInfo_2, 3, 1)        

        lyrST08d = QgsRasterLayer(self.myUriST08d, self.myNameST08d, 'wms')
        if not lyrST08d.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST08 + self.myCritical_2)        
        else:
            lyrST08d.setMinimumScale(175000.0)
            lyrST08d.setMaximumScale(75000.0)
            lyrST08d.setScaleBasedVisibility(1)
            lyrST08d.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST08d, False)
            mygroup.addLayer(lyrST08d) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST08 + self.myInfo_2, 3, 1)        

        lyrST08e = QgsRasterLayer(self.myUriST08e, self.myNameST08e, 'wms')
        if not lyrST08e.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST08 + self.myCritical_2)        
        else:
            lyrST08e.setMinimumScale(5000000.0)
            lyrST08e.setMaximumScale(175000.0)
            lyrST08e.setScaleBasedVisibility(1)
            lyrST08e.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST08e, False)
            mygroup.addLayer(lyrST08e) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST08 + self.myInfo_2, 3, 1)

    def addWmsST09(self):
        lyrST90 = QgsRasterLayer(self.myUriST09, self.myNameST09, 'wms')
        if not lyrST90.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST09 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrST90) 
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST09 + self.myInfo_2, 3, 1)   

    def addWmsST10(self):
        lyrST10 = QgsRasterLayer(self.myUriST10, self.myNameST10, 'wms')
        if not lyrST10.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST10 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrST10)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST10 + self.myInfo_2, 3, 1)

    def addWmsST11(self):
        lyrST11 = QgsRasterLayer(self.myUriST11, self.myNameST11, 'wms')
        if not lyrST11.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameST11 + self.myCritical_2)        
        else:
            lyrST11.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrST11)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameST11 + self.myInfo_2, 3, 1)
            
    # ------- TH - Thüringen ------------------------
    def addWmsTH01(self):
        lyrTH01 = QgsRasterLayer(self.myUriTH01, self.myNameTH01, 'wms')
        if not lyrTH01.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameTH01 + self.myCritical_2)        
        else:
            QgsProject.instance().addMapLayer(lyrTH01)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameTH01 + self.myInfo_2, 3, 1) 

    def addWmsTH02(self):
        lyrTH02 = QgsRasterLayer(self.myUriTH02, self.myNameTH02, 'wms')
        if not lyrTH02.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameTH02 + self.myCritical_2)        
        else:
            lyrTH02.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrTH02)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameTH02 + self.myInfo_2, 3, 1) 

    def addWmsTH03(self):
        myroot = QgsProject.instance().layerTreeRoot()
        mygroup = myroot.insertGroup(0, 'TH: ALKIS Tats. Nutzung (WMS)')
        
        lyrTH03a = QgsRasterLayer(self.myUriTH03a, self.myNameTH03a, 'wms')
        if not lyrTH03a.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameTH03a + self.myCritical_2)        
        else:
            lyrTH03a.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrTH03a, False)
            mygroup.addLayer(lyrTH03a)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameTH03a + self.myInfo_2, 3, 1)  
        
        lyrTH03b = QgsRasterLayer(self.myUriTH03b, self.myNameTH03b, 'wms')
        if not lyrTH03b.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameTH03b + self.myCritical_2)        
        else:
            lyrTH03b.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrTH03b, False)
            mygroup.addLayer(lyrTH03b)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameTH03b + self.myInfo_2, 3, 1)  
        
        lyrTH03c = QgsRasterLayer(self.myUriTH03c, self.myNameTH03c, 'wms')
        if not lyrTH03c.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameTH03c + self.myCritical_2)        
        else:
            lyrTH03c.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrTH03c, False)
            mygroup.addLayer(lyrTH03c)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameTH03c + self.myInfo_2, 3, 1)  
        
        lyrTH03d = QgsRasterLayer(self.myUriTH03d, self.myNameTH03d, 'wms')
        if not lyrTH03d.isValid():
            iface.messageBar().pushCritical(self.myPluginV, self.myCritical_1 + self.myNameTH03d + self.myCritical_2)        
        else:
            lyrTH03d.renderer().setOpacity(0.75)
            QgsProject.instance().addMapLayer(lyrTH03d, False)
            mygroup.addLayer(lyrTH03d)
            iface.messageBar().pushMessage(self.myPluginV, self.myInfo_1 + self.myNameTH03d + self.myInfo_2, 3, 1)  

    def addWmsTH12(self):       # ALKIS: Flurstücke, Gebäude, Nutzung zusammen
        self.addWmsTH03()
        self.addWmsTH02()
        self.addWmsTH01()
        
#    def open_website():
#        webbrowser.open(u'https://geoobserver.de')
            
# ------ Offene ------------------------

#Baden-Württemberg	BW
#Bayern (Freistaat)	BY
#Berlin	BE
#Bremen (Hansestadt)	HB
#Hamburg (Hansestadt)	HH
#Hessen	HE
#Mecklenburg-Vorpommern	MV
#Niedersachsen	NI
#Nordrhein-Westfalen	NW
#Rheinland-Pfalz	RP
#Saarland	SL
#Schleswig-Holstein	SH



