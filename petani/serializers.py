from django.conf import settings
from rest_framework import serializers
from utils.protected_medias import ConditionalSignedMediaMixin
from .models import Petani, Lampiran, Diklat, Pekerja


class PetaniSerializer(serializers.ModelSerializer):
    jns_kelamin_label = serializers.CharField(source='get_jns_kelamin_display', read_only=True)
    status_perkawinan_label = serializers.CharField(source='get_status_perkawinan_display', read_only=True)
    pendidikan_terakhir_label = serializers.CharField(source='get_pendidikan_terakhir_display', read_only=True)
    jumlah_kebun = serializers.IntegerField(source='get_jumlah_kebun', read_only=True)
    provinsi_nama = serializers.CharField(source='provinsi.nama', read_only=True, default=None)
    kabupaten_nama = serializers.CharField(source='kabupaten.nama', read_only=True, default=None)
    kecamatan_nama = serializers.CharField(source='kecamatan.nama', read_only=True, default=None)
    desa_nama = serializers.CharField(source='desa.nama', read_only=True, default=None)
    
    class Meta:
        model = Petani
        fields = '__all__'

    def to_internal_value(self, data):
        mutable_data = data.copy()
        for field_name in ["tgl_terbit_sppl", "tanggal_bergabung"]:
            value = mutable_data.get(field_name)
            if isinstance(value, str) and not value.strip():
                mutable_data[field_name] = None
        return super().to_internal_value(mutable_data)

    def validate_alamat(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Alamat harus diisi.")
        return value
    
    def create(self, validated_data):
        petani = super().create(validated_data)
        Diklat.objects.create(petani=petani)
        return petani


class PetaniDetailSerializer(serializers.ModelSerializer):
    jns_kelamin_label = serializers.CharField(source='get_jns_kelamin_display', read_only=True)
    status_perkawinan_label = serializers.CharField(source='get_status_perkawinan_display', read_only=True)
    luas_kebun = serializers.FloatField(source='get_luas_kebun', read_only=True)
    provinsi_nama = serializers.CharField(source='provinsi.nama', read_only=True, default=None)
    kabupaten_nama = serializers.CharField(source='kabupaten.nama', read_only=True, default=None)
    kecamatan_nama = serializers.CharField(source='kecamatan.nama', read_only=True, default=None)
    desa_nama = serializers.CharField(source='desa.nama', read_only=True, default=None)
    
    class Meta:
        model = Petani
        fields = '__all__'


class LampiranPetaniCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lampiran
        fields = ['id', 'petani', 'file_ktp', 'file_kk', 'file_nib']
        read_only_fields = ['id']


class LampiranPetaniSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    file_ktp = serializers.SerializerMethodField()
    thumb_ktp = serializers.SerializerMethodField()
    file_kk = serializers.SerializerMethodField()
    thumb_kk = serializers.SerializerMethodField()
    file_nib = serializers.SerializerMethodField()
    thumb_nib = serializers.SerializerMethodField()
    
    class Meta:
        model = Lampiran
        fields = '__all__'

    def get_file_ktp(self, obj):
        if obj.file_ktp:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_ktp, expires_in=3600)}"
            return url
        return ''

    def get_thumb_ktp(self, obj):
        if obj.thumb_ktp:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_ktp, expires_in=3600)}"
            return url
        return ''
    
    def get_file_kk(self, obj):
        if obj.file_kk:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_kk, expires_in=3600)}"
            return url
        return ''
    
    def get_thumb_kk(self, obj):
        if obj.thumb_kk:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_kk, expires_in=3600)}"
            return url
        return ''
    
    def get_file_nib(self, obj):
        if obj.file_nib:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.file_nib, expires_in=3600)}"
            return url
        return ''
    
    def get_thumb_nib(self, obj):
        if obj.thumb_nib:
            url = f"{settings.MEDIA_HOST}{self.get_media_url(obj.thumb_nib, expires_in=3600)}"
            return url
        return ''


