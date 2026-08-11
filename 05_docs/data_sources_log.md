# Data sources log

Study area: River Dodder catchment. EPA sub-catchment `Dodder_SC_010`,
Catchment ID `09`, South Dublin CC. Native extent in EPSG:29902 (Irish Grid):
306140, 215460, 327393, 234428. Project CRS: EPSG:2157.

| Dataset | Source | Access | Licence | Notes |
|---|---|---|---|---|
| Dodder catchment boundary | EPA WFD_SubCatchments | `00_fetch_epa_vectors.py` (WFS) | CC-BY 4.0 | Filter Name LIKE 'Dodder%' |
| River network | EPA WATER_RIVNETROUTES | `00_fetch_epa_vectors.py` (WFS) | CC-BY 4.0 | Clipped to catchment bbox |
| Fluvial flood extents (10%/1%/0.1%) | OPW CFRAM Community-Scale, current scenario | `02_fetch_opw_flood.py` (S3 zip) | CC-BY-NC-ND 4.0 | EPA flood WFS is display-only. NIFM excludes CFRAM areas so it is empty over the Dodder. CFRAM is the correct source. Native EPSG:29903, reprojected to 2157. Non-commercial |
| River water-quality status | EPA RWB_WFD_LatestStatus | `00_fetch_epa_vectors.py` (WFS) | CC-BY 4.0 | Context layer |
| Building footprints | OpenStreetMap | `01_fetch_osm_buildings.py` (Overpass via osmnx) | ODbL | Keeps building:levels where tagged |
| LiDAR DTM + DSM | GSI Open Topographic Data | Manual, see download guide | CC-BY 4.0 | GeoTIFF, 1 m / 2 m; DSM minus DTM = building height |
| OPW flood depth grids | floodinfo.ie (CFRAM) | Manual / WMS, see download guide | CC-BY-NC-ND | Non-commercial. Or derive depth from extent + DTM |
| Small Area boundaries | Tailte Éireann / GeoHive | Manual, see download guide | CC-BY 4.0 | Census 2022 |
| Population (SAPS) | CSO Small Area Population Statistics 2022 | Manual, see download guide | CC-BY 4.0 | Join to Small Areas on SA code |

Fill in the download date as you pull each manual dataset.

## Tooling note

The EPA GeoServer serves natively in EPSG:29902 (Irish Grid TM75). The fetch
script requests EPSG:2157 on output, so the GeoPackage is already in project CRS.
