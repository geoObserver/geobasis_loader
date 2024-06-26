defaultWMSSettings = 'format=image/png&dpiMode=7&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&Request=GetMap&Version=1.3.0&'
utm32 = 'crs=EPSG:25832&'
utm33 = 'crs=EPSG:25833&'

# Parameter pro Ebene:
#
# seperator: True | False ; Standard False => Wenn True ist unter dem Menüpunkt ein Trennbalken
# name: String ; NÖTIG => Name der Ebene im Ebenenbaum
# uri: String ; NÖTIG => Die URI der Ebene
# type: 'wms' | 'wfs' ; Standard wms => Typ der Ebene. Nur angeben wenn es eine WFS-Ebene ist
# opacity: 0 - 1 ; Standard 1 => Die Sichtbarkeit der Ebene
# minScale: Float | Int ; Standard NULL (bei WFS 25000) => Kleinster Maßstab der Ebene
# maxScale: Float | Int ; Standard NULL (bei WFS 1) => Größter Maßstab der Ebene
# 
# ---- Für WFS ---------------
# fillColor: Tuple | String ; Standard (220,220,220) => Farbe der Features
# strokeColor: Tuple | String ; Standard "black" => Farbe des Rands
# strokeWidth: Float ; Standard 0.3 => Strichbreite des Rands

