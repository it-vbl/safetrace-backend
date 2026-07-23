from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from datetime import datetime
from django.utils import timezone
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.conf import settings
from utils.serializers import custom_response
from utils.decorators import role_required
from utils.mixins import DownloadListMixin, DateParserMixin
from utils.choices import UserRole
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import datetime
from penjualan.serializers import (
    AngkutanSerializer, 
    KelompokPenyetorSerializer,
    KelompokPenyetorBulkCreateSerializer,
    KelompokPenyetorDetailSerializer,
    PabrikSerializer,
    AngkutanPabrikSerializer,
    LampiranSerializer,
    LampiranCreateUpdateSerializer,
)
from penjualan.models import Angkutan, KelompokPenyetor, Pabrik, Lampiran
from django.db.models import Q
from django.http import HttpResponse
import csv


# Angkutan
class AngkutanListView(DateParserMixin, generics.ListAPIView):
    serializer_class = AngkutanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    
    def get_queryset(self):
        start_date, end_date = self.get_date_range(self.request)
        if start_date and end_date:
            queryset = Angkutan.objects.filter(tanggal_penjualan__range=(start_date, end_date)).order_by('-created_at')
        else:
            queryset = Angkutan.objects.all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(
                kelompokpenyetor__anggota_petani__kabupaten_id=kab_sekadau_id
            ).distinct()
            
        search = self.request.query_params.get('search', None)
        kelompok_tani = self.request.query_params.get('kelompok_tani', None)
        pabrik = self.request.query_params.get('pabrik', None)
        tanggal_penjualan = self.request.query_params.get('tanggal_penjualan', None)
        
        if kelompok_tani:
            queryset = queryset.filter(kelompokpenyetor__nama_kelompok=kelompok_tani).distinct()
            
        if pabrik:
            queryset = queryset.filter(pabrik_id=pabrik)
            
        if tanggal_penjualan:
            queryset = queryset.filter(tanggal_penjualan=tanggal_penjualan)
                        
        if search:
            queryset = queryset.filter(
                Q(driver__icontains=search) | Q(no_registrasi__icontains=search) | 
                Q(no_polisi__icontains=search)
                
            )
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data angkutan",
            data=response.data,
            status="success"
        ), status=response.status_code)


class AngkutanDownloadListView(DownloadListMixin, AngkutanListView):
    filename_download = "angkutan_data_download"
    permission_classes = [IsAuthenticated, role_required(1, 6)]
    
    def create_header(self):
        return [
            'ID Penjualan',
            'Tanggal Penjualan',
            'Driver',
            'No Registrasi',
            'No Polisi',
            'Jumlah Tandan',
            'Berat Timbangan',
            'Tarra',
            'T Potongan Persen',
            'T Potongan KG',
            'Berat Bersih',
            'Harga Per Kilo',
            'Total Penjualan',
            'Kelompok Penyetor',
            'Created At',
            'Updated At',
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item.get('id_penjualan', item.get('id', '')),
                item.get('tanggal_penjualan', ''),
                item.get('driver', ''),
                item.get('no_registrasi', ''),
                item.get('no_polisi', ''),
                item.get('jumlah_tandan', ''),
                item.get('berat_timbangan', ''),
                item.get('tarra', ''),
                item.get('t_potongan_persen', ''),
                item.get('t_potongan_kg', ''),
                item.get('berat_bersih', ''),
                item.get('harga_per_kilo', ''),
                item.get('total_penjualan', ''),
                item.get('kelompok_penyetor', ''),
                item.get('created_at', ''),
                item.get('updated_at', ''),
            ])
        return list_data


class AngkutanDetailView(generics.RetrieveAPIView):
    serializer_class = AngkutanPabrikSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    queryset = Angkutan.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data angkutan",
            data=response.data,
            status="success"
        ), status=response.status_code)        


