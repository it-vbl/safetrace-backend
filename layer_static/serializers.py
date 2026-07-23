import json
from django.core.files.base import ContentFile
from rest_framework import serializers
from layer_static.models import LayerStatic, PetaStatis
from rest_framework.exceptions import ValidationError
from utils.shp_converter import shp_zip_to_geojson


class LayerStaticListSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerStatic
        fields = ('id', 'name', 'slug', 'order')
        
        
class LayerStaticSerializer(serializers.ModelSerializer):
    geom = serializers.SerializerMethodField('get_geojson')

    class Meta:
        model = LayerStatic
        fields = ('id', 'name', 'geom')

    def get_geojson(self, obj):
        return obj.to_geojson()


class PetaStatisSerializer(serializers.ModelSerializer):
    geom = serializers.SerializerMethodField('get_geojson', read_only=True)

    class Meta:
        model = PetaStatis
        fields = ('id', 'nama', 'geom', 'geojson_file', 'created_at', 'updated_at')

    def get_geojson(self, obj):
        return obj.to_geojson()

    def get_geojson(self, obj):
        return obj.to_geojson()
    
    def validate_geojson_file(self, value):
        """
        Validate that the uploaded file is a .geojson, .json, or .zip shapefile.
        If it is a .zip shapefile, it will be converted to GeoJSON.
        """
        if not value:
            return value
        
        # Validate the file extension
        file_name = value.name.lower()
        is_geojson = file_name.endswith('.geojson') or file_name.endswith('.json')
        is_zip = file_name.endswith('.zip')
        
        if not (is_geojson or is_zip):
            raise ValidationError('File harus berekstensi .geojson, .json, atau .zip (shapefile)')
        
        # Validate the file size (maximum 10MB)
        if value.size > 10 * 1024 * 1024:
            raise ValidationError('Ukuran file tidak boleh lebih dari 10MB')
        
        # If the file is .zip, validate the shapefile and convert it to GeoJSON
        if is_zip:
            try:
                value.seek(0)
                zip_bytes = value.read()
                value.seek(0)
                
                # Convert the shapefile zip to GeoJSON
                geojson_data = shp_zip_to_geojson(zip_bytes)
                
                # Save the GeoJSON to a new file
                geojson_content = json.dumps(geojson_data, indent=2)
                new_filename = file_name.replace('.zip', '.geojson')
                
                # Create a new ContentFile with the GeoJSON
                new_file = ContentFile(geojson_content.encode('utf-8'), name=new_filename)
                return new_file
                
            except ValueError as e:
                raise ValidationError(f'Shapefile validation error: {str(e)}')
            except Exception as e:
                raise ValidationError(f'Error convert shapefile ke GeoJSON: {str(e)}')
        
        # Validate the GeoJSON format for .json/.geojson files
        if is_geojson:
            try:
                value.seek(0)
                content = value.read()
                value.seek(0)  # Reset pointer for the next processing step
                
                geojson_data = json.loads(content)
                
                # Check whether it has a valid type
                if 'type' not in geojson_data:
                    raise ValidationError('File GeoJSON harus memiliki property "type"')
                
                valid_types = ['Feature', 'FeatureCollection', 'Point', 'LineString', 'Polygon', 
                              'MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection']
                
                if geojson_data['type'] not in valid_types:
                    raise ValidationError(f'Type GeoJSON tidak valid. Harus salah satu dari: {", ".join(valid_types)}')
                
                # If FeatureCollection, ensure features exist
                if geojson_data['type'] == 'FeatureCollection':
                    if 'features' not in geojson_data:
                        raise ValidationError('FeatureCollection harus memiliki property "features"')
                    if not isinstance(geojson_data['features'], list):
                        raise ValidationError('Property "features" harus berupa array')
                
                # If Feature, ensure geometry exists
                if geojson_data['type'] == 'Feature':
                    if 'geometry' not in geojson_data:
                        raise ValidationError('Feature harus memiliki property "geometry"')
                
            except json.JSONDecodeError:
                raise ValidationError('File bukan JSON yang valid')
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError(f'GeoJSON validation error: {str(e)}')
        
        return value

class PetaStatisListSerializer(serializers.ModelSerializer):

    class Meta:
        model = PetaStatis
        fields = ('id', 'nama', 'geojson_file', 'created_at', 'updated_at')
