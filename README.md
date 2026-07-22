# Dublin Dodder 3D Flood Risk

**How deep does a Dodder flood get, and how far up each building does the water reach?**

A 3D flood exposure analysis of the River Dodder catchment in Dublin. It combines LiDAR terrain, OPW flood extents, and building footprints to model inundation depth per building and count exposed storeys, not just which buildings sit inside a flood zone.

**[View the interactive 3D map →](link when available)**

---

## Findings

| | |
|---|---|
| **—** | Buildings exposed (1% annual flood) |
| **—** | Population within modelled flood extent |
| **—** | Buildings with ground floor fully inundated |

---

## How it works

**LiDAR DTM/DSM** — national LiDAR gives a bare-earth terrain model and a surface model. Building heights come from the normalised surface (DSM minus DTM).

**OPW CFRAM flood data** — modelled flood extents and, where available, depth grids for the 10%, 1%, and 0.1% annual exceedance probability events.

**Depth grid** — water surface elevation minus terrain within the flood extent gives depth per cell. Each building is attributed with the depth at its footprint and the number of storeys inundated.

**3D output** — buildings extruded to real height and shaded by flood depth, exported as an interactive web scene.

---

## Tools

- **QGIS** for 3D map view, styling, and the Qgis2threejs web export
- **Python** (GeoPandas, Rasterio, Shapely, NumPy) for terrain and depth processing
- **GDAL** for raster handling and reprojection

CRS: EPSG:2157 (Irish Transverse Mercator) throughout, so x, y, and z are all in metres.

---

## Project structure

```
├── 01_data/
│   ├── raw/                  # Source data — never edit these files
│   └── processed/            # Outputs of processing scripts
├── 02_qgis/                  # QGIS project file
├── 03_analysis/              # Python scripts
├── 04_outputs/deliverables/  # Final maps, reports, interactive scene
└── 05_docs/                  # Assumptions, data sources, notes
```

---

## Author

**Conor Fahy**
Freelance GIS Analyst
conorbrianfahy@gmail.com
