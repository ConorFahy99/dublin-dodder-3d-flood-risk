"""
00_fetch_epa_vectors.py

Pull the EPA vector layers this project needs, scoped to the River Dodder
catchment, reproject to EPSG:2157 (Irish Transverse Mercator), and write one
tidy GeoPackage.

Why this runs on your machine and not in the assistant sandbox: the assistant's
sandbox has no network route to gis.epa.ie. Your machine does. Run this once.

Why EPSG:2157: it is the national projected system, metric and low-distortion,
so x, y, and later z are all in true metres. The EPA GeoServer serves natively
in EPSG:29902 (Irish Grid TM75); we request 2157 on output.

Requires: requests, geopandas, pyogrio
    pip install requests geopandas pyogrio

Output: 01_data/raw/epa/dodder_epa.gpkg
"""

from pathlib import Path
import io
import sys
import requests
import geopandas as gpd

# --- config -----------------------------------------------------------------

WFS = "https://gis.epa.ie/geoserver/ows"

# Project root is the folder two levels up from this script (03_analysis/..).
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "01_data" / "raw" / "epa"
OUT_GPKG = OUT_DIR / "dodder_epa.gpkg"

# Dodder catchment bounding box in EPSG:29902 (Irish Grid), with ~1 km buffer
# so edge features survive later clipping. Derived from the live extent of
# sub-catchment Dodder_SC_010: 306140,215460,327393,234428.
BBOX_29902 = (305000, 214000, 328500, 235500)

# Layers to pull. Each entry: output layer name -> (EPA typeName, filter).
# "cql" filters by attribute (used for the catchment itself).
# "bbox" filters spatially (used for everything else).
LAYERS = {
    "dodder_subcatchment": ("EPA:WFD_SubCatchments", {"cql": "Name LIKE 'Dodder%'"}),
    "river_network":       ("EPA:WATER_RIVNETROUTES", {"bbox": True}),
    "river_wfd_status":    ("EPA:RWB_WFD_LatestStatus", {"bbox": True}),
}

# Flood extents are NOT here. The EPA GeoServer publishes its flood-extent layers
# (RWB_FLOODEXTENTS_*, CWB_FLOODEXTENTS_*) for display only; the WFS download is
# disabled and returns "Feature type unknown". Get flood extents from the OPW
# instead by running 02_fetch_opw_flood.py, which pulls the NIFM extents.

# --- fetch ------------------------------------------------------------------

def fetch_layer(typename, flt):
    """Return a GeoDataFrame in EPSG:2157 for one layer, or None on failure."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": typename,
        "outputFormat": "application/json",
        "srsName": "urn:ogc:def:crs:EPSG::2157",
    }
    if "cql" in flt:
        params["CQL_FILTER"] = flt["cql"]
    if flt.get("bbox"):
        # BBOX values must be in the CRS named at the end of the filter.
        minx, miny, maxx, maxy = BBOX_29902
        params["bbox"] = f"{minx},{miny},{maxx},{maxy},urn:ogc:def:crs:EPSG::29902"

    r = requests.get(WFS, params=params, timeout=180)
    r.raise_for_status()
    if not r.text.strip():
        raise ValueError("empty response from server")
    gdf = gpd.read_file(io.BytesIO(r.content))
    if gdf.empty:
        return gdf
    # The server should already return 2157; assert and set if missing.
    if gdf.crs is None:
        gdf = gdf.set_crs(2157)
    elif gdf.crs.to_epsg() != 2157:
        gdf = gdf.to_crs(2157)
    return gdf


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()  # rewrite cleanly

    summary = []
    for out_name, (typename, flt) in LAYERS.items():
        try:
            gdf = fetch_layer(typename, flt)
            if gdf is None or gdf.empty:
                summary.append((out_name, typename, "0 features (empty)"))
                continue
            gdf.to_file(OUT_GPKG, layer=out_name, driver="GPKG")
            geom = gdf.geom_type.iloc[0]
            summary.append((out_name, typename, f"{len(gdf)} features, {geom}"))
        except Exception as e:  # noqa: BLE001 - report and continue
            summary.append((out_name, typename, f"FAILED: {e}"))

    print("\nDodder EPA fetch summary")
    print("-" * 60)
    for out_name, typename, note in summary:
        print(f"{out_name:22s} {note}")
    print("-" * 60)
    print(f"GeoPackage: {OUT_GPKG}")
    print("CRS: EPSG:2157 (Irish Transverse Mercator)")
    if not OUT_GPKG.exists():
        print("\nNothing written. Check network access to gis.epa.ie.")
        sys.exit(1)


if __name__ == "__main__":
    main()