class AngkutanCreateView(generics.CreateAPIView):
    serializer_class = AngkutanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
            message="Berhasil menambahkan data angkutan",
            data=serializer.data
        ), status=status.HTTP_201_CREATED, headers=headers)


class AngkutanUpdateView(generics.UpdateAPIView):
    serializer_class = AngkutanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = Angkutan.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah data angkutan",
            data=serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class AngkutanPabrikUpdateView(AngkutanUpdateView):
    serializer_class = AngkutanPabrikSerializer


class AngkutanDeleteView(generics.DestroyAPIView):
    serializer_class = AngkutanSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = Angkutan.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data angkutan",
            data=None,
            status="success"
        ), status=response.status_code)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# Lampiran Penjualan
class LampiranListView(generics.ListAPIView):
    serializer_class = LampiranSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]

    def get_queryset(self):
        queryset = Lampiran.objects.select_related('angkutan').all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(
                angkutan__kelompokpenyetor__anggota_petani__kabupaten_id=kab_sekadau_id
            ).distinct()

        angkutan_id = self.request.query_params.get('angkutan', None)
        if angkutan_id:
            queryset = queryset.filter(angkutan_id=angkutan_id)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data lampiran penjualan",
            data=response.data,
            status="success"
        ), status=response.status_code)