class DiklatSerializer(serializers.ModelSerializer):
    id_petani = serializers.CharField(source='petani.id_petani', read_only=True)
    petani_id = serializers.IntegerField(source='petani.id', read_only=True)
    nama_petani = serializers.CharField(source='petani.nama', read_only=True)
    nama_kelompok = serializers.CharField(source='petani.nama_kelompok', read_only=True)
    jenis_kelamin = serializers.CharField(source='petani.jns_kelamin', read_only=True)
    jenis_kelamin_label = serializers.CharField(source='petani.get_jns_kelamin_display', read_only=True)
    
    class Meta:
        model = Diklat
        fields = '__all__'


class PekerjaPetaniListSerializer(serializers.ModelSerializer):
    id_petani = serializers.CharField(read_only=True)
    nama_petani = serializers.CharField(read_only=True, source='nama')
    jenis_kelamin_label = serializers.CharField(source='get_jns_kelamin_display', read_only=True)
    nama_kelompok = serializers.CharField(read_only=True)
    no_ktp = serializers.CharField(read_only=True)
    no_kk = serializers.CharField(read_only=True)
    luas_kebun = serializers.SerializerMethodField()
    jumlah_pekerja = serializers.SerializerMethodField()
    
    class Meta:
        model = Petani
        fields = ('id', 'id_petani', 'nama_petani', 'nama_kelompok', 'no_ktp', 'no_kk', 
                  'luas_kebun', 'jumlah_pekerja', 'jenis_kelamin_label')
    
    def get_luas_kebun(self, obj):
        first_kebun = obj.kebun_set.first()
        if first_kebun:
            return first_kebun.luas_area_geom
        return 0
    
    def get_jumlah_pekerja(self, obj):
        if hasattr(obj, 'pekerja'):
            return obj.pekerja.count()
        return 0
    

class PekerjaPetaniListSerializerV2(serializers.ModelSerializer):
    petani_id = serializers.IntegerField(read_only=True, source='petani.id')
    pemilik_kebun = serializers.CharField(read_only=True, source='petani.nama')
    kelompok_tani = serializers.CharField(read_only=True, source='petani.nama_kelompok')
    nama_pekerja = serializers.CharField(read_only=True, source='nama')
    jenis_kelamin_label = serializers.CharField(source='get_jns_kelamin_display', read_only=True)
    no_ktp = serializers.CharField(read_only=True)
    no_kk = serializers.CharField(read_only=True)
    umur = serializers.IntegerField(source='get_umur', read_only=True)
    status_pekerja_label = serializers.CharField(source='get_status_pekerja_display', read_only=True)
    
    class Meta:
        model = Pekerja
        fields = ('id', 'petani_id', 'pemilik_kebun', 'kelompok_tani', 'nama_pekerja', 
                  'jenis_kelamin_label', 'no_ktp', 'no_kk', 'umur', 'status_pekerja_label')


class PekerjaSerializer(serializers.ModelSerializer):
    jenis_kelamin_label = serializers.CharField(source='get_jns_kelamin_display', read_only=True)
    status_pekerja_label = serializers.CharField(source='get_status_pekerja_display', read_only=True)
    umur = serializers.IntegerField(source='get_umur', read_only=True)
    jenis_pekerjaan_label = serializers.SerializerMethodField()
    jenis_apd_label = serializers.SerializerMethodField()
    
    class Meta:
        model = Pekerja
        fields = '__all__'

    def get_jenis_pekerjaan_label(self, obj):
        from utils.choices import JenisPekerjaan

        labels = [choice.label for choice in JenisPekerjaan if choice.value in (obj.jenis_pekerjaan or [])]
        return ', '.join(labels)

    def get_jenis_apd_label(self, obj):
        from utils.choices import JenisAPD

        labels = [choice.label for choice in JenisAPD if choice.value in (obj.jenis_apd or [])]
        return ', '.join(labels)