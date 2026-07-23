import json 
import zipfile
import tempfile
import os
from osgeo import ogr
from kebun.models import Kebun
from django import forms
from django.contrib.gis.geos import GEOSGeometry


class PetaForm(forms.ModelForm):
    # Optional file uploads
    shapefile_upload = forms.FileField(
        required=False, 
        help_text="Upload shapefile (.zip) atau KML (.kml)"
    )
    
    class Meta:
        model = Kebun
        fields = ['petani', 'geom']
    
    def clean(self):
        cleaned_data = super().clean()
        shapefile_upload = cleaned_data.get('shapefile_upload')
        geom = cleaned_data.get('geom')
        
        # Priority: shapefile upload > geom
        if shapefile_upload:
            geometry = self._process_shapefile_upload(shapefile_upload)
            cleaned_data['geom'] = geometry
        elif not geom:
            raise forms.ValidationError(
                "Harap upload shapefile atau masukkan data geometry"
            )
        
        return cleaned_data
    
    def _process_shapefile_upload(self, uploaded_file):
        """Process uploaded shapefile (.zip or .shp) or KML (.kml)"""
        filename = uploaded_file.name.lower()
        
        if filename.endswith('.zip'):
            return self._process_zip_shapefile(uploaded_file)
        elif filename.endswith('.kml'):
            return self._process_kml_file(uploaded_file)
        elif filename.endswith('.shp'):
            raise forms.ValidationError(
                "Upload file .shp dalam format .zip bersama file pendampingnya"
            )
        else:
            raise forms.ValidationError(
                "Format file tidak didukung. Upload .zip (shapefile) atau .kml"
            )
    
    def _process_zip_shapefile(self, zip_file):
        """Extract and process shapefile from zip"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract zip
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find .shp file
                shp_path = self._find_shp_file(temp_dir)
                if not shp_path:
                    raise forms.ValidationError(
                        "File .shp tidak ditemukan dalam zip"
                    )
                
                # Read shapefile and convert to geometry
                geometry = self._read_shapefile_to_geometry(shp_path)
                
                return geometry
                
        except zipfile.BadZipFile:
            raise forms.ValidationError("File zip tidak valid")
        except Exception as e:
            raise forms.ValidationError(f"Error: {str(e)}")
    
    def _find_shp_file(self, directory):
        """Find .shp file in directory"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.shp'):
                    return os.path.join(root, file)
        return None
    
    def _read_shapefile_to_geometry(self, shp_path):
        """Read shapefile and return Django Geometry"""
        try:
            # Open with GDAL/OGR
            driver = ogr.GetDriverByName('ESRI Shapefile')
            datasource = driver.Open(shp_path, 0)
            
            if datasource is None:
                raise forms.ValidationError("Tidak dapat membaca shapefile")
            
            layer = datasource.GetLayer()
            feature_count = layer.GetFeatureCount()
            
            if feature_count == 0:
                raise forms.ValidationError("Shapefile tidak memiliki features")
            
            if feature_count > 1:
                raise forms.ValidationError(
                    f"Shapefile memiliki {feature_count} features. "
                    "Hanya 1 polygon yang diperbolehkan"
                )
            
            # Get first feature
            feature = layer.GetNextFeature()
            geom_ogr = feature.GetGeometryRef()
            
            if geom_ogr is None:
                raise forms.ValidationError("Feature tidak memiliki geometry")
            
            # Convert to GeoJSON then to Django Geometry
            geojson_str = geom_ogr.ExportToJson()
            geojson = json.loads(geojson_str)
            
            geom = GEOSGeometry(json.dumps(geojson), srid=4326)
            
            # Transform if needed
            if geom.srid and geom.srid != 4326:
                geom.transform(4326)
            
            # Handle MultiPolygon
            if geom.geom_type == 'MultiPolygon':
                if len(geom) == 1:
                    geom = geom[0]
                else:
                    raise forms.ValidationError(
                        "MultiPolygon tidak didukung"
                    )
            
            # Validate Polygon only
            if geom.geom_type != 'Polygon':
                raise forms.ValidationError(
                    f"Tipe geometry '{geom.geom_type}' tidak didukung"
                )
            
            # Clean up
            datasource = None
            
            return geom
            
        except Exception as e:
            raise forms.ValidationError(f"Error: {str(e)}")

    def _process_kml_file(self, kml_file):
        """Process uploaded KML file and return Django Geometry"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                kml_path = os.path.join(temp_dir, 'input.kml')
                with open(kml_path, 'wb') as f:
                    f.write(kml_file.read())

                # Try LIBKML first (more spec-compliant), fallback to KML driver
                datasource = None
                for driver_name in ('LIBKML', 'KML'):
                    driver = ogr.GetDriverByName(driver_name)
                    if driver:
                        datasource = driver.Open(kml_path, 0)
                        if datasource:
                            break

                if datasource is None:
                    raise forms.ValidationError("Tidak dapat membaca file KML")

                # Collect polygon features across all layers
                # Use ogr.GT_Flatten() to normalize 2.5D/3D/ISO variants
                # (e.g. wkbPolygon25D, wkbPolygonZ=1003) to their 2D base type
                geometries = []
                for layer_idx in range(datasource.GetLayerCount()):
                    layer = datasource.GetLayerByIndex(layer_idx)
                    layer.ResetReading()
                    for feature in layer:
                        geom_ogr = feature.GetGeometryRef()
                        if geom_ogr is None:
                            continue
                        flat_type = ogr.GT_Flatten(geom_ogr.GetGeometryType())
                        if flat_type in (ogr.wkbPolygon, ogr.wkbMultiPolygon):
                            geometries.append(geom_ogr.Clone())

                datasource = None

                if not geometries:
                    raise forms.ValidationError(
                        "Tidak ada geometry Polygon yang ditemukan dalam file KML"
                    )

                if len(geometries) > 1:
                    raise forms.ValidationError(
                        f"File KML memiliki {len(geometries)} features. "
                        "Hanya 1 polygon yang diperbolehkan"
                    )

                # KML coordinates include altitude (Z). Strip Z at OGR level
                # before converting to GEOSGeometry to match 2D PostGIS column.
                geom_ogr = geometries[0]
                geom_ogr.FlattenTo2D()
                geom = GEOSGeometry(geom_ogr.ExportToJson(), srid=4326)

                if geom.srid and geom.srid != 4326:
                    geom.transform(4326)

                if geom.geom_type == 'MultiPolygon':
                    if len(geom) == 1:
                        geom = geom[0]
                    else:
                        raise forms.ValidationError("MultiPolygon tidak didukung")

                if geom.geom_type != 'Polygon':
                    raise forms.ValidationError(
                        f"Tipe geometry '{geom.geom_type}' tidak didukung"
                    )

                return geom

        except forms.ValidationError:
            raise
        except Exception as e:
            raise forms.ValidationError(f"Error memproses KML: {str(e)}")