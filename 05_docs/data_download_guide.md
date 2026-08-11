# Data download guide

Two scripts in `03_analysis/` pull the vector data automatically. This guide
covers the three datasets that need a manual portal download or a licence
decision: LiDAR terrain, OPW flood depth grids, and population.

Study area: the River Dodder catchment (EPA sub-catchment `Dodder_SC_010`,
Catchment ID `09`). It runs from Kippure in the Dublin and Wicklow uplands in
the south-west, down through Rathfarnham, Templeogue, Rathmines, Donnybrook,
and Ballsbridge, to the tidal mouth at Ringsend in the north-east. Select tiles
that cover that footprint.

Working CRS for the project: EPSG:2157 (Irish Transverse Mercator).

---

## 1. Run the two fetch scripts first

From the project root:

```
pip install requests geopandas pyogrio osmnx
python 03_analysis/00_fetch_epa_vectors.py
python 03_analysis/01_fetch_osm_buildings.py
python 03_analysis/02_fetch_opw_flood.py
```

These write `01_data/raw/epa/dodder_epa.gpkg` (catchment, river network, river
water-quality status), `01_data/raw/osm/dodder_buildings.gpkg` (building
footprints), and `01_data/raw/opw/dodder_flood_cfram.gpkg` (fluvial flood extents
at the 10%, 1%, and 0.1% events). All in EPSG:2157.

Flood source note: the EPA GeoServer serves its flood extents for display only.
NIFM, the other OPW product, deliberately excludes catchments already mapped by
CFRAM, so it is empty over the Dodder. The correct source is the CFRAM
Community-Scale River Flood Extents (script 02), native in TM75 Irish Grid
(EPSG:29903) and reprojected to 2157. CC-BY-NC-ND, non-commercial. These are
extents (where it floods). Depth comes from the LiDAR plus the extents, or the
OPW depth grids below.

---

## 2. LiDAR DTM and DSM

Source: GSI Open Topographic (LiDAR) Data viewer on the government open data hub.
GeoTIFF rasters, licensed CC-BY 4.0. You need both:

- **DTM** (Digital Terrain Model, bare earth) for the flood surface and depth.
- **DSM** (Digital Surface Model, includes buildings and vegetation). DSM minus
  DTM gives the normalised surface (nDSM), which is real building height for the
  3D extrusion.

Steps:

1. Open the GSI Open Topographic Data download viewer:
   https://opendata-geodata-gov-ie.hub.arcgis.com/datasets/ie-gsi-open-topographic-lidar-data-ireland-itm-download-viewer
2. Pan to the Dodder catchment. Select every tile intersecting the footprint
   above. Download the DTM and the DSM for each tile.
3. Resolution varies by capture (1 m and 2 m exist for parts of Dublin). Note
   the resolution of what you pull in `05_docs/assumptions.md`; it sets the
   floor for depth accuracy.
4. Each tile downloads as a zip holding both a DTM and a DSM GeoTIFF. Drop every
   zip into `01_data/raw/lidar/_zips/` (excluded from git).
5. Run `python3 03_analysis/03_prep_lidar.py`. It extracts the zips, sorts DTMs
   into `dtm/` and DSMs into `dsm/`, and assigns EPSG:2157. The OPW GeoTIFFs hold
   correct ITM coordinates but a broken CRS label, so this assign step (a
   relabel, not a reprojection) is what makes them line up in QGIS.
6. In QGIS, merge tiles per model (Phase 2 of the method sheet), then clip to the
   catchment.

If GSI coverage for the lower Dodder is thin, the alternative national source is
the same open data hub, dataset "Open Topographic Lidar Data" on data.gov.ie.

## 3. OPW flood depth grids (optional but recommended)

The EPA extents tell you where the 10%, 1%, and 0.1% floods reach. For a proper
3D depth surface you have two routes:

**Route A, derive depth yourself (no extra download).** Take the OPW flood
extent, sample the DTM elevation along its edge to estimate the water surface
level, then subtract the DTM inside the extent. This bathtub method is standard
and is good practice to build once.

**Route B, use OPW modelled depth grids.** The CFRAM programme produced depth
grids. Access them through the flood maps portal:

1. https://www.floodinfo.ie/map/floodmaps/
2. Find the Dodder reach. The community-scale flood maps are served as WMS and
   can be added live in QGIS (Layer > Add WMS/WMTS Layer).
3. Gridded depth data availability and download vary by reach. If the download
   is not exposed in the viewer, request it from OPW, or fall back to Route A.

**Licence flag that matters for Avora.** The OPW community flood maps are
CC-BY-NC-ND (non-commercial, no derivatives). Fine for a personal portfolio
piece. Do not reuse them in paid client work without checking terms. The EPA
layers and GSI LiDAR are CC-BY 4.0, so those are safe for commercial use with
attribution.

## 4. Population (for exposure counts)

To count people in the flood extent, not just buildings:

1. Small Area boundaries (Census 2022) from the Tailte Éireann / GeoHive open
   data hub. Clip to the catchment. Use the ungeneralised version for area work.
2. CSO Small Area Population Statistics (SAPS) 2022 CSV from cso.ie.
3. Join SAPS to the boundaries on the Small Area code. Watch for leading-zero
   code mangling if the CSV passes through Excel.
4. Areal-interpolate population into the flood extent (proportion of each Small
   Area inside the extent) for an exposure estimate.

---

## Verify URLs at run time

Irish portal URLs drift after agency mergers (OSi is now Tailte Éireann). If a
link 404s, search the dataset title on data.gov.ie. Record the working URL and
download date in `data_sources_log.md`.
