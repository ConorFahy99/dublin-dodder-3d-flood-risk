# QGIS method sheet: Dodder 3D flood risk

The workflow from raw data to an interactive 3D scene. Each phase names the
concept, the QGIS tool, and the reasoning so the steps transfer to future work.
Project CRS throughout: EPSG:2157 (Irish Transverse Mercator), metric so depth
and height are in true metres.

Processing algorithms are in the Processing Toolbox (Ctrl+Alt+T). Where a step
is easier as one line of GDAL, that is noted.

---

## Phase 0: get the data in

1. Open a terminal in the project root.
2. `pip install requests geopandas pyogrio osmnx`
3. `python 03_analysis/00_fetch_epa_vectors.py`
4. `python 03_analysis/01_fetch_osm_buildings.py`
5. Download LiDAR DTM and DSM, and optionally the OPW depth grids, following
   `05_docs/data_download_guide.md`. DTM tiles to `01_data/raw/lidar/dtm/`,
   DSM to `01_data/raw/lidar/dsm/`.

You now have: `dodder_epa.gpkg`, `dodder_buildings.gpkg`, and LiDAR tiles.

---

## Phase 1: set up the QGIS project

1. New project. Save as `02_qgis/dodder_flood.qgz`.
2. Set project CRS to EPSG:2157 (Project > Properties > CRS). Do this first so
   every layer draws in the same frame.
3. Load the layers. Drag `dodder_epa.gpkg` in and add the sub-catchment and
   river network. Drag `dodder_flood_cfram.gpkg` in and add the three flood
   extent layers: `esds_floodmap_ext_f_c_0010` (10%), `_0100` (1%, the design
   flood), `_1000` (0.1%). Drag `dodder_buildings.gpkg` in for the footprints.
4. Inspect before you trust. For each layer check: CRS is 2157, geometry type,
   feature count, and that it sits over the Dodder when you add a basemap
   (QuickMapServices > OSM). This is the habit that catches bad data early.
5. Save.

---

## Phase 2: prepare the terrain

The DTM is your flood surface and your reference for depth. It must be one clean
raster in 2157, clipped to the catchment.

0. **Prep the tiles first.** Each downloaded tile zip holds both a DTM and a DSM.
   Drop every zip into `01_data/raw/lidar/_zips/` and run
   `python3 03_analysis/03_prep_lidar.py`. It sorts them into `dtm/` and `dsm/`
   and assigns EPSG:2157. This matters: the OPW GeoTIFFs carry correct ITM
   coordinates but a broken CRS label, so without this step QGIS treats them as
   unknown CRS and they will not line up. Assigning 2157 is a relabel, not a
   reprojection.
1. **Merge tiles.** Processing > GDAL > Merge, on all DTM tiles. Repeat for DSM.
   Output to `01_data/processed/dtm_merged.tif` and `dsm_merged.tif`.
2. **Confirm or set CRS.** If the merged raster is not 2157, Warp (Reproject):
   `gdalwarp -t_srs EPSG:2157 dtm_merged.tif dtm_2157.tif`.
3. **Clip to catchment.** Processing > GDAL > Clip Raster by Mask Layer, mask =
   `dodder_subcatchment`. Do this for both DTM and DSM.
4. Check the DTM makes sense: symbolise as a hillshade or a graduated ramp and
   confirm the valley of the Dodder reads as a low line through the terrain.

---

## Phase 3: building heights (nDSM)

Real building height is the surface model minus the terrain model. That is the
normalised DSM.

1. **Match the grids.** The DTM and DSM must share extent, resolution, and
   alignment before you subtract them. If they differ, Processing > GDAL >
   Warp each to the same resolution, or use "Align Rasters".
2. **Subtract.** Raster Calculator (Raster menu):
   `"dsm_2157@1" - "dtm_2157@1"`. Output `01_data/processed/ndsm.tif`.
   This raster is height above ground: near zero on roads, a few metres on
   buildings and trees.
3. **Height per footprint.** Processing > Zonal Statistics, polygons =
   buildings, raster = nDSM, statistic = **median**. Median not mean, because it
   ignores chimney and roof-edge outliers and gives a stable wall height.
4. The buildings layer now has a height field (for example `ndsm_median`). Where
   OSM `building:levels` exists, sanity-check against levels times about 3 m.
   Fill missing heights with a stated default (say 2 storeys, about 6 m) and
   record that in `assumptions.md`.

---

## Phase 4: flood depth grid

Two routes. Route A needs only the extent and the DTM and is the better
practice. Route B uses OPW depth grids if you downloaded them.

### Route A: derive depth (bathtub method)

The idea: the water surface sits at roughly the ground elevation at the edge of
the flood extent. Interpolate that surface across the extent, then subtract the
terrain to get depth. Do this per scenario, starting with the 1% design flood
layer `esds_floodmap_ext_f_c_0100`.

