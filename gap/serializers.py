from rest_framework import serializers
from .models import Produksi, PenggunaanPestisida, LB3, PenggunaanPupuk


class KebunGAPProduksiListSerializer(serializers.Serializer):
    kebun_id = serializers.IntegerField(source='id', read_only=True)
    id_kebun = serializers.CharField(read_only=True)
    nama_petani = serializers.CharField(source='petani.nama', read_only=True)
    kelompok_tani = serializers.CharField(source='petani.nama_kelompok', read_only=True)
    total_produksi = serializers.SerializerMethodField()
    umur_tanaman = serializers.IntegerField(source='get_umur_tanaman', read_only=True)
    prod_ha_th = serializers.SerializerMethodField()
    luas_kebun = serializers.CharField(source='luas', read_only=True)
    tahun_tanam = serializers.CharField(source='get_tahun_tanam', read_only=True)

    def __init__(self, *args, **kwargs):
        self.tahun = kwargs.pop('tahun', None)
        super().__init__(*args, **kwargs)
        
    def get_total_produksi(self, obj):
        return obj.get_total_produksi_gap(self.tahun)
    
    def get_prod_ha_th(self, obj):
        return obj.get_prod_ha_year_gap(self.tahun)


class KebunGAPestisidaListSerializer(serializers.Serializer):
    kebun_id = serializers.IntegerField(source='id', read_only=True)
    id_kebun = serializers.CharField(read_only=True)
    nama_petani = serializers.CharField(source='petani.nama', read_only=True)
    kelompok_tani = serializers.CharField(source='petani.nama_kelompok', read_only=True)
    total_pestisida = serializers.SerializerMethodField()
    umur_tanaman = serializers.IntegerField(source='get_umur_tanaman', read_only=True)
    luas_kebun = serializers.CharField(source='luas', read_only=True)
    tahun_tanam = serializers.CharField(source='get_tahun_tanam', read_only=True)

    def __init__(self, *args, **kwargs):
        self.tahun = kwargs.pop('tahun', None)
        super().__init__(*args, **kwargs)
        
    def get_total_pestisida(self, obj):
        return obj.get_total_pestisida_gap(self.tahun)


class KebunGALB3ListSerializer(serializers.Serializer):
    kebun_id = serializers.IntegerField(source='id', read_only=True)
    id_kebun = serializers.CharField(read_only=True)
    nama_petani = serializers.CharField(source='petani.nama', read_only=True)
    kelompok_tani = serializers.CharField(source='petani.nama_kelompok', read_only=True)
    total_lb3 = serializers.SerializerMethodField()
    umur_tanaman = serializers.IntegerField(source='get_umur_tanaman', read_only=True)
    luas_kebun = serializers.CharField(source='luas', read_only=True)
    tahun_tanam = serializers.CharField(source='get_tahun_tanam', read_only=True)

    def __init__(self, *args, **kwargs):
        self.tahun = kwargs.pop('tahun', None)
        super().__init__(*args, **kwargs)
        
    def get_total_lb3(self, obj):
        return obj.get_total_lb3_gap(self.tahun)


class KebunGAPPupukListSerializer(serializers.Serializer):
    kebun_id = serializers.IntegerField(source='id', read_only=True)
    id_kebun = serializers.CharField(read_only=True)
    nama_petani = serializers.CharField(source='petani.nama', read_only=True)
    kelompok_tani = serializers.CharField(source='petani.nama_kelompok', read_only=True)
    total_pupuk = serializers.SerializerMethodField()
    umur_tanaman = serializers.IntegerField(source='get_umur_tanaman', read_only=True)
    jumlah_pokok = serializers.IntegerField(read_only=True)
    luas_kebun = serializers.CharField(source='luas', read_only=True)
    tahun_tanam = serializers.CharField(source='get_tahun_tanam', read_only=True)

    def __init__(self, *args, **kwargs):
        self.tahun = kwargs.pop('tahun', None)
        super().__init__(*args, **kwargs)
        
    def get_total_pupuk(self, obj):
        return obj.get_total_pupuk_gap(self.tahun)


class ProduksiSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Produksi
        fields = '__all__'
    
    def validate(self, data):
        """Custom validation"""
        # Check the unique constraint
        kebun = data.get('kebun')
        tahun = data.get('tahun')
        
        if self.instance is None:  # Create
            if Produksi.objects.filter(kebun=kebun, tahun=tahun).exists():
                raise serializers.ValidationError(
                    f"Data produksi untuk kebun {kebun.id_kebun} tahun {tahun} sudah ada"
                )
        
        return data


class PenggunaanPestisidaSerializer(serializers.ModelSerializer):
    total_sistemik = serializers.FloatField(read_only=True)
    total_kontak = serializers.FloatField(read_only=True)
    total_pestisida = serializers.FloatField(read_only=True)
    
    class Meta:
        model = PenggunaanPestisida
        fields = '__all__'
    
    def to_internal_value(self, data):
        data = {**data}
        for field_name, field in self.fields.items():
            if (
                isinstance(field, serializers.DecimalField)
                and not field.read_only
                and field_name in data
                and (data[field_name] is None or data[field_name] == '')
            ):
                data[field_name] = '0'
        return super().to_internal_value(data)
    
    def validate(self, data):
        """Custom validation"""
        # Check the unique constraint
        kebun = data.get('kebun')
        tahun = data.get('tahun')
        
        if self.instance is None:  # Create
            if PenggunaanPestisida.objects.filter(kebun=kebun, tahun=tahun).exists():
                raise serializers.ValidationError(
                    f"Data pestisida untuk kebun {kebun.id_kebun} tahun {tahun} sudah ada"
                )
        
        return data