class LampiranCreateView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LampiranCreateUpdateSerializer
        return LampiranSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'angkutan' not in data and 'angkutan_id' in data:
            data['angkutan'] = data['angkutan_id']

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        angkutan = validated_data.pop('angkutan')
        instance, created = Lampiran.objects.update_or_create(
            angkutan=angkutan,
            defaults=validated_data
        )

        output_serializer = LampiranSerializer(instance)
        message = "Berhasil menambahkan lampiran penjualan" if created else "Berhasil mengubah lampiran penjualan"
        return Response(custom_response(
            status="success",
            message=message,
            data=output_serializer.data
        ), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class LampiranUpdateView(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Angkutan.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return LampiranCreateUpdateSerializer
        return LampiranSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        angkutan = self.get_object()
        data = request.data.copy()
        data['angkutan'] = angkutan.id

        instance = getattr(angkutan, 'lampiran_penjualan', None)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        validated_data.pop('angkutan', None)
        instance, created = Lampiran.objects.update_or_create(
            angkutan=angkutan,
            defaults=validated_data
        )

        output_serializer = LampiranSerializer(instance)
        message = "Berhasil menambahkan lampiran penjualan" if created else "Berhasil mengubah lampiran penjualan"
        return Response(custom_response(
            status="success",
            message=message,
            data=output_serializer.data
        ), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class LampiranDetailView(generics.RetrieveAPIView):
    serializer_class = LampiranSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    queryset = Angkutan.objects.all()

    def retrieve(self, request, *args, **kwargs):
        angkutan = self.get_object()
        try:
            lampiran = angkutan.lampiran_penjualan
        except Lampiran.DoesNotExist:
            return Response(custom_response(
                status="error",
                message="Lampiran penjualan belum tersedia",
                data=None
            ), status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(lampiran)
        return Response(custom_response(
            message="Berhasil mendapatkan data lampiran penjualan",
            data=serializer.data,
            status="success"
        ), status=status.HTTP_200_OK)


class LampiranDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = Angkutan.objects.all()

    def destroy(self, request, *args, **kwargs):
        angkutan = self.get_object()
        try:
            lampiran = angkutan.lampiran_penjualan
        except Lampiran.DoesNotExist:
            return Response(custom_response(
                status="error",
                message="Lampiran penjualan belum tersedia",
                data=None
            ), status=status.HTTP_404_NOT_FOUND)

        lampiran.delete()
        return Response(custom_response(
            message="Berhasil menghapus data lampiran penjualan",
            data=None,
            status="success"
        ), status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class KelompokPenyetorListView(generics.ListAPIView):
    serializer_class = KelompokPenyetorDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    
    def get_queryset(self):
        queryset = KelompokPenyetor.objects.all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(
                anggota_petani__kabupaten_id=kab_sekadau_id
            ).distinct()
        
        # Filter by angkutan if provided
        angkutan_id = self.request.query_params.get('angkutan', None)
        if angkutan_id:
            queryset = queryset.filter(angkutan_id=angkutan_id)
        
        # Search by nama kelompok
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(nama_kelompok__icontains=search)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data kelompok penyetor",
            data=response.data,
            status="success"
        ), status=response.status_code)


class KelompokPenyetorDetailView(generics.RetrieveAPIView):
    serializer_class = KelompokPenyetorDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    queryset = KelompokPenyetor.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data kelompok penyetor",
            data=response.data,
            status="success"
        ), status=response.status_code)


class KelompokPenyetorBulkCreateView(generics.CreateAPIView):
    """
    View for bulk creating KelompokPenyetor
    Accepts multiple groups in one request
    """
    serializer_class = KelompokPenyetorBulkCreateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
        
        # Perform bulk create
        result = serializer.save()
        
        # Serialize created objects for the response
        created_kelompok = result['created']
        created_data = KelompokPenyetorDetailSerializer(
            created_kelompok, 
            many=True
        ).data
        
        # Prepare the response
        response_data = {
            'created': created_data,
            'success_count': result['success_count'],
            'error_count': result['error_count']
        }
        
        if result['errors']:
            response_data['errors'] = result['errors']
        
        # Determine status
        if result['error_count'] > 0 and result['success_count'] == 0:
            # All failed
            return Response(custom_response(
                status="error",
                message="Semua data gagal dibuat",
                data=response_data
            ), status=status.HTTP_400_BAD_REQUEST)
        
        elif result['error_count'] > 0:
            # Partial success
            return Response(custom_response(
                status="warning",
                message=f"Berhasil membuat {result['success_count']} kelompok, {result['error_count']} gagal",
                data=response_data
            ), status=status.HTTP_207_MULTI_STATUS)
        
        else:
            # All success
            return Response(custom_response(
                status="success",
                message=f"Berhasil membuat {result['success_count']} kelompok penyetor",
                data=response_data
            ), status=status.HTTP_201_CREATED)


# Kelompok Penyetor
class KelompokPenyetorUpdateView(generics.UpdateAPIView):
    serializer_class = KelompokPenyetorSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = KelompokPenyetor.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_update(serializer)
        
        # Use KelompokPenyetorDetailSerializer for response
        response_serializer = KelompokPenyetorDetailSerializer(instance)
        
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah data kelompok penyetor",
            data=response_serializer.data
        ), status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class KelompokPenyetorDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = KelompokPenyetor.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data kelompok penyetor",
            data=None,
            status="success"
        ), status=status.HTTP_204_NO_CONTENT)
    
    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# Pabrik CRUD Views
class PabrikListView(generics.ListAPIView):
    serializer_class = PabrikSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    
    def get_queryset(self):
        queryset = Pabrik.objects.all().order_by('nama')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(kabupaten_id=kab_sekadau_id)
        
        # Filter by search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nama__icontains=search) | 
                Q(alamat__icontains=search)
            )
        
        # Filter by kabupaten
        kabupaten = self.request.query_params.get('kabupaten', None)
        if kabupaten:
            queryset = queryset.filter(kabupaten_id=kabupaten)
            
        # Filter by kecamatan
        kecamatan = self.request.query_params.get('kecamatan', None)
        if kecamatan:
            queryset = queryset.filter(kecamatan_id=kecamatan)
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data pabrik",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PabrikDetailView(generics.RetrieveAPIView):
    serializer_class = PabrikSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    queryset = Pabrik.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data pabrik",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PabrikDetailByAngkutanView(generics.RetrieveAPIView):
    """
    View to get factory details by transport ID
    """
    serializer_class = PabrikSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    
    def get_object(self):
        angkutan_id = self.kwargs.get('pk')
        
        try:
            angkutan_queryset = Angkutan.objects.all()

            # Filter by district for the DISBUNAK_SEKADAU role
            if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
                kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
                angkutan_queryset = angkutan_queryset.filter(
                    kelompokpenyetor__anggota_petani__kabupaten_id=kab_sekadau_id
                ).distinct()

            angkutan = angkutan_queryset.get(pk=angkutan_id)
            
            if not angkutan.pabrik:
                from rest_framework.exceptions import NotFound
                raise NotFound("Angkutan ini tidak memiliki pabrik tujuan")
            
            return angkutan.pabrik
            
        except Angkutan.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Angkutan tidak ditemukan")
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response(custom_response(
            message="Berhasil mendapatkan data pabrik dari angkutan",
            data=serializer.data,
            status="success"
        ), status=status.HTTP_200_OK)
        

