import sys
from pathlib import Path
sys.path.append(r"c:\Users\Ramil\Downloads\QM")
from reporting import create_labo_roads_geojson
import geopandas as gpd


def test_assign_barangays_on_geojson():
    # Regenerate or update the existing geojson so the property is added
    geojson_path = create_labo_roads_geojson(force_regenerate=False)
    assert geojson_path is not None
    gdf = gpd.read_file(geojson_path)
    # Confirm the 'barangay' column exists and there are non-null values
    assert 'barangay' in gdf.columns
    # At least one non-'Unknown' should be present if centers overlap area
    non_unknown = gdf[gdf['barangay'].notnull() & (gdf['barangay'] != 'Unknown')]
    assert len(non_unknown) > 0
