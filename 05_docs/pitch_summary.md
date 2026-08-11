# Dublin Dodder 3D flood risk: pitch summary

## The question

A flood extent map tells you which buildings sit in a flood zone. It does not tell you how deep the water gets or how far up each building it reaches. This project answers the second question for the River Dodder in Dublin: for the 1% annual flood, how deep is the water at each building, and how many buildings lose their ground floor.

## The approach

The work runs from open data to an interactive 3D model, all in EPSG:2157 so heights and depths are in true metres.

Flood extents come from the OPW CFRAM programme, terrain from the OPW 2 m National LiDAR, buildings from OpenStreetMap, and the catchment from the EPA. Building heights are the terrain-corrected LiDAR surface (DSM minus DTM) sampled per footprint. Flood depth is a bathtub surface: ground elevations along the flood edge, interpolated across the extent, minus the terrain. Each building is then attributed with its flood depth and the storeys inundated, and extruded to real height and shaded by depth in a 3D scene exported as an interactive web page.

## The result

For the lower and middle Dodder, the reach covered by LiDAR and 71% of the 1% flood extent:

- 2,254 buildings sit within the 1% flood
- 432 have damaging ground-floor depth over 0.3 m
- 1.04 km² of land floods, median depth 0.22 m, rising to several metres by the channel

The flooding is shallow and broad, ground-floor inundation across many buildings rather than deep water over a few, with the deepest water along the channel through Ballsbridge and Donnybrook, the reach that flooded in 2011.

## Tools

QGIS for the 3D map and export, Python (GeoPandas, Rasterio, Shapely) for the data pipeline, GDAL for raster handling, and Qgis2threejs for the web scene.

## Scope and next steps

This is a first pass on the LiDAR-covered reach. Extending it means pulling the upstream and eastern tiles for full-catchment cover, adding CSO Small Area population for a people-exposed figure alongside buildings, and running the 10% and 0.1% events already held in the flood GeoPackage.
