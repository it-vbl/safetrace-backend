from django.contrib.gis.db import models
from utils.choices import DeforestationSourceType


class AdmDesaArea(models.Model):
    provinsi = models.CharField(max_length=50)
    kabupaten = models.CharField(max_length=50)
    kecamatan = models.CharField(max_length=50)
    desa = models.CharField(max_length=50)
    geom = models.MultiPolygonField(srid=4326)
    properties = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.desa}-{self.kecamatan}-{self.kabupaten}-{self.provinsi}"


class DeforeStation(models.Model):
    label = models.CharField(max_length=255, help_text="Label like a identifier (id or something)")
    geom = models.MultiPolygonField(srid=4326)
    source_type = models.CharField(max_length=255, choices=DeforestationSourceType.choices, default=DeforestationSourceType.GLAD)
    area_ha = models.FloatField(default=0.0)
    properties = models.JSONField(default=dict)    
    date = models.DateField()
    raw_data = models.JSONField(default=dict)
    administrative_area = models.JSONField(
        default=dict, help_text="Administrative area info like province, regency, district, village")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.label} - {self.date}"

    def save_adm_desa_data(self, adm_desa_data):
        self.administrative_area = adm_desa_data
        self.save()

    @staticmethod
    def _extract_layer_names(intersections):
        if not isinstance(intersections, list):
            return []

        excluded_slugs = {'kecamatan', 'kabupaten', 'desa'}
        names = []
        for item in intersections:
            if not isinstance(item, dict):
                continue

            slug = str(item.get('slug', '')).strip().lower()
            if slug in excluded_slugs:
                continue

            name = item.get('name')
            if name:
                names.append(str(name))
        return names

    @staticmethod
    def _extract_impacted_kebun_names(impacted_kebun):
        if not isinstance(impacted_kebun, list):
            return []

        kebun_names = []
        for item in impacted_kebun:
            if not isinstance(item, dict):
                continue

            id_kebun = item.get('id_kebun')
            petani = item.get('petani')
            if id_kebun and petani:
                kebun_names.append(f"Kebun {petani}: {id_kebun}")
        return kebun_names

    def get_obyek_terdampak(self):
        intersections = self.raw_data.get('layer_static_intersections', [])
        impacted_kebun = self.raw_data.get('impacted_kebun', [])
        layer_names = self._extract_layer_names(intersections)
        kebun_names = self._extract_impacted_kebun_names(impacted_kebun)
        return ', '.join(layer_names + kebun_names)
    
    @property
    def centroid_point(self):
        if self.geom:
            centroid = self.geom.centroid
            return {
                "type": "Point",
                "coordinates": [centroid.x, centroid.y]
            }
        return None
    
    @property
    def provinsi(self):
        return self.administrative_area.get('ProvID', '')
    
    @property
    def kabupaten(self):
        return self.administrative_area.get('DistrictID', '')
    
    @property
    def kecamatan(self):
        return self.administrative_area.get('SubdistID', '')
    
    @property
    def desa(self):
        return self.administrative_area.get('VillageID', '')
    
