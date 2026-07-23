import json
import django_rq
from django.http import FileResponse
from datetime import datetime
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from utils.serializers import custom_response
from utils.decorators import role_required
from utils.shp_converter import geojson_to_shp_zip_bytes
from utils.whisp import WHISPService
from django.conf import settings
from utils.choices import JenisLegalitas, UserRole
from utils.mixins import DownloadListMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from kebun.serializers import (
    KebunSerializer, LampiranKebunSerializer, LampiranKebunCreateUpdateSerializer, 
    KebunGeomSerializer, KebunListSerializer, KebunDeforestationAnalysisSerializer
)
from kebun.models import Kebun, Lampiran
from kebun.forms import PetaForm
from django.db.models import Q


class KebunListView(generics.ListAPIView):
    serializer_class = KebunListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    
    def get_queryset(self):
        queryset = Kebun.objects.all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(kabupaten_id=kab_sekadau_id)

        search = self.request.query_params.get('search', None)
        kelompok_tani = self.request.query_params.get('kelompok_tani', None)
        is_rspo = self.request.query_params.get('rspo', None)
        is_ispo = self.request.query_params.get('ispo', None)
        petani_id = self.request.query_params.get('petani_id', None)
        jenis_legalitas = self.request.query_params.get('jenis_legalitas', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if kelompok_tani:
            queryset = queryset.filter(petani__nama_kelompok__icontains=kelompok_tani)
            
        if is_rspo:
            queryset = queryset.filter(is_rspo__icontains=is_rspo)

        if is_ispo:
            queryset = queryset.filter(is_ispo__icontains=is_ispo)
        
        if petani_id:
            queryset = queryset.filter(petani_id=petani_id)
            
        if jenis_legalitas:
            queryset = queryset.filter(jenis_legalitas=jenis_legalitas)

        if search:
            queryset = queryset.filter(
                Q(petani__nama__icontains=search) | Q(petani__id_petani__icontains=search) |
                Q(id_kebun__icontains=search)
            )
            
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun",
            data=response.data,
            status="success"
        ), status=response.status_code)


class KebunDownloadListView(DownloadListMixin, KebunListView):
    filename_download = "kebun_data_download"
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create_header(self):
        return [
            'ID Kebun',
            'ID Petani',
            'Nama Petani',
            'Kelompok Tani',
            'Lokasi Kebun',
            'Luas Kebun (m2)',
            'Waktu Tanam',
            'Is Rspo',
            'Is Ispo',
            'Risiko Deforestasi',
            'Jenis Legalitas',
            'Pemilik Legalitas',
            'Nomor Legalitas',
            'Nomor Stdb',
            'Tanggal Diperbarui'
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['id_kebun'],
                item['petani_id'],
                item['nama_petani'],
                item['kelompok_tani'],
                item['lokasi_kebun'],
                item['luas_kebun'],
                item['waktu_tanam'],
                item['is_rspo'],
                item['is_ispo'],
                item['risiko_deforestasi'],
                item['jenis_legalitas_label'],
                item['pemilik_legalitas'],
                item['nomor_legalitas'],
                item['nomor_stdb'],
                item['updated_at'],
            ])
        return list_data


class KebunDetailView(generics.RetrieveAPIView):
    serializer_class = KebunSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    queryset = Kebun.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun",
            data=response.data,
            status="success"
        ), status=response.status_code)        


class KebunCreateView(generics.CreateAPIView):
    serializer_class = KebunSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        data['petani'] = data.get('petani_id')
        
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(custom_response(
            status="success",
            message="Berhasil menambahkan data Kebun",
            data=serializer.data
        ), status=status.HTTP_201_CREATED, headers=headers)