class LB3Serializer(serializers.ModelSerializer):
    total_lb3 = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = LB3
        fields = '__all__'
        
    
    def validate(self, data):
        """Custom validation"""
        # Check the unique constraint
        kebun = data.get('kebun')
        tahun = data.get('tahun')
        
        if self.instance is None:  # Create
            if LB3.objects.filter(kebun=kebun, tahun=tahun).exists():
                raise serializers.ValidationError(
                    f"Data LB3 untuk kebun {kebun.id_kebun} tahun {tahun} sudah ada"
                )
        
        return data


# gap/serializers.py

class PenggunaanPupukSerializer(serializers.ModelSerializer):
    # Calculated fields - Session 1
    s1_total_pupuk = serializers.FloatField(read_only=True)
    
    # Calculated fields - Session 2
    s2_total_pupuk = serializers.FloatField(read_only=True)
    
    # Calculated fields - Session 3
    s3_total_pupuk = serializers.FloatField(read_only=True)
    
    # Calculated fields - Annual total
    total_npk = serializers.FloatField(read_only=True)
    total_nitrogen = serializers.FloatField(read_only=True)
    total_postpat = serializers.FloatField(read_only=True)
    total_kalium = serializers.FloatField(read_only=True)
    total_boron = serializers.FloatField(read_only=True)
    total_magnesium = serializers.FloatField(read_only=True)
    total_pupuk = serializers.FloatField(read_only=True)
    intensitas_per_ha = serializers.FloatField(read_only=True)
    umur_tanaman = serializers.IntegerField(read_only=True)
    
    # Display values for application time - Session 1
    s1_npk_waktu_label = serializers.CharField(
        source='get_s1_npk_waktu_aplikasi_display',
        read_only=True
    )
    s1_nitrogen_waktu_label = serializers.CharField(
        source='get_s1_nitrogen_waktu_aplikasi_display',
        read_only=True
    )
    s1_postpat_waktu_label = serializers.CharField(
        source='get_s1_postpat_waktu_aplikasi_display',
        read_only=True
    )
    s1_kalium_waktu_label = serializers.CharField(
        source='get_s1_kalium_waktu_aplikasi_display',
        read_only=True
    )
    s1_boron_waktu_label = serializers.CharField(
        source='get_s1_boron_waktu_aplikasi_display',
        read_only=True
    )
    s1_magnesium_waktu_label = serializers.CharField(
        source='get_s1_magnesium_waktu_aplikasi_display',
        read_only=True
    )
    
    # Display values for application time - Session 2
    s2_npk_waktu_label = serializers.CharField(
        source='get_s2_npk_waktu_aplikasi_display',
        read_only=True
    )
    s2_nitrogen_waktu_label = serializers.CharField(
        source='get_s2_nitrogen_waktu_aplikasi_display',
        read_only=True
    )
    s2_postpat_waktu_label = serializers.CharField(
        source='get_s2_postpat_waktu_aplikasi_display',
        read_only=True
    )
    s2_kalium_waktu_label = serializers.CharField(
        source='get_s2_kalium_waktu_aplikasi_display',
        read_only=True
    )
    s2_boron_waktu_label = serializers.CharField(
        source='get_s2_boron_waktu_aplikasi_display',
        read_only=True
    )
    s2_magnesium_waktu_label = serializers.CharField(
        source='get_s2_magnesium_waktu_aplikasi_display',
        read_only=True
    )
    
    # Display values for application time - Session 3
    s3_npk_waktu_label = serializers.CharField(
        source='get_s3_npk_waktu_aplikasi_display',
        read_only=True
    )
    s3_nitrogen_waktu_label = serializers.CharField(
        source='get_s3_nitrogen_waktu_aplikasi_display',
        read_only=True
    )
    s3_postpat_waktu_label = serializers.CharField(
        source='get_s3_postpat_waktu_aplikasi_display',
        read_only=True
    )
    s3_kalium_waktu_label = serializers.CharField(
        source='get_s3_kalium_waktu_aplikasi_display',
        read_only=True
    )
    s3_boron_waktu_label = serializers.CharField(
        source='get_s3_boron_waktu_aplikasi_display',
        read_only=True
    )
    s3_magnesium_waktu_label = serializers.CharField(
        source='get_s3_magnesium_waktu_aplikasi_display',
        read_only=True
    )
    
    class Meta:
        model = PenggunaanPupuk
        fields = '__all__'

    def to_internal_value(self, data):
        data = {**data}
        for field_name, field in self.fields.items():
            if (
                isinstance(field, serializers.DecimalField)
                and not field.read_only
                and field_name in data
                and (data[field_name] is None or data[field_name] == '')
            ):
                data[field_name] = '0'
        return super().to_internal_value(data)

    def validate(self, data):
        """Custom validation"""
        kebun = data.get('kebun')
        tahun = data.get('tahun')
        
        # Check the unique constraint on create
        if self.instance is None:
            if PenggunaanPupuk.objects.filter(kebun=kebun, tahun=tahun).exists():
                raise serializers.ValidationError(
                    f"Data pupuk untuk kebun {kebun.id_kebun} tahun {tahun} sudah ada"
                )
        else:
            # On update, check whether another record has the same kebun + year
            existing = PenggunaanPupuk.objects.filter(
                kebun=kebun, tahun=tahun
            ).exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError(
                    f"Data pupuk untuk kebun {kebun.id_kebun} tahun {tahun} sudah ada"
                )
        
        return data