class PabrikCreateView(generics.CreateAPIView):
    serializer_class = PabrikSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
            message="Berhasil menambahkan data pabrik",
            data=serializer.data
        ), status=status.HTTP_201_CREATED, headers=headers)


class PabrikUpdateView(generics.UpdateAPIView):
    serializer_class = PabrikSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = Pabrik.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_update(serializer)
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah data pabrik",
            data=serializer.data
        ), status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class PabrikDeleteView(generics.DestroyAPIView):
    serializer_class = PabrikSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    queryset = Pabrik.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data pabrik",
            data=None,
            status="success"
        ), status=response.status_code)
    
    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# Sankey Diagram API
class SankeyDiagramAPIView(APIView):
    """
    API for Sankey Diagram showing the flow:
    Petani -> KelompokPenyetor -> Angkutan -> Pabrik
    
    Query params:
    - start_date: start date (format: DD-MM-YYYY)
    - end_date: end date (format: DD-MM-YYYY)
    - max range: 31 days
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 4, 5, 6)]
    
    def get(self, request):
        from datetime import timedelta, date
        
        def parse_multi_param(param_name):
            values = request.query_params.getlist(param_name)
            if values:
                return [value for value in values if value]
            raw = request.query_params.get(param_name, '')
            if not raw:
                return []
            return [item.strip() for item in raw.split(',') if item.strip()]
        
        # Parse date parameters
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)
        
        # Set default values if empty
        if not end_date_str:
            end_date = date.today()
        else:
            try:
                end_date = datetime.strptime(end_date_str, '%d-%m-%Y').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format end_date tidak valid. Gunakan format DD-MM-YYYY"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if not start_date_str:
            start_date = end_date - timedelta(days=31)
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%d-%m-%Y').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format start_date tidak valid. Gunakan format DD-MM-YYYY"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate the maximum range of 31 days
        date_diff = (end_date - start_date).days
        if date_diff > 31:
            return Response({
                "status": "error",
                "message": "Range tanggal maksimal 31 hari"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if date_diff < 0:
            return Response({
                "status": "error",
                "message": "start_date tidak boleh lebih besar dari end_date"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse filter params
        kelompok_filter = parse_multi_param('kelompok_tani')
        pabrik_filter = parse_multi_param('pabrik')

        # Filter Angkutan by tanggal_penjualan
        angkutan_list = Angkutan.objects.filter(
            tanggal_penjualan__gte=start_date,
            tanggal_penjualan__lte=end_date,
            pabrik__isnull=False  # Hanya yang sudah completed (ada pabrik)
        )

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            angkutan_list = angkutan_list.filter(
                kelompokpenyetor__anggota_petani__kabupaten_id=kab_sekadau_id
            )

        if kelompok_filter:
            angkutan_list = angkutan_list.filter(
                kelompokpenyetor__nama_kelompok__in=kelompok_filter
            )

        if pabrik_filter:
            angkutan_list = angkutan_list.filter(
                pabrik__nama__in=pabrik_filter
            )

        angkutan_list = angkutan_list.select_related('pabrik').prefetch_related(
            'kelompokpenyetor_set__anggota_petani'
        ).distinct()
        
        # Data structure for nodes and links
        petani_data = {}  # {petani_nama: {id_petani, berat, kelompok}}
        kelompok_data = {}  # {kelompok_nama: berat_total}
        angkutan_data = {}  # {angkutan_node_id: {nama, berat, metadata}}
        pabrik_data = {}  # {pabrik_nama: {berat, lokasi}}
        
        # Links: petani -> kelompok, kelompok -> angkutan, angkutan -> pabrik
        petani_kelompok_links = {}  # {(petani_nama, kelompok_nama): berat}
        kelompok_angkutan_links = {}  # {(kelompok_nama, angkutan_node_id): berat}
        angkutan_pabrik_links = {}  # {(angkutan_node_id, pabrik_nama): berat}
        
        # Proses setiap angkutan
        for angkutan in angkutan_list:
            berat_bersih = float(angkutan.berat_bersih)
            
            # Get the contributor groups for this transport
            kelompok_list = angkutan.kelompokpenyetor_set.all()
            
            if not kelompok_list.exists():
                continue  # Skip if there are no contributor groups
            
            # Hitung pembagian berat per kelompok (asumsi merata)
            jumlah_kelompok = kelompok_list.count()
            berat_per_kelompok = berat_bersih / jumlah_kelompok
            
            angkutan_node_id = f"{angkutan.no_polisi}"
            angkutan_nama = getattr(angkutan, 'id_penjualan', None) or f"Angkutan {angkutan.no_polisi}"

            # Track angkutan
            if angkutan_node_id not in angkutan_data:
                angkutan_data[angkutan_node_id] = {
                    'nama': angkutan_nama,
                    'berat': 0,
                    'metadata': {
                        'id_penjualan': getattr(angkutan, 'id_penjualan', None) or angkutan.no_polisi,
                        'driver': getattr(angkutan, 'driver', None),
                        'no_polisi': getattr(angkutan, 'no_polisi', None),
                        'tanggal_penjualan': angkutan.tanggal_penjualan.strftime('%d-%m-%Y') if angkutan.tanggal_penjualan else None
                    }
                }
            angkutan_data[angkutan_node_id]['berat'] += berat_bersih

            # Track pabrik
            pabrik_nama = angkutan.pabrik.nama
            if pabrik_nama not in pabrik_data:
                pabrik_data[pabrik_nama] = {
                    'berat': 0,
                    'lokasi': angkutan.pabrik.alamat
                }
            pabrik_data[pabrik_nama]['berat'] += berat_bersih

            # Link: angkutan -> pabrik
            angkutan_pabrik_key = (angkutan_node_id, pabrik_nama)
            if angkutan_pabrik_key not in angkutan_pabrik_links:
                angkutan_pabrik_links[angkutan_pabrik_key] = 0
            angkutan_pabrik_links[angkutan_pabrik_key] += berat_bersih

            for kelompok in kelompok_list:
                kelompok_nama = kelompok.nama_kelompok
                
                # Track kelompok
                if kelompok_nama not in kelompok_data:
                    kelompok_data[kelompok_nama] = 0
                kelompok_data[kelompok_nama] += berat_per_kelompok
                
                # Link: kelompok -> angkutan
                kelompok_angkutan_key = (kelompok_nama, angkutan_node_id)
                if kelompok_angkutan_key not in kelompok_angkutan_links:
                    kelompok_angkutan_links[kelompok_angkutan_key] = 0
                kelompok_angkutan_links[kelompok_angkutan_key] += berat_per_kelompok
                
                # Ambil petani dari kelompok dan hitung pembagian
                petani_list = kelompok.anggota_petani.all()
                if petani_list.exists():
                    jumlah_petani = petani_list.count()
                    berat_per_petani = berat_per_kelompok / jumlah_petani
                    
                    for petani in petani_list:
                        petani_nama = petani.nama
                        
                        # Track petani
                        if petani_nama not in petani_data:
                            petani_data[petani_nama] = {
                                'id_petani': petani.id_petani,
                                'berat': 0,
                                'kelompok': petani.nama_kelompok
                            }
                        petani_data[petani_nama]['berat'] += berat_per_petani
                        
                        # Link: petani -> kelompok
                        petani_kelompok_key = (petani_nama, kelompok_nama)
                        if petani_kelompok_key not in petani_kelompok_links:
                            petani_kelompok_links[petani_kelompok_key] = 0
                        petani_kelompok_links[petani_kelompok_key] += berat_per_petani
        
        # Build nodes
        nodes = []
        
        # Petani nodes
        for petani_nama, data in petani_data.items():
            nodes.append({
                "id": petani_nama,
                "name": petani_nama,
                "category": "petani",
                "value": round(data['berat'], 2),
                "metadata": {
                    "id_petani": data['id_petani'],
                    "kelompok_tani": data['kelompok']
                }
            })
        
        # Kelompok nodes
        for kelompok_nama, berat in kelompok_data.items():
            nodes.append({
                "id": kelompok_nama,
                "name": kelompok_nama,
                "category": "kelompok_penyetor",
                "value": round(berat, 2),
                "metadata": {}
            })
        
        # Angkutan nodes
        for angkutan_node_id, data in angkutan_data.items():
            nodes.append({
                "id": angkutan_node_id,
                "name": data['nama'],
                "category": "angkutan",
                "value": round(data['berat'], 2),
                "metadata": data['metadata']
            })

        # Pabrik nodes
        for pabrik_nama, data in pabrik_data.items():
            nodes.append({
                "id": pabrik_nama,
                "name": pabrik_nama,
                "category": "pabrik",
                "value": round(data['berat'], 2),
                "metadata": {
                    "lokasi": data['lokasi']
                }
            })
        
        # Build links
        links = []
        
        # Petani -> Kelompok
        for (petani_nama, kelompok_nama), berat in petani_kelompok_links.items():
            links.append({
                "source": petani_nama,
                "target": kelompok_nama,
                "value": round(berat, 2)
            })
        
        # Kelompok -> Angkutan
        for (kelompok_nama, angkutan_node_id), berat in kelompok_angkutan_links.items():
            links.append({
                "source": kelompok_nama,
                "target": angkutan_node_id,
                "value": round(berat, 2)
            })

        # Angkutan -> Pabrik
        for (angkutan_node_id, pabrik_nama), berat in angkutan_pabrik_links.items():
            links.append({
                "source": angkutan_node_id,
                "target": pabrik_nama,
                "value": round(berat, 2)
            })
        
        # Calculate total volume (dari petani)
        total_volume = sum(data['berat'] for data in petani_data.values())
        
        # Response data
        data = {
            "meta": {
                "start_date": start_date.strftime('%d-%m-%Y'),
                "end_date": end_date.strftime('%d-%m-%Y'),
                "total_volume": round(total_volume, 2),
                "unit": "Kg",
                "total_angkutan": angkutan_list.count(),
                "total_petani": len(petani_data),
                "total_kelompok": len(kelompok_data),
                "total_pabrik": len(pabrik_data),
                "updated_at": datetime.now().isoformat() + "Z"
            },
            "stages": [
                {"id": "petani", "label": "Petani", "order": 1},
                {"id": "kelompok_penyetor", "label": "Kelompok Penyetor", "order": 2},
                {"id": "angkutan", "label": "Angkutan", "order": 3},
                {"id": "pabrik", "label": "Pabrik", "order": 4}
            ],
            "nodes": nodes,
            "links": links
        }
        
        return Response({
            "status": "success",
            "message": "Data sankey diagram berhasil diambil",
            "data": data
        }, status=status.HTTP_200_OK)


class SankeyDiagramDownloadCSVView(APIView):
    """
    API to download CSV from the Sankey Diagram
    CSV format: Farmer, Group, Transport, Factory, Volume
    
    Query params are the same as SankeyDiagramAPIView:
    - start_date: start date (format: DD-MM-YYYY)
    - end_date: end date (format: DD-MM-YYYY)
    - kelompok_tani: filter group name (can be multiple)
    - pabrik: filter factory (can be multiple)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def get(self, request):
        from datetime import timedelta, date
        
        def parse_multi_param(param_name):
            values = request.query_params.getlist(param_name)
            if values:
                return [value for value in values if value]
            raw = request.query_params.get(param_name, '')
            if not raw:
                return []
            return [item.strip() for item in raw.split(',') if item.strip()]
        
        # Parse date parameters (same as SankeyDiagramAPIView)
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)
        
        if not end_date_str:
            end_date = date.today()
        else:
            try:
                end_date = datetime.strptime(end_date_str, '%d-%m-%Y').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format end_date tidak valid. Gunakan format DD-MM-YYYY"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if not start_date_str:
            start_date = end_date - timedelta(days=31)
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%d-%m-%Y').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format start_date tidak valid. Gunakan format DD-MM-YYYY"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate
        date_diff = (end_date - start_date).days
        if date_diff > 31:
            return Response({
                "status": "error",
                "message": "Range tanggal maksimal 31 hari"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if date_diff < 0:
            return Response({
                "status": "error",
                "message": "start_date tidak boleh lebih besar dari end_date"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse filter params
        kelompok_filter = parse_multi_param('kelompok_tani')
        pabrik_filter = parse_multi_param('pabrik')

        # Filter transports
        angkutan_list = Angkutan.objects.filter(
            tanggal_penjualan__gte=start_date,
            tanggal_penjualan__lte=end_date,
            pabrik__isnull=False
        )

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            angkutan_list = angkutan_list.filter(
                kelompokpenyetor__anggota_petani__kabupaten_id=kab_sekadau_id
            )

        if kelompok_filter:
            angkutan_list = angkutan_list.filter(
                kelompokpenyetor__nama_kelompok__in=kelompok_filter
            )

        if pabrik_filter:
            angkutan_list = angkutan_list.filter(
                pabrik__nama__in=pabrik_filter
            )

        angkutan_list = angkutan_list.select_related('pabrik').prefetch_related(
            'kelompokpenyetor_set__anggota_petani'
        ).distinct()
        
        # Prepare CSV response
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f'sankey_diagram_{start_date.strftime("%d%m%Y")}_{end_date.strftime("%d%m%Y")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        # Write header
        writer.writerow(['Petani', 'Kelompok Tani', 'Angkutan', 'Pabrik', 'Volume'])
        
        # Collect CSV rows
        csv_rows = []
        
        # Proses setiap angkutan (sama seperti logic di SankeyDiagramAPIView)
        for angkutan in angkutan_list:
            berat_bersih = float(angkutan.berat_bersih)
            
            kelompok_list = angkutan.kelompokpenyetor_set.all()
            
            if not kelompok_list.exists():
                continue
            
            jumlah_kelompok = kelompok_list.count()
            berat_per_kelompok = berat_bersih / jumlah_kelompok
            
            angkutan_nama = angkutan.no_polisi
            pabrik_nama = angkutan.pabrik.nama
            
            for kelompok in kelompok_list:
                kelompok_nama = kelompok.nama_kelompok
                
                petani_list = kelompok.anggota_petani.all()
                if petani_list.exists():
                    jumlah_petani = petani_list.count()
                    berat_per_petani = berat_per_kelompok / jumlah_petani
                    
                    for petani in petani_list:
                        # Format volume with a comma as the decimal separator
                        volume_formatted = f"{berat_per_petani:,.2f} Kg".replace(',', 'X').replace('.', ',').replace('X', '.')
                        
                        csv_rows.append([
                            petani.nama,
                            kelompok_nama,
                            angkutan_nama,
                            pabrik_nama,
                            volume_formatted
                        ])
        
        # Write all rows
        writer.writerows(csv_rows)
        
        return response


class TotalPenjualanBarChartAPIView(APIView):
    """
    API view to get monthly sales bar chart data
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    look_up_filter = 'total_penjualan'
    message_label = 'Total Penjualan'
    
    def get(self, request):
        # Read the start_date and end_date parameters
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)
        
        # Set defaults if parameters are empty
        if not start_date_str:
            start_date = datetime(timezone.now().year, 1, 1).date()
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format start_date tidak valid. Gunakan format YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if not end_date_str:
            end_date = timezone.now().date()
        else:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format end_date tidak valid. Gunakan format YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Query sales data
        penjualan_data = Angkutan.objects.filter(
            tanggal_penjualan__range=(start_date, end_date)
        ).annotate(
            bulan=ExtractMonth('tanggal_penjualan')
        ).values('bulan').annotate(
            total=Sum(self.look_up_filter)
        ).order_by('bulan')
        
        # Month names in Indonesian
        nama_bulan = [
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        ]
        
        # Initialize all months with 0
        data_per_bulan = {i: 0 for i in range(1, 13)}
        
        # Fill the data from the query
        for item in penjualan_data:
            bulan = item['bulan']
            total = float(item['total']) if item['total'] else 0
            data_per_bulan[bulan] = round(total, 2)
        
        # Format the response
        response_data = {
            "labels": nama_bulan,
            "data": [data_per_bulan[i] for i in range(1, 13)]
        }
        
        return Response({
            "status": "success",
            "message": f"Data bar chart {self.message_label} berhasil diambil",
            "data": response_data
        }, status=status.HTTP_200_OK)
        

class BeratTimbanganBarChartAPIView(TotalPenjualanBarChartAPIView):
    """
    API view to get monthly weighed-weight bar chart data
    """
    look_up_filter = 'berat_timbangan'
    message_label = 'Berat Timbangan'


class JumlahTandanBarChartAPIView(TotalPenjualanBarChartAPIView):
    """
    API view to get monthly bunch count bar chart data
    """
    look_up_filter = 'jumlah_tandan'
    message_label = 'Jumlah Tandan'


class BeratTimbanganPabrikDonutChartAPIView(APIView):
    """
    API view to get weighed-weight donut chart data per factory
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Read the start_date and end_date parameters
        start_date_str = request.query_params.get('start_date', None)
        end_date_str = request.query_params.get('end_date', None)
        
        # Set defaults if parameters are empty
        if not start_date_str:
            start_date = datetime(timezone.now().year, 1, 1).date()
        else:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format start_date tidak valid. Gunakan format YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if not end_date_str:
            end_date = timezone.now().date()
        else:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    "status": "error",
                    "message": "Format end_date tidak valid. Gunakan format YYYY-MM-DD"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Query weighed-weight data per factory
        pabrik_data = Angkutan.objects.filter(
            tanggal_penjualan__range=(start_date, end_date),
            pabrik__isnull=False
        ).values('pabrik__nama').annotate(
            total_berat=Sum('berat_timbangan')
        ).order_by('-total_berat')
        
        # Extract labels (factory names) and data (total weight)
        labels = []
        data = []
        
        for item in pabrik_data:
            labels.append(item['pabrik__nama'])
            total_berat = float(item['total_berat']) if item['total_berat'] else 0
            data.append(round(total_berat, 2))
        
        # Format response
        response_data = {
            "labels": labels,
            "data": data
        }
        
        return Response({
            "status": "success",
            "message": "Data donut chart berat timbangan per pabrik berhasil diambil",
            "data": response_data
        }, status=status.HTTP_200_OK)