class KebunUpdateView(generics.UpdateAPIView):
    serializer_class = KebunSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Kebun.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = dict(request.data)
        data['petani'] = data.get('petani_id')
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah data kebun",
            data=serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class KebunDeleteView(generics.DestroyAPIView):
    serializer_class = KebunSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Kebun.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data Kebun",
            data=None,
            status="success"
        ), status=response.status_code)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class KebunGeomCreateUpdateView(generics.UpdateAPIView):
    serializer_class = KebunGeomSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Kebun.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = dict(request.data)
        data['petani'] = data.get('petani_id')
        
        # Convert GeoJSON to GEOSGeometry
        try:
            geojson = data.get("geom")
            geom = GEOSGeometry(json.dumps(geojson))
            if geom.empty:
                data["geom"] = {}
                return data

            if geom.srid != 4326:
                geom.transform(4326)
            data["geom"] = geom
        except Exception:
            pass
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)
        
        # Trigger WHISP analysis if geom is updated
        whisp_service = WHISPService()
     
        queue = django_rq.get_queue('default')
        queue.enqueue(
            whisp_service.process_whisp_analysis,
            instance.id
        )
        
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah data peta kebun",
            data=serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class KebunGeomUploadShapefileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    form_class = PetaForm
    serializer_class = KebunGeomSerializer
    
    def get_data_post(self, request):
        # Avoid deep copy to prevent pickle errors with uploaded files
        # Use get() to extract single values from QueryDict, not lists
        data = request.data.copy()
        data["petani"] = data.get("petani_id")
        return data

    def post(self, request, pk):
        data = self.get_data_post(request)
        try:
            kebun = Kebun.objects.get(pk=pk, petani_id=data["petani_id"])
        except Kebun.DoesNotExist:
            return Response(
                custom_response(status="error", message="Data Kebun tidak ditemukan."),
                status=status.HTTP_404_NOT_FOUND,
            )
        
        form = self.form_class(self.get_data_post(request), request.FILES, instance=kebun)
        if not form.is_valid():
            return Response(
                custom_response(
                    status="error",
                    message="Permintaan Tidak Valid. Harap periksa data Anda",
                    errors=form.errors,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Save kebun
        kebun = form.save()
        
        # Trigger WHISP analysis if geom is updated
        whisp_service = WHISPService()
     
        queue = django_rq.get_queue('default')
        queue.enqueue(
            whisp_service.process_whisp_analysis,
            kebun.id
        )
        
        # make response
        serializer = self.serializer_class(kebun)
        return Response(
            custom_response(
                status="success", message="Berhasil mengunggah shapefile kebun", data=serializer.data
            ),
            status=status.HTTP_200_OK,
        )


class KebunDownloadSHPView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]

    def get(self, request, pk):
        try:
            kebun = Kebun.objects.get(pk=pk)
        except Kebun.DoesNotExist:
            return Response(
                custom_response(status="error", message="Data kebun tidak ditemukan."),
                status=status.HTTP_404_NOT_FOUND,
            )

        if not kebun.geom:
            return Response(
                custom_response(
                    status="error", message="Data geometry kebun tidak tersedia."
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": json.loads(kebun.geom.geojson),
                    "properties": {
                        "id": kebun.id,
                        "nama": getattr(kebun, "nama", ""),
                        "no_dokumen": getattr(kebun, "no_dokumen", ""),
                    },
                }
            ],
        }

        shp_zip_bytes = geojson_to_shp_zip_bytes(geojson)
        shp_zip_bytes.seek(0)
        response = FileResponse(shp_zip_bytes, content_type="application/zip")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        response["Content-Disposition"] = (
            f"attachment; filename=kebun_{pk}_{timestamp}.zip"
        )
        return response


class KebunDeforestationAnalysisView(generics.RetrieveAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    queryset = Kebun.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Trigger WHISP analysis if geom is updated
        whisp_service = WHISPService()
     
        queue = django_rq.get_queue('default')
        queue.enqueue(
            whisp_service.process_whisp_analysis,
            instance.id
        )
        
        return Response(custom_response(
            message="Proses Analisa Deforestasi WHISP telah dimulai. "
                    "Silakan cek pada endpoint STATUS untuk melihat progresnya.",
            data=None,
            status="success"
        ), status=status.HTTP_200_OK)
        

class KebunDeforestationStatusView(generics.RetrieveAPIView):
    serializer_class = KebunDeforestationAnalysisSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    queryset = Kebun.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        defo_analysis = instance.deforestation_analysis
        serializer = self.get_serializer(defo_analysis)
        return Response(custom_response(
            message="Status Analisa Deforestasi WHISP",
            data=serializer.data,
            status="success"
        ), status=status.HTTP_200_OK)


class KebunDeforestationPropertiesView(generics.RetrieveAPIView):
    serializer_class = KebunDeforestationAnalysisSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    queryset = Kebun.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = {'whisp_properties': instance.whisp_properties}
        return Response(custom_response(
            message="Status Analisa Deforestasi WHISP",
            data=data,
            status="success"
        ), status=status.HTTP_200_OK)
        
        
class LampiranKebunCreateView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Explicit parser for file upload
    
    def get_serializer_class(self):
        """Use different serializers for input and output"""
        if self.request.method == 'POST':
            return LampiranKebunCreateUpdateSerializer
        return LampiranKebunSerializer
    
    def create(self, request, *args, **kwargs):
        # Avoid deep copy to prevent pickle errors with uploaded files
        # Use get() to extract single values from QueryDict, not lists
        data = request.data.copy()
        data['kebun'] = data['kebun_id']
        
        # Use input serializer for validation
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_create(serializer)
        
        # Use output serializer for response
        instance = serializer.instance
        output_serializer = LampiranKebunSerializer(instance)
        headers = self.get_success_headers(output_serializer.data)
        return Response(custom_response(
            status="success",
            message="Berhasil menambahkan lampiran kebun",
            data=output_serializer.data
        ), status=status.HTTP_201_CREATED, headers=headers)


class LampiranKebunUpdateView(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Kebun.objects.all()
    
    def get_serializer_class(self):
        """Use different serializers for input and output"""
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return LampiranKebunCreateUpdateSerializer
        return LampiranKebunSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        kebun = self.get_object()
        instance = kebun.lampiran
        # Avoid deep copy to prevent pickle errors with uploaded files
        # Use get() to extract single values from QueryDict, not lists
        data = request.data.copy()
        data['kebun'] = kebun.id
        
        # Use input serializer for validation
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)
        
        # Use output serializer for response
        output_serializer = LampiranKebunSerializer(instance)
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah lampiran kebun",
            data=output_serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)    


