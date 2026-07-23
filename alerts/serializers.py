from rest_framework import serializers
from .models import DeforeStation


class DeforeStationSerializer(serializers.ModelSerializer):
    titik_lokasi = serializers.SerializerMethodField(read_only=True)
    provinsi = serializers.CharField(read_only=True)
    kabupaten = serializers.CharField(read_only=True)
    kecamatan = serializers.CharField(read_only=True)
    desa = serializers.CharField(read_only=True)
    obyek_terdampak = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = DeforeStation
        exclude = ['raw_data', 'administrative_area', 'properties']

    def get_obyek_terdampak(self, obj):
        return obj.get_obyek_terdampak()
    
    def get_titik_lokasi(self, obj):
        return obj.centroid_point