0. **Dissolve first.** CFRAM delivers the extent as ~1,200 small polygons.
   Processing > Dissolve on `esds_floodmap_ext_f_c_0100` to merge them into one
   clean extent. Use the dissolved output everywhere below.
1. **Extent to boundary.** Processing > Polygons to Lines on the dissolved extent.
2. **Points along the edge.** Processing > Points along Geometry (spacing about
   50 m) on that boundary.
3. **Sample ground level.** Processing > Sample Raster Values, points = the edge
   points, raster = clipped DTM. Each point now carries the ground elevation at
   the flood edge, which stands in for the water level there.
4. **Interpolate a water surface.** Processing > TIN Interpolation, using the
   sampled elevation field. Set the extent and pixel size to match the DTM.
   Output `water_surface.tif`.
5. **Clip** the water surface to the flood extent polygon (Clip Raster by Mask).
6. **Depth.** Raster Calculator:
   `"water_surface@1" - "dtm_2157@1"`. Output `flood_depth_medium.tif`.
7. **Remove negatives.** In the same expression wrap it so depth below zero
   becomes null: `("water_surface@1" - "dtm_2157@1") * (("water_surface@1" - "dtm_2157@1") > 0)`
   then set 0 to NoData in layer properties, or use the "Set null" tool.

Limitation to note: this assumes a locally flat water surface tied to the extent
edge. Fine for a floodplain reach, weaker on steep gradients. State it.

### Route B: OPW depth grid

If you downloaded the OPW grid, it is already depth. Just Warp to 2157 and Clip
to the catchment. Skip straight to Phase 5.

---

## Phase 5: attribute buildings with flood depth

1. Processing > Zonal Statistics, polygons = buildings, raster =
   `flood_depth_medium`, statistic = **mean** and **max**. Buildings outside the
   extent get null, which means not flooded.
2. **Storeys inundated.** Open the field calculator on buildings, new field
   `storeys_flooded`:
   `ceil( "flood_depth_mean" / 2.7 )` using a 2.7 m floor-to-floor assumption.
   Null depth gives null, which is correct.
3. **Ground floor lost flag.** New field `gf_lost`:
   `if("flood_depth_mean" > 0.3, 1, 0)`. The 0.3 m threshold is a common
   habitable-floor damage trigger. Record both assumptions in `assumptions.md`.
4. Repeat Phases 4 and 5 for the 10% (`esds_floodmap_ext_f_c_0010`) and 0.1%
   (`esds_floodmap_ext_f_c_1000`) scenarios if you want the full set. Name fields
   per scenario.

---

## Phase 6: exposure summary

1. Buildings exposed: Select by Expression `"flood_depth_mean" > 0`, read the
   count from the status bar. Do it per scenario.
2. Population: load Small Areas plus the SAPS join (see download guide). Areal
   interpolation: intersect Small Areas with the flood extent, compute the area
   fraction inside, multiply by Small Area population. Sum for the exposed total.
3. Put the headline numbers into the project README findings table.

---

## Phase 7: build the 3D scene

1. View > 3D Map Views > New 3D Map.
2. **Terrain.** In the 3D map config, set Terrain type = DEM (Raster Layer),
   layer = clipped DTM. Now the ground has real relief.
3. **Buildings extruded.** Select the buildings layer, Properties > 3D View >
   enable, extrusion height = your height field (`ndsm_median`). Colour by flood
   depth: graduated symbology on `flood_depth_mean` (blues, deeper = darker) so
   flooded buildings read at a glance while dry ones stay neutral.
4. **Water.** Two options. Simple: add the flood extent polygon, give it a small
   fixed elevation offset and a translucent blue fill so it reads as a sheet.
   Better: drape the depth raster as a coloured surface.
5. Orbit and confirm the story reads: water pooling in the valley, buildings
   along the reach shaded by how deep they sit.

---

## Phase 8: export and write up

1. **Interactive scene.** Install the Qgis2threejs plugin (Plugins > Manage).
   Open it, it reads your 3D scene, then Export > Web (glTF/HTML). Save the HTML
   into `04_outputs/deliverables/`. This is the single file you can host or send.
2. **Static maps.** A 2D depth map and a 3D screenshot to `04_outputs/maps/`.
3. **Fill the README** findings table and the assumptions file. The assumptions
   are what make this defensible: floor height, depth method, height source.
4. Commit. If iCloud sync keeps locking the `.git` folder, move the project off
   the synced Desktop or pause sync while committing.

---

## Suggested order for a first pass

Do the 1% (medium) scenario end to end first: terrain, nDSM, one depth grid, one
set of building attributes, one 3D scene. Get the whole pipeline working on one
scenario before adding the 10% and 0.1% events. It is faster to debug and you
have a shareable result sooner.