class LampiranKebunDetailView(generics.RetrieveAPIView):
    serializer_class = LampiranKebunSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    queryset = Kebun.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        kebun = self.get_object()
        lampiran = getattr(kebun, 'lampiran', None)
        if not lampiran:
            return Response(custom_response(
                message="Lampiran kebun tidak ditemukan",
                data=None,
                status="error"
            ), status=status.HTTP_404_NOT_FOUND)
            
        lampiran = kebun.lampiran
        
        serializer = self.get_serializer(lampiran)
        return Response(custom_response(
            message="Berhasil mendapatkan data lampiran kebun",
            data=serializer.data,
            status="success"
        ), status=status.HTTP_200_OK)


class KebunDokumenStatisticView(generics.GenericAPIView):
    """
    View for kebun document completeness statistics.
    Shows counts and percentages of kebun records that have completed:
    - Land document (file_legalitas)
    - STDB (nomor_stdb or file_stdb)
    - SHM (jenis_legalitas = SHM)
    - SKT (jenis_legalitas = SKT)
    - TS (titik_koordinat)
    - Map (geom)
    """
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
        
        # Count kebun records that have completed each document
        
        # Land document - from file_legalitas attachment
        jumlah_lahan = Lampiran.objects.filter(
            kebun__in=queryset,
            file_legalitas__isnull=False
        ).exclude(file_legalitas='').count()
        
        # STDB - from kebun nomor_stdb (already filled STDB number)
        jumlah_stdb = queryset.filter(
            nomor_stdb__isnull=False
        ).exclude(nomor_stdb='').count()
        
        # SHM - from kebun jenis_legalitas = SHM
        jumlah_shm = queryset.filter(
            jenis_legalitas=JenisLegalitas.SHM
        ).count()
        
        # SKT - from kebun jenis_legalitas = SKT  
        jumlah_skt = queryset.filter(
            jenis_legalitas=JenisLegalitas.SKT
        ).count()
        
        # TS (coordinate point) - from kebun titik_koordinat
        jumlah_ts = queryset.filter(
            titik_koordinat__isnull=False
        ).count()
        
        # Map - from kebun geom (map polygon)
        jumlah_peta = queryset.filter(
            geom__isnull=False
        ).count()
        
        # Calculate percentages
        persentase_lahan = round((jumlah_lahan / total_kebun * 100), 2) if total_kebun > 0 else 0
        persentase_stdb = round((jumlah_stdb / total_kebun * 100), 2) if total_kebun > 0 else 0
        persentase_shm = round((jumlah_shm / total_kebun * 100), 2) if total_kebun > 0 else 0
        persentase_skt = round((jumlah_skt / total_kebun * 100), 2) if total_kebun > 0 else 0
        persentase_ts = round((jumlah_ts / total_kebun * 100), 2) if total_kebun > 0 else 0
        persentase_peta = round((jumlah_peta / total_kebun * 100), 2) if total_kebun > 0 else 0
        
        response_data = {
            'lahan': {
                'jumlah': jumlah_lahan,
                'persentase': persentase_lahan
            },
            'stdb': {
                'jumlah': jumlah_stdb,
                'persentase': persentase_stdb
            },
            'shm': {
                'jumlah': jumlah_shm,
                'persentase': persentase_shm
            },
            'skt': {
                'jumlah': jumlah_skt,
                'persentase': persentase_skt
            },
            'ts': {
                'jumlah': jumlah_ts,
                'persentase': persentase_ts
            },
            'peta': {
                'jumlah': jumlah_peta,
                'persentase': persentase_peta
            },
            'total_kebun': total_kebun
        }
        
        return Response(custom_response(
            message="Berhasil mendapatkan statistik dokumen kebun",
            data=response_data,
            status="success"
        ), status=status.HTTP_200_OK)
