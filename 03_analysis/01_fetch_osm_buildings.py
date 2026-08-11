"""
01_fetch_osm_buildings.py

Pull OpenStreetMap building footprints for the Dodder study area, reproject to
EPSG:2157, and write them to a GeoPackage. Buildings are the objects you extrude
and shade by flood depth in the 3D scene.

Note on authority: OSM is the open source. GeoDirectory is the authoritative
Irish building and address database, but it is paid. This uses OSM; where OSM
carries a `building:levels` tag we keep it, since it gives real storey counts
for the 3D extrusion. Gaps get filled with an assumed floor height later.

Requires: osmnx, geopandas, pyogrio
    pip install osmnx geopandas pyogrio

GUI alternative if you would rather practise in QGIS: install the QuickOSM
plugin, run a query for key=building in the same bounding box, then reproject.

Output: 01_data/raw/osm/dodder_buildings.gpkg
"""

from pathlib import Path
import osmnx as ox
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "01_data" / "raw" / "osm"
OUT_GPKG = OUT_DIR / "dodder_buildings.gpkg"

# Dodder catchment bounding box in WGS84 (lon/lat), matching the EPA bbox.
# Approx: Kippure/Wicklow uplands in the south-west to Ringsend in the north-east.
WEST, SOUTH, EAST, NORTH = -6.45, 53.18, -6.19, 53.36


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # features_from_polygon is stable across osmnx versions, unlike bbox arg order.
    poly = box(WEST, SOUTH, EAST, NORTH)
    gdf = ox.features_from_polygon(poly, tags={"building": True})

    # Keep polygon geometries only (drop stray points/lines).
    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()

    # Reproject to Irish Transverse Mercator for metric area and height work.
    gdf = gdf.to_crs(2157)

    # Trim to useful columns; osm tag set is wide and mixed-type.
    keep = [c for c in ["building", "building:levels", "height", "name"] if c in gdf.columns]
    gdf = gdf[keep + ["geometry"]]

    # GPKG dislikes list-valued cells that OSM sometimes produces; coerce to str.
    for c in keep:
        gdf[c] = gdf[c].astype(str)

    gdf.to_file(OUT_GPKG, layer="buildings", driver="GPKG")
    print(f"buildings: {len(gdf)} footprints")
    print(f"GeoPackage: {OUT_GPKG}")
    print("CRS: EPSG:2157")


if __name__ == "__main__":
    main()
