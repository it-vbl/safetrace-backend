import os
import tempfile
import zipfile
import fiona
from shapely.geometry import shape, mapping
import io


def geojson_to_shp_zip_bytes(geojson_data):
    """
    Convert GeoJSON to SHP file compressed in ZIP and return ZIP bytes.

    Args:
        geojson_data (dict): GeoJSON data (not a file path).

    Returns:
        bytes: Bytes of the resulting ZIP file.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = os.path.join(tmpdir, "output.shp")
        # Get schema from first feature
        first_feature = geojson_data['features'][0]
        schema = {
            'geometry': first_feature['geometry']['type'],
            'properties': {k: type(v).__name__ for k, v in first_feature['properties'].items()}
        }
        # Map data types to fiona
        type_map = {'str': 'str', 'int': 'int', 'float': 'float'}
        schema['properties'] = {k: type_map.get(v, 'str') for k, v in schema['properties'].items()}

        crs = geojson_data.get('crs', {'init': 'epsg:4326'})

        with fiona.open(
            shp_path, 'w',
            driver='ESRI Shapefile',
            schema=schema,
            crs=crs
        ) as shp:
            for feature in geojson_data['features']:
                shp.write({
                    'geometry': mapping(shape(feature['geometry'])),
                    'properties': feature['properties']
                })

        # Bundle all SHP files into ZIP (to memory)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zipf:
            for ext in ['shp', 'shx', 'dbf', 'prj', 'cpg']:
                file_path = os.path.join(tmpdir, f"output.{ext}")
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=f"output.{ext}")

        zip_buffer.seek(0)
        return zip_buffer


def shp_zip_to_geojson(shp_zip_bytes):
    """
    Convert SHP file in ZIP form (bytes) to GeoJSON FeatureCollection.

    Args:
        shp_zip_bytes (bytes): ZIP bytes containing SHP file.

    Returns:
        dict: GeoJSON FeatureCollection data with all features from shapefile.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save zip to temporary file and extract
        zip_path = os.path.join(tmpdir, "input.zip")
        with open(zip_path, "wb") as f:
            f.write(shp_zip_bytes)
        
        # Validate that file is a valid ZIP
        try:
            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(tmpdir)
        except zipfile.BadZipFile:
            raise ValueError("File is not a valid ZIP")
        
        # Find .shp file
        shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
        if not shp_files:
            raise ValueError("ZIP file does not contain shapefile (.shp)")
        
        shp_path = os.path.join(tmpdir, shp_files[0])
        
        features = []
        with fiona.open(shp_path, 'r') as src:
            for feat in src:
                # Convert geometry object to dict using mapping
                geometry_dict = mapping(shape(feat['geometry'])) if feat['geometry'] else None
                
                features.append({
                    'type': 'Feature',
                    'geometry': geometry_dict,
                    'properties': dict(feat['properties']) if feat['properties'] else {}
                })
        
        if not features:
            raise ValueError("Shapefile does not contain features")
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return geojson


def shp_zip_to_geojson_polygon(shp_zip_bytes):
    """
    Convert SHP file in ZIP form (bytes) to GeoJSON (dict) only for features with Polygon geometry type.

    Args:
        shp_zip_bytes (bytes): ZIP bytes containing SHP file.

    Returns:
        dict: GeoJSON Polygon type data (not FeatureCollection).
    """

    polygons = []
    crs = None
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save zip to temporary file and extract
        zip_path = os.path.join(tmpdir, "input.zip")
        with open(zip_path, "wb") as f:
            f.write(shp_zip_bytes)
        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(tmpdir)
        # Find .shp file
        shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
        if not shp_files:
            return None
        shp_path = os.path.join(tmpdir, shp_files[0])
        with fiona.open(shp_path, 'r') as src:
            crs = src.crs
            for feat in src:
                if feat['geometry'] and feat['geometry']['type'] == 'Polygon':
                    polygons.append(feat['geometry'])
        if not polygons:
            return None
        geojson = {
            'type': 'Polygon',
            'coordinates': polygons[0]['coordinates']
        }
        if crs:
            geojson['crs'] = crs
        return geojson
