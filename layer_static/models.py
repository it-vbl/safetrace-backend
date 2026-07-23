import json
from django.db import models


class LayerStatic(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    geojson_file = models.FileField(upload_to="static_layers/", null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, blank=False, null=False,)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

    def to_geojson(self):
        self.geojson_file.open()
        self.geojson_file.seek(0)
        return json.load(self.geojson_file)


class PetaStatis(models.Model):
    nama = models.CharField(max_length=255)
    geojson_file = models.FileField(upload_to="static_layers/", null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.nama

    def to_geojson(self):
        self.geojson_file.open()
        self.geojson_file.seek(0)
        return json.load(self.geojson_file)

