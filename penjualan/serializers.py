from django.conf import settings
from rest_framework import serializers
from django.db import transaction
from .models import KelompokPenyetor, Angkutan, Pabrik, Lampiran
from utils.protected_medias import ConditionalSignedMediaMixin


class AngkutanSerializer(serializers.ModelSerializer):
    id_penjualan = serializers.IntegerField(source="id", read_only=True)
    kelompok_penyetor = serializers.SerializerMethodField()
    
    class Meta:
        model = Angkutan
        fields = '__all__'

    def get_kelompok_penyetor(self, obj):
        return obj.get_kelompok_penyetor()


class KelompokPenyetorSerializer(serializers.ModelSerializer):
    """Serializer for a single KelompokPenyetor"""
    # Read-only display fields
    anggota_count = serializers.SerializerMethodField()
    anggota_names = serializers.SerializerMethodField()
    
    class Meta:
        model = KelompokPenyetor
        fields = '__all__'
    
    def get_anggota_count(self, obj):
        return obj.anggota_petani.count()
    
    def get_anggota_names(self, obj):
        return [petani.nama for petani in obj.anggota_petani.all()]


class KelompokPenyetorBulkCreateSerializer(serializers.Serializer):
    """
    Serializer for bulk creating KelompokPenyetor
    Accepts a list of contributor groups
    """
    angkutan = serializers.PrimaryKeyRelatedField(
        queryset=Angkutan.objects.all(),
        required=False,
        allow_null=True
    )
    kelompok_data = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of kelompok penyetor data"
    )
    
    def validate_kelompok_data(self, value):
        """Validate the group data structure"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Kelompok data tidak boleh kosong")
        
        for idx, kelompok in enumerate(value):
            # Validate required fields
            if 'nama_kelompok' not in kelompok:
                raise serializers.ValidationError(
                    f"Item {idx}: nama_kelompok is required"
                )
            
            if 'anggota_petani' not in kelompok or not kelompok['anggota_petani']:
                raise serializers.ValidationError(
                    f"Item {idx}: anggota_petani is required and must not be empty"
                )
            
            # Validate the anggota_petani data type
            if not isinstance(kelompok['anggota_petani'], list):
                raise serializers.ValidationError(
                    f"Item {idx}: anggota_petani must be a list of IDs"
                )
        
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """Bulk create contributor groups"""
        angkutan = validated_data.get('angkutan')
        kelompok_data_list = validated_data.get('kelompok_data')
        
        created_kelompok = []
        errors = []
        
        for idx, kelompok_data in enumerate(kelompok_data_list):
            try:
                # Extract data
                nama_kelompok = kelompok_data.get('nama_kelompok')
                anggota_ids = kelompok_data.get('anggota_petani', [])
                
                # Create KelompokPenyetor
                kelompok = KelompokPenyetor.objects.create(
                    angkutan=angkutan,
                    nama_kelompok=nama_kelompok
                )
                
                # Add farmer members (ManyToMany)
                from petani.models import Petani
                anggota_petani = Petani.objects.filter(id__in=anggota_ids)
                
                if anggota_petani.count() != len(anggota_ids):
                    # There are invalid IDs
                    valid_ids = list(anggota_petani.values_list('id', flat=True))
                    invalid_ids = [id for id in anggota_ids if id not in valid_ids]
                    errors.append({
                        'index': idx,
                        'nama_kelompok': nama_kelompok,
                        'error': f'Invalid petani IDs: {invalid_ids}'
                    })
                    kelompok.delete()  # Roll back
                    continue
                
                kelompok.anggota_petani.set(anggota_petani)
                created_kelompok.append(kelompok)
                
            except Exception as e:
                errors.append({
                    'index': idx,
                    'nama_kelompok': kelompok_data.get('nama_kelompok', 'Unknown'),
                    'error': str(e)
                })
        
        return {
            'created': created_kelompok,
            'errors': errors,
            'success_count': len(created_kelompok),
            'error_count': len(errors)
        }


class KelompokPenyetorDetailSerializer(serializers.ModelSerializer):
    """Serializer with full details for the response"""
    anggota_petani = serializers.SerializerMethodField()
    
    class Meta:
        model = KelompokPenyetor
        fields = '__all__'
    
    def get_anggota_petani(self, obj):
        data = []
        for petani in obj.anggota_petani.all():
            data.append({
                'id': petani.id,
                'id_petani': petani.id_petani,
                'nama': petani.nama,
                'jns_kelamin': petani.jns_kelamin,
                'jns_kelamin_label': petani.get_jns_kelamin_display()
            })
        return data


class PabrikSerializer(serializers.ModelSerializer):
    """Serializer for Pabrik"""
    provinsi_label = serializers.CharField(source='get_provinsi_display', read_only=True)
    kabupaten_label = serializers.CharField(source='get_kabupaten_display', read_only=True)
    kecamatan_label = serializers.CharField(source='get_kecamatan_display', read_only=True)
    
    class Meta:
        model = Pabrik
        fields = '__all__'


class AngkutanPabrikSerializer(AngkutanSerializer):
    pabrik_data = PabrikSerializer(source='pabrik', read_only=True)

    class Meta:
        model = Angkutan
        fields = '__all__'


class LampiranSerializer(ConditionalSignedMediaMixin, serializers.ModelSerializer):
    file_1 = serializers.SerializerMethodField()
    thumb_1 = serializers.SerializerMethodField()
    file_2 = serializers.SerializerMethodField()
    thumb_2 = serializers.SerializerMethodField()
    file_3 = serializers.SerializerMethodField()
    thumb_3 = serializers.SerializerMethodField()
    file_4 = serializers.SerializerMethodField()
    thumb_4 = serializers.SerializerMethodField()
    file_5 = serializers.SerializerMethodField()
    thumb_5 = serializers.SerializerMethodField()
    file_6 = serializers.SerializerMethodField()
    thumb_6 = serializers.SerializerMethodField()

    class Meta:
        model = Lampiran
        fields = '__all__'

    def _signed_url(self, file_obj):
        if file_obj:
            return f"{settings.MEDIA_HOST}{self.get_media_url(file_obj, expires_in=3600)}"
        return ''

    def get_file_1(self, obj):
        return self._signed_url(obj.file_1)

    def get_thumb_1(self, obj):
        return self._signed_url(obj.thumb_1)

    def get_file_2(self, obj):
        return self._signed_url(obj.file_2)

    def get_thumb_2(self, obj):
        return self._signed_url(obj.thumb_2)

    def get_file_3(self, obj):
        return self._signed_url(obj.file_3)

    def get_thumb_3(self, obj):
        return self._signed_url(obj.thumb_3)

    def get_file_4(self, obj):
        return self._signed_url(obj.file_4)

    def get_thumb_4(self, obj):
        return self._signed_url(obj.thumb_4)

    def get_file_5(self, obj):
        return self._signed_url(obj.file_5)

    def get_thumb_5(self, obj):
        return self._signed_url(obj.thumb_5)

    def get_file_6(self, obj):
        return self._signed_url(obj.file_6)

    def get_thumb_6(self, obj):
        return self._signed_url(obj.thumb_6)


class LampiranCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lampiran
        fields = [
            'id',
            'angkutan',
            'file_1',
            'file_2',
            'file_3',
            'file_4',
            'file_5',
            'file_6',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            # Upsert flow is handled in view with update_or_create, so default
            # one-to-one unique validation must not block existing angkutan.
            'angkutan': {'validators': []},
        }