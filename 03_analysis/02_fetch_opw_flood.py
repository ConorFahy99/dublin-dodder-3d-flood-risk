"""
02_fetch_opw_flood.py

Flood extents for the Dodder, from the OPW.

Source history worth knowing:
- EPA GeoServer serves flood extents for display only (WFS download disabled).
- NIFM (National Indicative Fluvial Mapping) deliberately excludes catchments
  already mapped by CFRAM. The Dodder is a CFRAM catchment, so NIFM is empty
  there. Confirmed: NIFM held zero features over the Dodder.
- The right product is the CFRAM Community-Scale River Flood Extents, which
  cover the modelled Areas for Further Assessment including the Dodder.

This downloads the national CFRAM current-scenario extents, reads only the
Dodder area, reprojects to EPSG:2157, clips to the catchment, and writes a
flood GeoPackage.

CRS trap handled here: the CFRAM file is TM75 Irish Grid (EPSG:29903), not ITM.
The bbox read must use catchment bounds expressed in the file's own CRS, then we
reproject the result to 2157. Reading the CRS from the file rather than assuming
it makes this robust to either Irish Grid variant.

Scenarios inside: 10% (High), 1% (Medium, the design flood), 0.1% (Low) AEP.

Licence flag: CC-BY-NC-ND 4.0. Non-commercial, no derivatives. Fine for a
personal portfolio piece with attribution to OPW. Not for paid Avora work.

Requires: requests, geopandas, pyogrio (already installed)
Output: 01_data/raw/opw/dodder_flood_cfram.gpkg
"""

from pathlib import Path
import zipfile
import requests
import pyogrio
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
OPW_DIR = ROOT / "01_data" / "raw" / "opw"
ZIP_PATH = OPW_DIR / "esds_floodmap_ext_f_c.zip"
EXTRACT_DIR = OPW_DIR / "cfram"
OUT_GPKG = OPW_DIR / "dodder_flood_cfram.gpkg"

CATCHMENT_GPKG = ROOT / "01_data" / "raw" / "epa" / "dodder_epa.gpkg"

URL = "https://s3.eu-west-1.amazonaws.com/catalogue.floodinfo.opw/cfram/esds_floodmap_ext_f_c.zip"


def download():
    OPW_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        print(f"zip already present: {ZIP_PATH.name}")
        return
    print("downloading CFRAM current-scenario extents (national file, may take a minute)...")
    with requests.get(URL, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(ZIP_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    print(f"saved {ZIP_PATH.stat().st_size / 1e6:.0f} MB")


def extract():
    with zipfile.ZipFile(ZIP_PATH) as z:
        z.extractall(EXTRACT_DIR)
    shps = sorted(EXTRACT_DIR.rglob("*.shp"))
    print(f"extracted {len(shps)} shapefile(s): {[s.name for s in shps]}")
    return shps


def main():
    download()
    shps = extract()

    catchment = gpd.read_file(CATCHMENT_GPKG, layer="dodder_subcatchment").to_crs(2157)

    if OUT_GPKG.exists():
        OUT_GPKG.unlink()

    wrote_any = False
    for shp in shps:
        # Read the file's native CRS, then express the catchment bounds in it so
        # the spatial pre-filter actually lines up.
        src_crs = pyogrio.read_info(shp)["crs"]
        bounds = tuple(catchment.to_crs(src_crs).total_bounds)

        gdf = gpd.read_file(shp, bbox=bounds)
        if gdf.empty:
            print(f"{shp.name}: no features near the Dodder")
            continue

        gdf = gdf.to_crs(2157)
        clipped = gpd.clip(gdf, catchment)
        if clipped.empty:
            print(f"{shp.name}: nothing inside the catchment after clip")
            continue

        layer = shp.stem.lower()
        clipped.to_file(OUT_GPKG, layer=layer, driver="GPKG")
        wrote_any = True
        print(f"\n{shp.name} -> layer '{layer}'")
        print(f"  native CRS: {src_crs}")
        print(f"  features in catchment: {len(clipped)}")
        print(f"  columns: {list(clipped.columns)}")
        for col in clipped.columns:
            low = col.lower()
            if any(k in low for k in ("aep", "prob", "scen", "event", "annual", "flood")):
                vals = clipped[col].dropna().unique().tolist()
                if len(vals) <= 20:
                    print(f"  {col} values: {sorted(map(str, vals))}")

    print(f"\nGeoPackage: {OUT_GPKG}")
    print("CRS: EPSG:2157")
    if not wrote_any:
        print("No flood features written. Send me this output.")


if __name__ == "__main__":
    main()
