from rest_framework import serializers

from accounts.models import CustomUser
from .models import LaporanStatistik
from petani.serializers import PetaniSerializer, PekerjaPetaniListSerializerV2, DiklatSerializer
from kebun.serializers import KebunListSerializer
from gap.serializers import (
    KebunGAPestisidaListSerializer, KebunGAPProduksiListSerializer, KebunGALB3ListSerializer,KebunGAPPupukListSerializer
)
from penjualan.serializers import AngkutanSerializer

class LaporanStatistikCreatedBySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'name']


class LaporanStatistikCreateInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaporanStatistik
        fields = ['bulan', 'tahun', 'judul', 'kebutuhan']

    def create(self, validated_data):
        request = self.context.get('request')
        created_by = request.user if request and getattr(request.user, 'is_authenticated', False) else None
        return LaporanStatistik.objects.create(created_by=created_by, **validated_data)


class LaporanStatistikSerializer(serializers.ModelSerializer):
    created_by = LaporanStatistikCreatedBySerializer(read_only=True)

    class Meta:
        model = LaporanStatistik
        fields = [
            'id',
            'bulan',
            'tahun',
            'judul',
            'kebutuhan',
            'file_excel',
            'created_by',
            'created_at',
            'updated_at',
        ]


class LaporanPetaniSerializer(serializers.Serializer):
    data_petani = PetaniSerializer()
    data_kebun = KebunListSerializer(many=True)
    data_produksi = KebunGAPProduksiListSerializer(many=True)
    data_pestisida = KebunGAPestisidaListSerializer(many=True)
    data_pupuk = KebunGAPPupukListSerializer(many=True)
    data_lb3 = KebunGALB3ListSerializer(many=True)
    data_pekerja = PekerjaPetaniListSerializerV2(many=True)
    data_diklat = DiklatSerializer(many=True)
    # data_penjualan = AngkutanSerializer(many=True)
