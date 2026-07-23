from django.conf import settings
from rest_framework import serializers
from .models import Kebun, Lampiran, KebunDeforestationAnalysis
from utils.protected_medias import ConditionalSignedMediaMixin


class KebunSerializer(serializers.ModelSerializer):
    petani_id = serializers.IntegerField(read_only=True, source='petani.id')
    nama_petani = serializers.CharField(source='petani.nama', read_only=True)
    kelompok_tani = serializers.CharField(source='petani.nama_kelompok', read_only=True)
    titik_koordinat = serializers.SerializerMethodField(read_only=True)
    jenis_legalitas_label = serializers.CharField(source='get_jenis_legalitas_display', read_only=True)
    risk_acrop = serializers.CharField(read_only=True)
    risk_pcrop = serializers.CharField(read_only=True)
    risk_timber = serializers.CharField(read_only=True)
    risiko_deforestasi = serializers.CharField(source='risk_pcrop', read_only=True)
    luas_kebun = serializers.FloatField(source='luas_area_geom', read_only=True)
    # STDB choice labels
    komoditas_label = serializers.CharField(source='get_komoditas_display', read_only=True)
    pola_tanam_label = serializers.CharField(source='get_pola_tanam_display', read_only=True)
    jenis_lahan_label = serializers.CharField(source='get_jenis_lahan_display', read_only=True)
    asal_benih_label = serializers.CharField(source='get_asal_benih_display', read_only=True)
    jenis_pupuk_label = serializers.CharField(source='get_jenis_pupuk_display', read_only=True)
    # Wilayah administratif labels
    provinsi_nama = serializers.CharField(source='get_provinsi_display', read_only=True)
    kabupaten_nama = serializers.CharField(source='get_kabupaten_display', read_only=True)
    kecamatan_nama = serializers.CharField(source='get_kecamatan_display', read_only=True)
    desa_nama = serializers.CharField(source='get_desa_display', read_only=True)

    class Meta:
        model = Kebun
        exclude = ['jenis_bibit']

    def get_titik_koordinat(self, obj):
        return obj.centroid_point


class KebunListSerializer(serializers.ModelSerializer):
    petani_id = serializers.IntegerField(read_only=True, source='petani.id')
    nama_petani = serializers.CharField(source='petani.nama', read_only=True)
    kelompok_tani = serializers.CharField(source='petani.nama_kelompok', read_only=True)
    luas_kebun = serializers.FloatField(source='luas_area_geom', read_only=True)
    jenis_legalitas_label = serializers.CharField(source='get_jenis_legalitas_display', read_only=True)
    titik_koordinat = serializers.SerializerMethodField(read_only=True)
    risk_acrop = serializers.CharField(read_only=True)
    risk_pcrop = serializers.CharField(read_only=True)
    risk_timber = serializers.CharField(read_only=True)
    risiko_deforestasi = serializers.CharField(source='risk_pcrop', read_only=True)

    class Meta:
        model = Kebun
        fields = ['id', 'titik_koordinat', 'id_kebun', 'petani_id', 'nama_petani', 'kelompok_tani', 'lokasi_kebun', 
                  'luas_kebun', 'luas_peta', 'waktu_tanam', 'is_rspo', 'is_ispo', 'jenis_legalitas_label',
                  'jenis_legalitas', 'pemilik_legalitas','nomor_legalitas', 'nomor_stdb', 'geom', 'created_at', 'updated_at',
                  'risk_acrop', 'risk_pcrop', 'risk_timber', 'risiko_deforestasi']

    def get_titik_koordinat(self, obj):
        return obj.centroid_point


class KebunGeomSerializer(serializers.ModelSerializer):
    petani_id = serializers.IntegerField(read_only=True, source='petani.id')
    titik_koordinat = serializers.SerializerMethodField(source='centroid_point', read_only=True)
    
    class Meta:
        model = Kebun
        fields = ['id', 'id_kebun', 'geom', 'titik_koordinat', 'petani_id']
        read_only_fields = ['id_kebun', 'id']

    def get_titik_koordinat(self, obj):
        return obj.centroid_point
    

class LampiranKebunCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lampiran
        fields = ['id', 'kebun', 'file_legalitas', 'file_stdb', 
                  'file_rspo', 'file_ispo', 'file_gambar_peta']
        read_only_fields = ['id']


class LampiranKebunSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    file_legalitas = serializers.SerializerMethodField()
    thumb_legalitas = serializers.SerializerMethodField()
    file_stdb = serializers.SerializerMethodField()
    thumb_stdb = serializers.SerializerMethodField()
    file_rspo = serializers.SerializerMethodField()
    thumb_rspo = serializers.SerializerMethodField()
    file_ispo = serializers.SerializerMethodField()
    thumb_ispo = serializers.SerializerMethodField()
    file_gambar_peta = serializers.SerializerMethodField()
    thumb_gambar_peta = serializers.SerializerMethodField()
    
    class Meta:
        model = Lampiran
        fields = '__all__'

    def get_file_legalitas(self, obj):
        if obj.file_legalitas:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_legalitas, expires_in=3600)}"
            return url
        return ''

    def get_thumb_legalitas(self, obj):
        if obj.thumb_legalitas:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_legalitas, expires_in=3600)}"
            return url
        return ''

    def get_file_stdb(self, obj):
        if obj.file_stdb:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_stdb, expires_in=3600)}"
            return url
        return ''

    def get_thumb_stdb(self, obj):
        if obj.thumb_stdb:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_stdb, expires_in=3600)}"
            return url
        return ''

    def get_file_rspo(self, obj):
        if obj.file_rspo:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_rspo, expires_in=3600)}"
            return url
        return ''

    def get_thumb_rspo(self, obj):
        if obj.thumb_rspo:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_rspo, expires_in=3600)}"
            return url
        return ''

    def get_file_ispo(self, obj):
        if obj.file_ispo:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_ispo, expires_in=3600)}"
            return url
        return ''

    def get_thumb_ispo(self, obj):
        if obj.thumb_ispo:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_ispo, expires_in=3600)}"
            return url
        return ''

    def get_file_gambar_peta(self, obj):
        if obj.file_gambar_peta:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_gambar_peta, expires_in=3600)}"
            return url
        return ''

    def get_thumb_gambar_peta(self, obj):
        if obj.thumb_gambar_peta:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_gambar_peta, expires_in=3600)}"
            return url
        return ''


class KebunDeforestationAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = KebunDeforestationAnalysis
        fields = '__all__'
