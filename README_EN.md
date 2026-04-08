<p align="center">
  <img src="GeoBasis_Loader_icon.png" alt="GeoBasis Loader Logo" width="80">
</p>

<h1 align="center">GeoBasis Loader</h1>

<p align="center">
  Load open-data geo services into QGIS with a single click &mdash; focused on Germany.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/QGIS-%E2%89%A5_3.40-93b023?logo=qgis" alt="QGIS Version">
  <img src="https://img.shields.io/github/license/geoObserver/geobasis_loader" alt="License">
  <img src="https://img.shields.io/badge/dynamic/json?color=green&label=Downloads&query=$.GeoBasis_Loader.downloads&url=https://raw.githubusercontent.com/Mariosmsk/qgis-plugins-downloads/main/data/plugins.json" alt="Downloads">
  <img src="https://img.shields.io/badge/Qt5_%7C_Qt6-compatible-41cd52" alt="Qt Compatibility">
</p>

<p align="center">
  <a href="README.md">Deutsche Version</a> &middot;
  <a href="https://geoobserver.de/qgis-plugin-geobasis-loader/">Website</a> &middot;
  <a href="https://github.com/geoObserver/geobasis_loader/issues">Report a Bug</a>
</p>

---

## What is GeoBasis Loader?

This QGIS plugin simplifies access to **WMS, WMTS, WFS, WCS, and VectorTiles services** from the open data portals of state surveying offices (focused on Germany) and other providers, as well as background maps like OSM and Basemap.de. Instead of manually assembling URLs, just pick a layer from the plugin menu.

## Features

- Access to geo services from all 16 German federal states plus Europe and World catalogs
- Supported services: WMS, WMTS, WFS, WCS, OGC API Features, VectorTiles
- Integrated QGIS search via the Locator (prefix `gbl`)
- Favorites system with star indicators for frequently used services
- Automatic coordinate reference system detection
- Redundant servers with automatic failover
- Local cache for fast offline access to catalog data

## Screenshot

<p align="center">
  <img src="GBLv21.png" alt="GeoBasis Loader plugin menu with favorites" width="700">
</p>

## Installation

### Via the QGIS Plugin Manager (recommended)

1. Open QGIS
2. Go to **Plugins** > **Manage and Install Plugins...**
3. Search for **GeoBasis_Loader**
4. Click **Install Plugin**

### Manual Installation

1. Download the latest ZIP from the [Releases page](https://github.com/geoObserver/geobasis_loader/releases)
2. In QGIS: **Plugins** > **Manage and Install Plugins...** > **Install from ZIP**
3. Select the downloaded ZIP file

## Quick Start

**Step 1** &mdash; After installation, the **GeoBasis Loader** entry appears in the Plugins menu. Select a catalog (e.g., *Deutschland*).

**Step 2** &mdash; Choose a federal state and topic from the menu (e.g., *Sachsen > Digitale Orthophotos*).

**Step 3** &mdash; Select the appropriate coordinate reference system or use automatic detection. The layer is loaded directly into the current project.

> **Tip:** Use the Locator (`Ctrl+K`) with the prefix `gbl` to find topics by text search.

## Favorites

Frequently used services can be marked as favorites:

1. Open **Settings** from the plugin menu
2. In the *Topics* tab, check the desired entries in the **Favorite** column
3. After saving, a dedicated **Favorites** section appears in the plugin menu with all marked entries (indicated by &#9733;)

Favorites persist across plugin updates as they are stored in the QGIS user profile.

## FAQ

**A service is unavailable or shows no data.**
Availability depends entirely on the respective data provider. If a link is outdated, please [create an issue](https://github.com/geoObserver/geobasis_loader/issues) or send an email to [news@geoobserver.de](mailto:news@geoobserver.de?subject=GeoBasis_Loader_Input:).

**Which coordinate reference system should I choose?**
When in doubt, EPSG:25832 (UTM Zone 32N) works for most of Germany. The *Automatic CRS* option in the plugin menu uses the current project's CRS if supported by the service.

**How do I update the catalog data?**
Select **Reload Catalogs** from the plugin menu. Catalogs are loaded from redundant servers; if one fails, an automatic fallback occurs.

**Does the plugin support QGIS < 3.40?**
Version 2.0+ requires QGIS 3.40+ (Qt6-compatible). For older QGIS versions, plugin version 1.3 is available.

## Contributing

Contributions are welcome! Ways to help:

- **Report broken URLs** &mdash; [Create an issue](https://github.com/geoObserver/geobasis_loader/issues)
- **Suggest new services** &mdash; Via issue or email to [news@geoobserver.de](mailto:news@geoobserver.de?subject=GeoBasis_Loader_Input:)
- **Contribute code** &mdash; Fork the repo, develop on a feature branch, submit a pull request

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

## Acknowledgments

- **Anton May** &mdash; for development support
- **Mike Elstermann ([#geoObserver](https://geoobserver.de))** &mdash; project initiator and maintainer
- All data providers who offer their geo services as open data

---

<p align="center">
  <a href="https://download.geoobserver.de/donate.html">
    <img src="https://geoobserver.de/wp-content/uploads/2022/02/btn_donate_pp_142x27.png" alt="Donate">
  </a>
  <br>
  <sub>Like the plugin? Support via donation is greatly appreciated.</sub>
</p>

---

<details>
<summary>Disclaimer</summary>

The links (URLs) to the providers' services used in this plugin are researched and implemented with the greatest possible care. However, errors in the editing process cannot be ruled out. No liability can be accepted for the availability, accuracy, completeness, and topicality of these links. The terms of use described by the respective provider apply.
</details>
