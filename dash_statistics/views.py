from django.db.models import Sum
from rest_framework import generics
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from petani.models import Petani
from kebun.models import Kebun
from alerts.models import DeforeStation
from utils.choices import JenisLegalitas
from utils.serializers import custom_response
from utils.decorators import role_required


class SidebarStatisticView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    
    def get(self, request, *args, **kwargs):
        # Get totals from different models
        total_petani = Petani.objects.count()
        total_kebun = Kebun.objects.count()
        total_alert = DeforeStation.objects.count()
        total_luas_deforestation = DeforeStation.objects.aggregate(
            total_luas=Sum('area_ha')
        )['total_luas'] or 0
        
        response_data = {
            'total_petani': total_petani,
            'total_kebun': total_kebun,
            'total_alert': total_alert,
            'total_luas_deforestation': round(total_luas_deforestation, 2)
        }
        
        return Response(custom_response(
            message="Berhasil mendapatkan statistik dashboard",
            data=response_data,
            status="success"
        ), status=status.HTTP_200_OK)


class KebunDokumenStatisticV2View(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    
    def get(self, request, *args, **kwargs):
        # Filter kebun
        queryset = Kebun.objects.all()

        # Optional filters
        petani_id = request.query_params.get('petani_id', None)
        if petani_id:
            queryset = queryset.filter(petani_id=petani_id)

        total_kebun = queryset.count()

        # Detect the kebun area field (adjust the priority if needed)
        kebun_fields = {f.name for f in Kebun._meta.fields}
        luas_field = next(
            (f for f in ['luas_ha', 'luas_lahan', 'luas_kebun', 'luas'] if f in kebun_fields),
            None
        )

        def sum_luas(qs):
            if not luas_field:
                return 0
            return round((qs.aggregate(total=Sum(luas_field))['total'] or 0), 2)

        # Total kebun area (for hectare percentages)
        total_luas_kebun = sum_luas(queryset)

        def hitung_stat(qs):
            qs = qs.distinct()
            jumlah_plot = qs.count()
            jumlah_ha = sum_luas(qs)
            persentase_plot = round((jumlah_plot / total_kebun * 100), 2) if total_kebun > 0 else 0
            persentase_ha = round((jumlah_ha / total_luas_kebun * 100), 2) if total_luas_kebun > 0 else 0
            return {
                'jumlah': {'plot': jumlah_plot, 'ha': jumlah_ha},
                'persentase': {'plot': persentase_plot, 'ha': persentase_ha}
            }

        # Land document - kebun with a file_legalitas attachment
        qs_lahan = queryset.filter(
            lampiran__file_legalitas__isnull=False
        ).exclude(
            lampiran__file_legalitas=''
        )

        # STDB - kebun with nomor_stdb filled in
        qs_stdb = queryset.filter(
            nomor_stdb__isnull=False
        ).exclude(
            nomor_stdb=''
        )

        # SHM
        qs_shm = queryset.filter(
            jenis_legalitas=JenisLegalitas.SHM
        )

        # SKT
        qs_skt = queryset.filter(
            jenis_legalitas=JenisLegalitas.SKT
        )

        # TS (coordinate point)
        qs_ts = queryset.filter(
            titik_koordinat__isnull=False
        )

        # Map (polygon)
        qs_peta = queryset.filter(
            geom__isnull=False
        )

        response_data = {
            'lahan': hitung_stat(qs_lahan),
            'stdb': hitung_stat(qs_stdb),
            'shm': hitung_stat(qs_shm),
            'skt': hitung_stat(qs_skt),
            'ts': hitung_stat(qs_ts),
            'peta': hitung_stat(qs_peta),
            'total_kebun': total_kebun,
            'total_ha': total_luas_kebun
        }

        return Response(custom_response(
            message="Berhasil mendapatkan statistik dokumen kebun",
            data=response_data,
            status="success"
        ), status=status.HTTP_200_OK)


