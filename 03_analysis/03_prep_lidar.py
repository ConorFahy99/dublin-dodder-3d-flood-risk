"""
03_prep_lidar.py

Prepare the downloaded OPW LiDAR tiles for QGIS.

Each tile you download from the GSI viewer is a zip holding a DTM and a DSM
GeoTIFF. Two things need doing before they are usable:
  1. Sort them: DTMs into lidar/dtm/, DSMs into lidar/dsm/.
  2. Fix the CRS. The OPW GeoTIFFs carry correct ITM coordinates but a broken
     projection label, so QGIS reads them as an unknown CRS and they will not
     line up. We ASSIGN EPSG:2157. This is a relabel, not a reprojection: the
     pixels and coordinates are untouched, we just stamp the right CRS tag.
     Only safe because the coordinates are already ITM (verified: a tile near
     Ringsend reads easting ~719000, northing ~733000, which is ITM).

How to use:
  1. Download the tile zips from the GSI viewer.
  2. Drop every zip into 01_data/raw/lidar/_zips/
  3. Run: python3 03_analysis/03_prep_lidar.py

Requires: rasterio
    pip install rasterio

Result: sorted, correctly-projected tiles in lidar/dtm/ and lidar/dsm/.
"""

from pathlib import Path
import zipfile
import shutil
import tempfile
import rasterio
from rasterio.crs import CRS

ROOT = Path(__file__).resolve().parents[1]
LIDAR = ROOT / "01_data" / "raw" / "lidar"
ZIP_DIR = LIDAR / "_zips"
DTM_DIR = LIDAR / "dtm"
DSM_DIR = LIDAR / "dsm"

ITM = CRS.from_epsg(2157)


def stamp_crs(path):
    """Assign EPSG:2157 in place. Relabel only, no resampling."""
    with rasterio.open(path, "r+") as ds:
        ds.crs = ITM


def place(tif_path):
    """Route a tif to dtm/ or dsm/ by its filename, then fix its CRS."""
    name = tif_path.name
    upper = name.upper()
    if "_DTM" in upper:
        dest = DTM_DIR / name
    elif "_DSM" in upper:
        dest = DSM_DIR / name
    else:
        print(f"  skipped (not DTM or DSM): {name}")
        return None
    DTM_DIR.mkdir(parents=True, exist_ok=True)
    DSM_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tif_path, dest)
    stamp_crs(dest)
    return dest


def main():
    zips = sorted(ZIP_DIR.glob("*.zip"))
    if not zips:
        print(f"No zips found in {ZIP_DIR}")
        print("Drop your downloaded OPW tile zips there, then rerun.")
        return

    dtm_n = dsm_n = 0
    for z in zips:
        print(f"\n{z.name}")
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(z) as zf:
                zf.extractall(tmp)
            for tif in sorted(Path(tmp).rglob("*.tif")):
                dest = place(tif)
                if dest is None:
                    continue
                with rasterio.open(dest) as r:
                    b = [round(x) for x in r.bounds]
                print(f"  {dest.parent.name}/{dest.name}  CRS set to EPSG:2157  bounds {b}")
                if "dtm" in dest.parent.name:
                    dtm_n += 1
                else:
                    dsm_n += 1

    print(f"\nDone. {dtm_n} DTM tiles in {DTM_DIR}")
    print(f"      {dsm_n} DSM tiles in {DSM_DIR}")
    print("Next: merge each set in QGIS (Phase 2), then clip to the catchment.")


if __name__ == "__main__":
    main()