services = {
  'de': {   # ----------- deutschland -------------------------------------------------------------------------
    'bundeslandname': 'Deutschland',
    'themen': {
      'osm': {
        'name': 'OSM: OpenStreetMap (XYZ)',
        'uri': '&type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0',
        'seperator': True,
      },
      'grau': {
        'name': 'DE: basemap.de grau (WMS)',
        'uri': f'crs=EPSG:3857&{defaultWMSSettings}layers=de_basemapde_web_raster_grau&styles&url=https://sgx.geodatenzentrum.de/wms_basemapde?',
      },
      'farbig': {
        'name': 'DE: basemap.de farbig (WMS)',
        'uri': f'crs=EPSG:3857&{defaultWMSSettings}layers=de_basemapde_web_raster_farbe&styles&url=https://sgx.geodatenzentrum.de/wms_basemapde?',
        'seperator': True,
      },
        'grau-wfs': {
            'name': 'DE: basemap.de grau (WFS)', 
            'uri': '&type=xyz&styleUrl=https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_gry.json&zmin=0&zmax=20&url=https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/tiles/v1/bm_web_de_3857/{z}/{x}/{y}.pbf',
            'type': "vectorTiles"
        },
        'farbig-wfs': {
            'name': 'DE: basemap.de farbig (WFS)',
            'uri': '&type=xyz&styleUrl=https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/styles/bm_web_col.json&zmin=0&zmax=20&url=https://sgx.geodatenzentrum.de/gdz_basemapde_vektor/tiles/v1/bm_web_de_3857/{z}/{x}/{y}.pbf',
            'type': "vectorTiles",
            'seperator': True,
        },
         'verwaltung': {
        'name': 'DE: Verwaltungsgebiete 1:2 500 000 (WMS)',
        'uri': f'crs=EPSG:25832&{defaultWMSSettings}layers=vg2500_lan&styles&url=https://sgx.geodatenzentrum.de/wms_vg2500',
        'opacity': 0.75,
      }
    }
  },
  'be': {   # ----------- berlin -------------------------------------------------------------------------
    'bundeslandname': 'Berlin',
    'themen': {
      "flurstuecke":{
        "name":"BE: ALKIS Flurstücke (WMS)",
        "uri": f"{utm33}{defaultWMSSettings}&url=https://fbinter.stadt-berlin.de/fb/wms/senstadt/wmsk_alkis&layers=25&layers=28&styles=&styles="
      },
      "gebaeude":{
        "name":"BE: ALKIS Gebäude (WMS)",
        "uri": f"{utm33}{defaultWMSSettings}&url=https://fbinter.stadt-berlin.de/fb/wms/senstadt/wmsk_alkis&layers=9&layers=12&styles=&styles=",
      },
      "nutzung":{
        "name":"BE: ALKIS Tatsächliche Nutzung (WMS)",
        "uri": f"{utm33}{defaultWMSSettings}&url=https://fbinter.stadt-berlin.de/fb/wms/senstadt/wmsk_alkis&layers=5&layers=7&styles=&styles=",
      },
      "alkis_alles": {
        "name": "BE: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"BE: Bodenrichtwerte Bauland 2024 (WMS)",
        "uri": f"{utm33}{defaultWMSSettings}&url=https://fbinter.stadt-berlin.de/fb/wms/senstadt/brw_2024_amtlich&layers=2&layers=3&styles=&styles=",
        "seperator": True,
        "opacity": 0.75,
      },
      "flustuecke_wfs":{
        "name":"BE: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='fis:s_wfs_alkis' url='https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_wfs_alkis' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"BE: ALKIS Gebäude (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='fis:s_wfs_alkis_gebaeudeflaechen' url='https://fbinter.stadt-berlin.de/fb/wfs/data/senstadt/s_wfs_alkis_gebaeudeflaechen' version='auto'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },
      "tk_farbig_layergroup":{
        "name":"BE: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_10_farbig": {
            "name":"BE: TK 10 farbig (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=0&styles&url=https://fbinter.stadt-berlin.de/fb/wms/senstadt/k_dtk10",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"BE: TK 25 farbig (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=dtk25_col&styles&url=https://gdi.berlin.de/services/wms/dtk25",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"BE: TK 50 farbig (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=dtk50_col&styles&url=https://gdi.berlin.de/services/wms/dtk50",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"BE: TK 100 farbig (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=dtk100_col&styles&url=https://gdi.berlin.de/services/wms/dtk100",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
      },
      "tk_grau_layergroup": {
        "name": "BE: Topograf. Karten grau (WMS)",
        "layers": {
          "tk_10_grau":{
            "name":"BE: TK 10 grau (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=1&styles&url=https://fbinter.stadt-berlin.de/fb/wms/senstadt/k_dtk10",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_grau":{
            "name":"BE: TK 25 grau (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=dtk25_bcgr&styles&url=https://gdi.berlin.de/services/wms/dtk25",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_grau":{
            "name":"BE: TK 50 grau (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=dtk50_bcgr&styles&url=https://gdi.berlin.de/services/wms/dtk50",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_grau":{
            "name":"BE: TK 100 grau (WMS)",
            "uri": f"{utm33}{defaultWMSSettings}layers=dtk100_bcgr&styles&url=https://gdi.berlin.de/services/wms/dtk100",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
        "seperator": True
      },
      "dop20":{
        "name":"BE: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm33}{defaultWMSSettings}layers=truedop_2023&styles&url=https://gdi.berlin.de/services/wms/truedop_2023",
        "seperator": True,
      }
    }
  },
  'by': {   # ----------- bayern -------------------------------------------------------------------------
    'bundeslandname': 'Bayern',
    'themen': {
      "webkarte_farbig":{
        "name":"BY: Webkarte farbig (WMTS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=by_webkarte&styles=default&tileMatrixSet=adv_utm32&url=https://geoservices.bayern.de/od/wmts/geobasis/v1/1.0.0/WMTSCapabilities.xml",
      },
      "webkarte_grau":{
        "name":"BY: Webkarte grau (WMTS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=by_webkarte_grau&styles=default&tileMatrixSet=adv_utm32&url=https://geoservices.bayern.de/od/wmts/geobasis/v1/1.0.0/WMTSCapabilities.xml",
        "seperator": True,
      },
      "TK":{
        "name":"BY: Topograf. Karte (WMTS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=by_amtl_karte&styles=default&tileMatrixSet=adv_utm32&url=https://geoservices.bayern.de/od/wmts/geobasis/v1/1.0.0/WMTSCapabilities.xml",
        "seperator": True,
      },
      "dop20":{
        "name":"BY: Digitale Orthophotos - DOP30 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}format=image/jpeg&layers=by_dop&styles=default&tileMatrixSet=adv_utm32&url=https://geoservices.bayern.de/od/wmts/geobasis/v1/1.0.0/WMTSCapabilities.xml",
      }
    }
  },
  'bb': {   # ----------- brandenburg -------------------------------------------------------------------------
    'bundeslandname': 'Brandenburg',
    'themen': {
      "flurstuecke":{
        "name":"BB: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_flurstuecke&styles=Farbe&url=https://isk.geobasis-bb.de/ows/alkis_wms",
      },
      "gebaeude":{
        "name":"BB: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gebaeude&styles=Farbe&url=https://isk.geobasis-bb.de/ows/alkis_wms",
      },
      "nutzung_layergroup": {
        "name": "BB: ALKIS Tatsächliche Nutzung (WMS)",
        "layers": {
          "gewaesser":{
            "name":"Gewässer",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gewaesser&styles=Farbe&url=https://isk.geobasis-bb.de/ows/alkis_wms",
            "opacity": 0.75,
          },
          "siedlung":{
            "name":"Siedlung",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_siedlung&styles=Farbe&url=https://isk.geobasis-bb.de/ows/alkis_wms",
            "opacity": 0.75,
          },
          "vegetation":{
            "name":"Vegetation",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_vegetation&styles=Farbe&url=https://isk.geobasis-bb.de/ows/alkis_wms",
            "opacity": 0.75,
          },
          "verkehr":{
            "name":"Verkehr",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_verkehr&styles=Farbe&url=https://isk.geobasis-bb.de/ows/alkis_wms",
            "opacity": 0.75,
          }
        }
      },
      "alkis_alles": {
        "name": "BB: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung_layergroup", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"BB: Bodenrichtwerte Bauland 2024 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=bbv_pg_zobau_2024&styles&url=https://isk.geobasis-bb.de/ows/brw_wms",
        "seperator": True,
        "opacity": 0.75,
      },
      "flustuecke_wfs":{
        "name":"BB: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='ave:Flurstueck' url='https://isk.geobasis-bb.de/ows/alkis_vereinf_wfs' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"BB: ALKIS Gebäude (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='ave:GebaeudeBauwerk' url='https://isk.geobasis-bb.de/ows/alkis_vereinf_wfs' version='auto'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },
      "tk_farbig_layergroup":{
        "name":"BB: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_10_farbig": {
            "name":"BB: TK 10 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk10_farbe&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk10farbe/service/wms",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"BB: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk25_farbe&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk25farbe/service/wms",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"BB: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk50_farbe&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk50farbe/service/wms",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"BB: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk100_farbe&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk100farbe/service/wms",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
      },
      "tk_grau_layergroup": {
        "name": "BB: Topograf. Karten grau (WMS)",
        "layers": {
          "tk_10_grau":{
            "name":"BB: TK 10 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk10_grau&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk10grau/service/wms",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_grau":{
            "name":"BB: TK 25 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk25_grau&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk25grau/service/wms",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_grau":{
            "name":"BB: TK 50 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk50_grau&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk50grau/service/wms",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_grau":{
            "name":"BB: TK 100 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=bb_dtk100_grau&styles&url=https://isk.geobasis-bb.de/mapproxy/dtk100grau/service/wms",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
        "seperator": True
      },
      "dop20":{
        "name":"BB: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=bebb_dop20c&styles&url=https://isk.geobasis-bb.de/mapproxy/dop20c/service/wms",
        "seperator": True,
      }
    }
  },
  'hb': {   # ----------- bremen -------------------------------------------------------------------------
    'bundeslandname': 'Bremen',
    'themen': {
      "dop20hb":{
        "name":"HB: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=DOP20_2023_HB&styles&url=https://geodienste.bremen.de/wms_dop20_2023?VERSION%3D1.3.0",
      },
      "dop20bhv":{
        "name":"BHV: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=DOP20_2023_BHV&styles&url=https://geodienste.bremen.de/wms_dop20_2023?VERSION%3D1.3.0",
      }
    }
  },
  'hh': {   # ----------- hamburg -------------------------------------------------------------------------
    'bundeslandname': 'Hamburg',
    'themen': {
      "flurstuecke":{
        "name":"HH: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&url=https://geodienste.hamburg.de/HH_WMS_ALKIS_Basiskarte&layers=19&layers=21&layers=24&layers=30&layers=36&styles=&styles=&styles=&styles=&styles="
      },
      "gebaeude":{
        "name":"HH: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&url=https://geodienste.hamburg.de/HH_WMS_ALKIS_Basiskarte&layers=14&layers=15&layers=8&layers=29&layers=35&layers=26&layers=27&layers=32&layers=33&layers=34&layers=28&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=",
      },
      "nutzung":{
        "name":"HH: ALKIS Tatsächliche Nutzung (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&url=https://geodienste.hamburg.de/HH_WMS_ALKIS_Basiskarte&layers=0&layers=1&layers=4&layers=6&styles=&styles=&styles=&styles=",
      },
      "alkis_alles": {
        "name": "HH: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "brw_layergroup":{
        "name":"HH: Bodenrichtwerte (WMS)",
        "layers": {
          "brw_1": {
            "name":"HH: BRW Einfamilienhäuser (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=brw_uek_efh&styles&url=https://geodienste.hamburg.de/HH_WMS_UEKnormierteBodenrichtwerte",
            "opacity": 0.75
          },
          "brw_2": {
            "name":"HH: BRW Mehfamilienhäuser (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=brw_uek_mfh&styles&url=https://geodienste.hamburg.de/HH_WMS_UEKnormierteBodenrichtwerte",
            "opacity": 0.75
          },
          "brw_3": {
            "name":"HH: BRW Läden (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=brw_uek_gh&styles&url=https://geodienste.hamburg.de/HH_WMS_UEKnormierteBodenrichtwerte",
            "opacity": 0.75
          },
          "brw_4": {
            "name":"HH: BRW Bürohäuser (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=brw_uek_bh&styles&url=https://geodienste.hamburg.de/HH_WMS_UEKnormierteBodenrichtwerte",
            "opacity": 0.75
          },
          "brw_5": {
            "name":"HH: BRW Produktion und Logistik (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=brw_uek_pl&styles&url=https://geodienste.hamburg.de/HH_WMS_UEKnormierteBodenrichtwerte",
            "opacity": 0.75
          },
        },
        "seperator": True
      },
      "flustuecke_wfs":{
        "name":"HH: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:Flurstueck' url='https://geodienste.hamburg.de/WFS_HH_ALKIS_vereinfacht' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"HH: ALKIS Gebäude (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:GebaeudeBauwerk' url='https://geodienste.hamburg.de/WFS_HH_ALKIS_vereinfacht' version='auto'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },

      "dk5":{
        "name":"HH: Topograf. Karte farbig DK5 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&layers=DK5&styles&url=https://geodienste.hamburg.de/HH_WMS_DK5",
        "seperator": True
      },
      "dop15":{
        "name":"HH: Digitale Orthophotos - DOP15 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=dop_rgb_0_5000&styles&url=https://geodienste.hamburg.de/HH_WMS_DOP",
      },
      "dop100":{
        "name":"HH: Digitale Orthophotos - DOP100(WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&layers=dop_rgb_downscale&styles&url=https://geodienste.hamburg.de/HH_WMS_DOP",
        "seperator": True,
      }
    }
  },
  'he': {   # ----------- hessen -------------------------------------------------------------------------
    'bundeslandname': 'Hessen',
    'themen': {
      "flurstuecke":{
        "name":"HE: ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=he_alk&styles&url=https://www.geoportal.hessen.de/mapbender/php/wms.php?inspire%3D1%26layer_id%3D52063%26withChilds%3D1",
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"HE: Bodenrichtwerte Bauland 2024 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}url=https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-maps.ows?language%3Dger%26VERSION%3D1.3.0&layers=hboris_feature&layers=hboris_label&styles=&styles=",
        "seperator": True,
        "opacity": 0.75,
      },
      "flustuecke_wfs":{
        "name":"HE: ALKIS Flurstücke (WFS)",
        "uri":"pageSize='10000' pagingEnabled='disabled' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:Flurstueck' url='https://www.gds.hessen.de/wfs2/aaa-suite/cgi-bin/alkis/vereinf/wfs' version='1.0.0'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"HE: ALKIS Gebäude (WFS)",
        "uri":"pageSize='10000' pagingEnabled='disabled' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:GebaeudeBauwerk' url='https://www.gds.hessen.de/wfs2/aaa-suite/cgi-bin/alkis/vereinf/wfs' version='1.0.0'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },
      "tk_farbig_layergroup":{
        "name":"HE: Topograf. Karten farbig (WMS)",
        "layers": {
#          "tk_10_farbig": {
#            "name":"HE: TK 10 farbig (WMS)",
#            "uri": f"{utm32}{defaultWMSSettings}layers=he_dtk&styles&url=https://www.geoportal.hessen.de/mapbender/php/wms.php?inspire%3D1%26layer_id%3D52113%26withChilds%3D1",
#            "opacity": 0.75,
#            "minScale": 17500.0,
#            "maxScale": 1
#          },
          "tk_25_farbig":{
            "name":"HE: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=he_dtk25&styles&url=https://www.geoportal.hessen.de/mapbender/php/wms.php?inspire%3D1%26layer_id%3D52068%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 1.0
          },
          "tk_50_farbig":{
            "name":"HE: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=he_dtk50&styles&url=https://www.geoportal.hessen.de/mapbender/php/wms.php?inspire%3D1%26layer_id%3D52085%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"HE: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=he_dtk100&styles&url=https://www.geoportal.hessen.de/mapbender/php/wms.php?inspire%3D1%26layer_id%3D52092%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
      },
      "pg_4_100":{
        "name":"HE: Präsentationsgrafik - PG4 ... PG100 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}url=https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-maps.ows?language%3Dger%26VERSION%3D1.3.0&layers=he_pg4&layers=he_pg10&layers=he_pg100&layers=he_pg50&layers=he_pg25&styles=&styles=&styles=&styles=&styles=",
        "seperator": True,
      },
      "dop20":{
        "name":"HE: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=he_dop_rgb&styles&url=https://www.geoportal.hessen.de/mapbender/php/wms.php?inspire%3D1%26layer_id%3D52123%26withChilds%3D1",
        #"minScale": 25000.0,
        #"maxScale": 1.0,
        "seperator": True
      }
    }
  },
  'mv': {   # ----------- Mecklenburg-Vorpommern -------------------------------------------------------------------------
  #&layers=adv_alkis_tatsaechliche_nutzung&styles=Farbe&url=https://www.geodaten-mv.de/dienste/alkis_wms
    'bundeslandname': 'Mecklenburg-Vorpommern',
    'themen': {
      "flurstuecke":{
        "name":"MV: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_flurstuecke&styles&url=https://www.geodaten-mv.de/dienste/alkis_wms",
      },
      "gebaeude":{
        "name":"MV: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gebaeude&styles&url=https://www.geodaten-mv.de/dienste/alkis_wms",
      },
      "nutzung":{
        "name":"MV: ALKIS Tatsächliche Nutzung (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_tatsaechliche_nutzung&styles=Farbe&url=https://www.geodaten-mv.de/dienste/alkis_wms",
      },
      "alkis_alles": {
        "name": "MV: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"MV: Bodenrichtwerte Bauland 2024 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}	&url=https://www.geodaten-mv.de/dienste/bodenrichtwerte_wms&layers=wohnbauflaeche&layers=sonderbauflaeche&layers=gemischte_bauflaeche&layers=gewerbliche_bauflaeche&layers=bebaute_flaeche_im_aussenbereich&styles=&styles=&styles=&styles=&styles=",
        "seperator": True,
        "opacity": 0.75,
      },
      "flurstuecke_wfs":{
        "name":"MV: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='cp:CadastralParcel' url='https://www.geodaten-mv.de/dienste/inspire_cp_alkis_download' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
        "seperator": True,
      },
      "tk_farbig_layergroup":{
        "name":"MV: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_10_farbig": {
            "name":"MV: TK 10 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk10&styles=palette_rgb&url=https://www.geodaten-mv.de/dienste/adv_dtk10",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"MV: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk25&styles=palette_rgb&url=https://www.geodaten-mv.de/dienste/adv_dtk25",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"MV: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk50&styles=palette_rgb&url=https://www.geodaten-mv.de/dienste/adv_dtk50",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"MV: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk100&styles=palette_rgb&url=https://www.geodaten-mv.de/dienste/adv_dtk100",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
      },
      "tk_grau_layergroup":{
        "name":"MV: Topograf. Karten grau (WMS)",
        "layers": {
          "tk_10_grau": {
            "name":"MV: TK 10 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk10&styles=palette_grau&url=https://www.geodaten-mv.de/dienste/adv_dtk10",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_grau":{
            "name":"MV: TK 25 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk25&styles=palette_grau&url=https://www.geodaten-mv.de/dienste/adv_dtk25",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_grau":{
            "name":"MV: TK 50 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk50&styles=palette_grau&url=https://www.geodaten-mv.de/dienste/adv_dtk50",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_grau":{
            "name":"MV: TK 100 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=mv_dtk100&styles=palette_grau&url=https://www.geodaten-mv.de/dienste/adv_dtk100",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
        "seperator": True
      },
      "dop10":{
        "name":"MV: Digitale Orthophotos - DOP10 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=mv_dop&styles=palette_rgb&url=https://www.geodaten-mv.de/dienste/adv_dop",
      },
    }
  },
  'ni': {   # ----------- niedersachsen -------------------------------------------------------------------------
    'bundeslandname': 'Niedersachsen',
    'themen': {
      "dop20":{
        "name":"NI: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=dop20&styles&url=https://www.geobasisdaten.niedersachsen.de/doorman/noauth/wms_ni_dop",
      },
    }
  },
  'nw': {   # ----------- nordrhein-westfalen -------------------------------------------------------------------------
    'bundeslandname': 'Nordrhein-Westfalen',
    'themen': {
      "flurstuecke":{
        "name":"NW: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_flurstuecke&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_alkis",
      },
      "gebaeude":{
        "name":"NW: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gebaeude&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_alkis",
      },
      "nutzung_layergroup": {
        "name": "NW: ALKIS Tatsächliche Nutzung (WMS)",
        "layers": {
          "verkehr":{
            "name":"Verkehr",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_verkehr&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_alkis",
            "opacity": 0.75,
          },
          "gewaesser":{
            "name":"Gewässer",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gewaesser&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_alkis",
            "opacity": 0.75,
          },
          "siedlung":{
            "name":"Siedlung",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_siedlung&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_alkis",
            "opacity": 0.75,
          },
          "vegetation":{
            "name":"Vegetation",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_vegetation&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_alkis",
            "opacity": 0.75,
          }
        }
      },
      "alkis_alles": {
        "name": "NW: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung_layergroup", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"NW: Bodenrichtwerte (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&url=https://www.wms.nrw.de/boris/wms_nw_brw&layers=0&layers=2&layers=3&layers=5&layers=6&layers=8&layers=9&layers=11&layers=12&layers=14&layers=15&layers=17&layers=18&layers=20&layers=21&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=&styles=",
        "seperator": True,
        "opacity": 0.75,
      },
      "flustuecke_wfs":{
        "name":"NW: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:Flurstueck' url='https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_vereinfacht' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"NW: ALKIS Gebäude (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:GebaeudeBauwerk' url='https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_vereinfacht' version='auto'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },
      "tk_farbig_layergroup":{
        "name":"NW: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_10_farbig": {
            "name":"NW: TK 10 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk10_col&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk10",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"NW: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk25_col&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk25",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"NW: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk50_col&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk50",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"NW: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk100_col&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk100",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
      },
      "tk_grau_layergroup":{
        "name":"NW: Topograf. Karten grau/sw (WMS)",
        "layers": {
          "tk_10_grau": {
            "name":"NW: TK 10 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk10_pan&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk10",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_grau":{
            "name":"NW: TK 25 sw (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk25_sw&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk25",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_grau":{
            "name":"NW: TK 50 sw (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk50_sw&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk50",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_grau":{
            "name":"NW: TK 100 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=nw_dtk100_pan&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dtk100",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
        "seperator": True,
      },
      "dop20":{
        "name":"NW: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=nw_dop_rgb&styles&url=https://www.wms.nrw.de/geobasis/wms_nw_dop",
      }
    }
  },
  'rp': {   # ----------- Rheinland-Pfalz -------------------------------------------------------------------------
    'bundeslandname': 'Rheinland-Pfalz',
    'themen': {
      "flurstuecke":{
        "name":"RP: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=Flurstueck&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61680%26withChilds%3D1%26VERSION%3D1.1.1",
      },
      "gebaeude":{
        "name":"RP: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=GebaeudeBauwerke&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61680%26withChilds%3D1%26VERSION%3D1.1.1",
      },
      "nutzung":{
        "name":"RP: ALKIS Tatsächliche Nutzung (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=Nutzung&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61680%26withChilds%3D1%26VERSION%3D1.1.1",
      },      
      "alkis_alles": {
        "name": "RP: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "tk_farbig_layergroup":{
        "name":"RP: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_10_farbig": {
            "name":"RP: TK 5 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk5&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D24142%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"RP: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk25&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61671%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"RP: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk50&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61696%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"RP: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk100&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61694%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
      },
      "tk_grau_layergroup":{
        "name":"RP: Topograf. Karten grau/sw (WMS)",
        "layers": {
          "tk_10_grau": {
            "name":"RP: TK 5 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk5_grau&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D24142%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_grau":{
            "name":"RP: TK 25 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk25_grau&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61671%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_grau":{
            "name":"RP: TK 50 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk50_grau&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61696%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_grau":{
            "name":"RP: TK 100 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=rp_dtk100_grau&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61694%26VERSION%3D1.1.1%26withChilds%3D1",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
        "seperator": True,
      },
      "dop40":{
        "name":"RP: Digitale Orthophotos - DOP40 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=rp_dop40&styles&url=https://www.geoportal.rlp.de/mapbender/php/wms.php?layer_id%3D61675%26VERSION%3D1.1.1%26withChilds%3D1",
      }
    }
  },
  'sn': {   # ----------- sachsen -------------------------------------------------------------------------
    'bundeslandname': 'Sachsen',
    'themen': {
      "flurstuecke":{
        "name":"SN: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_flurstuecke&styles&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest",
      },
      "gebaeude":{
        "name":"SN: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gebaeude&styles&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest",
      },
      "nutzung_layergroup": {
        "name": "SN: ALKIS Tatsächliche Nutzung (WMS)",
        "layers": {
          "gewaesser":{
            "name":"Gewässer",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gewaesser&styles&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest",
            "opacity": 0.75,
          },
          "siedlung":{
            "name":"Siedlung",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_siedlung&styles&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest",
            "opacity": 0.75,
          },
          "vegetation":{
            "name":"Vegetation",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_vegetation&styles&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest",
            "opacity": 0.75,
          },
          "verkehr":{
            "name":"Verkehr",
            "uri": f"{utm32}{defaultWMSSettings}&layers=adv_alkis_verkehr&styles&url=https://geodienste.sachsen.de/wms_geosn_alkis-adv/guest",
            "opacity": 0.75,
          }
        }
      },
      "alkis_alles": {
        "name": "SN: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung_layergroup", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"SN: Bodenrichtwerte Bauland 2024 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&layers=brw_akt&styles&url=https://www.landesvermessung.sachsen.de/fp/http-proxy/svc?cfg%3Dboris",
        "seperator": True,
        "opacity": 0.75,
      },
      "flustuecke_wfs":{
        "name":"SN: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='ave:Flurstueck' url='https://geodienste.sachsen.de/aaa/public_alkis/vereinf/wfs' url='https://geodienste.sachsen.de/aaa/public_alkis/vereinf/wfs?VERSION=1.1.0' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"SN: ALKIS Gebäude (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='ave:GebaeudeBauwerk' url='https://geodienste.sachsen.de/aaa/public_alkis/vereinf/wfs' url='https://geodienste.sachsen.de/aaa/public_alkis/vereinf/wfs?VERSION=1.1.0' version='auto'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },
      "dtk farbe":{
        "name":"SN: Topograf. Karten farbig (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=sn_dtk_pg_color&styles&url=https://geodienste.sachsen.de/wms_geosn_dtk-pg-color/guest",
        "opacity": 0.75,
      },
      "dtk grau":{
        "name":"SN: Topograf. Karten grau (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=sn_dtk_pg_grau&styles&url=https://geodienste.sachsen.de/wms_geosn_dtk-pg-grau/guest",
        "seperator": True,
        "opacity": 0.75,
      },
      "dop20":{
        "name":"SN: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}&layers=sn_dop_020&styles&tilePixelRatio=0&url=https://geodienste.sachsen.de/wms_geosn_dop-rgb/guest?VERSION%3D1.3.0t",
      },
    }
  },
  'st': {   # ----------- sachsen-anhalt -------------------------------------------------------------------------
    'bundeslandname': 'Sachsen-Anhalt',
    'themen': {
      "flurstuecke_wms":{
        "name":"ST: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_flurstuecke&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest",
      },
      "gebaeude_wms":{
        "name":"ST: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gebaeude&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest",
        "opacity": 0.75,
      },
      "nutzung_layergroup": {
        "name": "ST: ALKIS Tats. Nutzung (WMS)",
        "layers": {
          "gewaesser":{
            "name":"Gewässer",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gewaesser&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest",
            "opacity": 0.75,
          },
          "siedlung":{
            "name":"Siedlung",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_siedlung&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest",
            "opacity": 0.75,
          },
          "vegetation":{
            "name":"Vegetation",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_vegetation&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest",
            "opacity": 0.75,
          },
          "verkehr":{
            "name":"Verkehr",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_verkehr&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WMS_AdV_konform_App/guest",
            "opacity": 0.75,
          },
        }
      },
      "alkis_alles": {
        "name": "ST: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung_layergroup", "flurstuecke_wms", "gebaeude_wms"],
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"ST: Bodenrichtwerte Bauland 2024 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=Bauland&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_BRW2024_gast/guest?VERSION%3D1.3.0",
        "seperator": True,
        "opacity": 0.75,
      },
      "flustuecke_wfs":{
        "name":"ST: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:Flurstueck' url='https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WFS_OpenData/guest' url='https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WFS_OpenData/guest?VERSION=2.0.0' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"ST: ALKIS Gebäude (WFS)",
        "uri":"https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_ALKIS_WFS_OpenData/guest?&service=WFS&BBOX=1332412,6708967,1333423,6709355&restrictToRequestBBOX=1&VERSION=auto&typename=ave:GebaeudeBauwerk&srsname=EPSG:25832&preferCoordinatesForWfsT11=false&pagingEnabled=true",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },
      "tk_farbig_layergroup":{
        "name":"ST: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_10_farbig": {
            "name":"ST: TK 10 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk10_col_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"ST: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk25_col_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"ST: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk50_col_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"ST: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk100_col_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
#          "tk_250_farbig":{
#            "name":"ST: TÜK 250 farbig (WMS)",
#            "uri": f"{utm32}{defaultWMSSettings}layers=TUEK_250_col&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
#            "opacity": 0.75,
#            "minScale": 5000000.0,
#            "maxScale": 175000.0
#          },
        },
      },
      "tk_grau_layergroup": {
        "name": "ST: Topograf. Karten grau (WMS)",
        "layers": {
          "tk_10_grau":{
            "name":"ST: TK 10 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk10_ein_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_grau":{
            "name":"ST: TK 25 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk25_ein_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_grau":{
            "name":"ST: TK 50 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk50_ein_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_grau":{
            "name":"ST: TK 100 grau (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dtk100_ein_1&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
#          "tk_250_grau":{
#            "name":"ST: TÜK 250 grau (WMS)",
#            "uri": f"{utm32}{defaultWMSSettings}layers=TUEK_250_grau&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DTK_WMS_OpenData/guest?VERSION%3D1.3.0",
#            "opacity": 0.75,
#            "minScale": 5000000.0,
#            "maxScale": 175000.0
#          },
        },
        "seperator": True
      },
      "dop20":{
        "name":"ST: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dop20_2&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest",
      },
      "dop100":{
        "name":"ST: Digitale Orthophotos - DOP100 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=lsa_lvermgeo_dop100_unbesch&styles&url=https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest",
        "seperator": True,
      },
      "dsgk_hal":{
        "name":"HAL: Digitale Stadtgrundkarte (WMS)",
        "uri": f"{defaultWMSSettings}crs=EPSG:2398&layers=DSGK&styles&url=https://geodienste.halle.de/opendata/f398a5d8-9dce-cbbc-b7ae-7e1a7f5bf809",
        "seperator": True,
      },
    }
  },
  'sh': {   # ----------- schleswig holstein -------------------------------------------------------------------------
    'bundeslandname': 'Schleswig-Holstein',
    'themen': {
      "flurstuecke":{
        "name":"SH: ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=SH_ALKIS&styles&url=https://service.gdi-sh.de/WMS_SH_ALKIS_OpenGBD",
        "seperator": True,
      },
      "flurstuecke_wfs":{
        "name":"SH: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25833' typename='cp:CadastralParcel' url='https://service.gdi-sh.de/SH_INSPIREDOWNLOAD_AI_CP_ALKIS' url='https://service.gdi-sh.de/SH_INSPIREDOWNLOAD_AI_CP_ALKIS?version=2.0.0' version='auto'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "tk_farbig_layergroup":{
        "name":"SH: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_5_farbig": {
            "name":"SH: TK 5 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk5_col&styles&url=https://service.gdi-sh.de/WMS_SH_DTK5_OpenGBD",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"SH: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk25_col&styles&url=https://service.gdi-sh.de/WMS_SH_DTK25_OpenGBD",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"SH: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk50_col&styles&url=https://service.gdi-sh.de/WMS_SH_DTK50_OpenGBD",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"SH: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk100_col&styles&url=https://service.gdi-sh.de/WMS_SH_DTK100_OpenGBD",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
      },
      "tk_einfarbig_layergroup":{
        "name":"SH: Topograf. Karten einfarbig (WMS)",
        "layers": {
          "tk_5_einfarbig": {
            "name":"SH: TK 5 einfarbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk5_ein&styles&url=https://service.gdi-sh.de/WMS_SH_DTK5_OpenGBD",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_einfarbig":{
            "name":"SH: TK 25 einfarbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk25_ein&styles&url=https://service.gdi-sh.de/WMS_SH_DTK25_OpenGBD",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_einfarbig":{
            "name":"SH: TK 50 einfarbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk50_ein&styles&url=https://service.gdi-sh.de/WMS_SH_DTK50_OpenGBD",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_einfarbig":{
            "name":"SH: TK 100 einfarbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=sh_dtk100_ein&styles&url=https://service.gdi-sh.de/WMS_SH_DTK100_OpenGBD",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
        "seperator": True,
      },
      "dop20":{
        "name":"SH: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=sh_dop20_rgb&styles&url=https://service.gdi-sh.de/WMS_SH_DOP20col_OpenGBD",
      }
    }
  },
  'th': {   # ----------- thüringen -------------------------------------------------------------------------
    'bundeslandname': 'Thüringen',
    'themen': {
      "flurstuecke":{
        "name":"TH: ALKIS Flurstücke (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_flurstuecke&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th",
      },
      "gebaeude":{
        "name":"TH: ALKIS Gebäude (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gebaeude&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th",
      },
      "nutzung_layergroup": {
        "name": "TH: ALKIS Tatsächliche Nutzung (WMS)",
        "layers": {
          "gewaesser":{
            "name":"Gewässer",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_gewaesser&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th",
            "opacity": 0.75,
          },
          "siedlung":{
            "name":"Siedlung",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_siedlung&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th",
            "opacity": 0.75,
          },
          "vegetation":{
            "name":"Vegetation",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_vegetation&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th",
            "opacity": 0.75,
          },
          "verkehr":{
            "name":"Verkehr",
            "uri": f"{utm32}{defaultWMSSettings}layers=adv_alkis_verkehr&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wms_th",
            "opacity": 0.75,
          }
        }
      },
      "alkis_alles": {
        "name": "TH: ▶︎ ALKIS Flurstücke, Gebäude, Nutzung (WMS)",
        "layers": ["nutzung_layergroup", "flurstuecke", "gebaeude"],
        "seperator": True,
      },
      "bodenrichtwerte":{
        "name":"TH: Bodenrichtwerte Aktuell PTO (WMS)",
        "uri": f"{utm32}dpiMode=7&featureCount=10&format=image/png&tilePixelRatio=0&stepHeight=3000&stepWidth=3000&&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/boris/vBORIS_simple?zERSION%3D1.3.0&layers=vBODENRICHTWERTZONE_aktuell&layers=vBODENRICHTWERTZONE_aktuell_PTO&styles=Bodenrichtwertzone&styles=default",
        "seperator": True,
        "opacity": 0.75,
      },
      "flustuecke_wfs":{
        "name":"TH: ALKIS Flurstücke (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:Flurstueck' url='https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs' url='https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs?version=2.0.0' version='auto'",
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": "transparent",
      },
      "gebaeude_wfs":{
        "name":"TH: ALKIS Gebäude (WFS)",
        "uri":"pagingEnabled='default' preferCoordinatesForWfsT11='false' restrictToRequestBBOX='1' srsname='EPSG:25832' typename='ave:GebaeudeBauwerk' url='https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs' url='https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs?version=2.0.0' version='auto'",
        "seperator": True,
        "type": "wfs",
        "opacity": 0.75,
        "fillColor": (220,220,220),
        "strokeWidth": 0.1
      },
      "tk_farbig_layergroup":{
        "name":"TH: Topograf. Karten farbig (WMS)",
        "layers": {
          "tk_10_farbig": {
            "name":"TH: TK 10 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=th_dtk10&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/geobasis/DTK10col",
            "opacity": 0.75,
            "minScale": 17500.0,
            "maxScale": 1
          },
          "tk_25_farbig":{
            "name":"TH: TK 25 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=th_dtk25&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/geobasis/DTK25col",
            "opacity": 0.75,
            "minScale": 37500.0,
            "maxScale": 17500.0
          },
          "tk_50_farbig":{
            "name":"TH: TK 50 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=th_dtk50&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/geobasis/DTK50col",
            "opacity": 0.75,
            "minScale": 75000.0,
            "maxScale": 37500.0
          },
          "tk_100_farbig":{
            "name":"TH: TK 100 farbig (WMS)",
            "uri": f"{utm32}{defaultWMSSettings}layers=th_dtk100&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/geobasis/DTK100col",
            "opacity": 0.75,
            "minScale": 500000.0,
            "maxScale": 75000.0
          },
        },
        "seperator": True,
      },
      "dop20":{
        "name":"TH: Digitale Orthophotos - DOP20 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=th_dop&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/DOP",
      },
      "dop200":{
        "name":"TH: Digitale Orthophotos - DOP200 (WMS)",
        "uri": f"{utm32}{defaultWMSSettings}layers=th_dop200rgb&styles&url=https://www.geoproxy.geoportal-th.de/geoproxy/services/DOP",
      }
    }
  }
}
