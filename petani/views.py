from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from utils.serializers import custom_response
from utils.decorators import role_required
from utils.mixins import DownloadListMixin
from django.conf import settings
from utils.choices import JenisKelamin, StatusKeanggotaan, StatusPekerja, UserRole
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from petani.serializers import (
    LampiranPetaniCreateUpdateSerializer, PetaniSerializer, LampiranPetaniSerializer, DiklatSerializer, PekerjaSerializer,
    PekerjaPetaniListSerializer, PetaniDetailSerializer, PekerjaPetaniListSerializerV2
)
from petani.models import Petani, Diklat, Pekerja, Lampiran
from django.db.models import Count, Q, Max
from django.utils.text import slugify


class PetaniListView(generics.ListAPIView):
    serializer_class = PetaniSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    
    def get_queryset(self):
        queryset = Petani.objects.all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(kabupaten_id=kab_sekadau_id)

        search = self.request.query_params.get('search', None)
        kelompok_tani = self.request.query_params.get('kelompok_tani', None)
        keanggotaan = self.request.query_params.get('keanggotaan', None)
        is_rspo = self.request.query_params.get('is_rspo', None)
        is_ispo = self.request.query_params.get('is_ispo', None)
        
        if kelompok_tani:
            queryset = queryset.filter(nama_kelompok__icontains=kelompok_tani)
            
        if keanggotaan:
            queryset = queryset.filter(keanggotaan=keanggotaan)

        if is_rspo is not None:
            queryset = queryset.filter(kebun__is_rspo=is_rspo.lower() == 'true').distinct()

        if is_ispo is not None:
            queryset = queryset.filter(kebun__is_ispo=is_ispo.lower() == 'true').distinct()
                        
        if search:
            queryset = queryset.filter(
                Q(nama__icontains=search) | Q(id_petani__icontains=search)
            )
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data petani",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PetaniListDownloadView(DownloadListMixin, PetaniListView):
    filename_download = "cukk_petani_data"
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create_header(self):
        return [
            'id_petani', 
            'nama', 
            'jns_kelamin', 
            'nama_kelompok', 
            'no_ktp', 
            'no_kk',
            'status_perkawinan',
            'no_nib',
            'tgl_terbit_sppl',
            'tanggal_bergabung', 
            'tanggal_keluar', 
            'keanggotaan', 
            'updated_at'
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['id_petani'],
                item['nama'],
                item['jns_kelamin'],
                item['nama_kelompok'],
                item['no_ktp'],
                item['no_kk'] or '',
                item['status_perkawinan'] or '',
                item['no_nib'] or '',
                item['tgl_terbit_sppl'] or '',
                item['tanggal_bergabung'] or '',
                item['tanggal_keluar'] or '',
                StatusKeanggotaan(item['keanggotaan']).label if item['keanggotaan'] else '',
                item['updated_at'],
            ])
        return list_data


class PetaniWANotNullView(PetaniListView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(~Q(no_wa__isnull=True) & ~Q(no_wa__exact='')).order_by('-created_at')


class PetaniDetailView(generics.RetrieveAPIView):
    serializer_class = PetaniDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    queryset = Petani.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Successfully retrieved farmer data",
            data=response.data,
            status="success"
        ), status=response.status_code)        


class PetaniCreateView(generics.CreateAPIView):
    serializer_class = PetaniSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
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
            message="Berhasil menambahkan data petani",
            data=serializer.data
        ), status=status.HTTP_201_CREATED, headers=headers)


class PetaniUpdateView(generics.UpdateAPIView):
    serializer_class = PetaniSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Petani.objects.all()
    
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
            message="Berhasil mengubah data petani",
            data=serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class PetaniDeleteView(generics.DestroyAPIView):
    serializer_class = PetaniSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Petani.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data petani",
            data=None,
            status="success"
        ), status=response.status_code)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class LampiranPetaniCreateView(generics.CreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Explicit parser for file upload
    
    def get_serializer_class(self):
        """Use different serializers for input and output"""
        if self.request.method == 'POST':
            return LampiranPetaniCreateUpdateSerializer
        return LampiranPetaniSerializer
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['petani'] = data['petani_id']
        
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
        output_serializer = LampiranPetaniSerializer(instance)
        headers = self.get_success_headers(output_serializer.data)
        return Response(custom_response(
            status="success",
            message="Berhasil menambahkan lampiran petani",
            data=output_serializer.data
        ), status=status.HTTP_201_CREATED, headers=headers)
        
        
class LampiranPetaniUpdateView(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Petani.objects.all()
    
    def get_serializer_class(self):
        """Use different serializers for input and output"""
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return LampiranPetaniCreateUpdateSerializer
        return LampiranPetaniSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        petani = self.get_object()
        instance = petani.lampiran
        data = request.data.copy()
        data['petani'] = petani.id

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
        output_serializer = LampiranPetaniSerializer(instance)
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah lampiran petani",
            data=output_serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)    


class LampiranPetaniDetailView(generics.RetrieveAPIView):
    serializer_class = LampiranPetaniSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    queryset = Petani.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        petani = self.get_object()
        lampiran = getattr(petani, 'lampiran', None)
        if not lampiran:
            return Response(custom_response(
                message="Lampiran petani tidak ditemukan",
                data=None,
                status="error"
            ), status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(lampiran)
        return Response(custom_response(
            message="Berhasil mendapatkan data lampiran petani",
            data=serializer.data,
            status="success"
        ), status=status.HTTP_200_OK)


class DiklatListView(generics.ListAPIView):
    serializer_class = DiklatSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self):
        queryset = Diklat.objects.all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(petani__kabupaten_id=kab_sekadau_id)

        search = self.request.query_params.get('search', None)
        kelompok_tani = self.request.query_params.get('kelompok_tani', None)
        
        if kelompok_tani:
            queryset = queryset.filter(petani__nama_kelompok__icontains=kelompok_tani)
        if search:
            queryset = queryset.filter(
                Q(petani__nama__icontains=search) | Q(petani__id_petani__icontains=search)
            )
        
        for field in ('sl', 'pnc', 'k3', 'sop', 'fdg', 'pestisida', 'manajemen_api', 'pengendalian_hpt', 'nkt'):
            value = self.request.query_params.get(field, None)
            if value is not None:
                queryset = queryset.filter(**{field: value.lower() == 'true'})
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data diklat",
            data=response.data,
            status="success"
        ), status=response.status_code)


class DiklatDownloadView(DownloadListMixin, DiklatListView):
    filename_download = "cukk_diklat_data"
    
    def create_header(self):
        return [
            'id_petani',
            'nama_petani',
            'nama_kelompok',
            'jenis_kelamin',
            'pnc',
            'pnc_trainer',
            'k3',
            'k3_trainer',
            'sl',
            'sl_trainer',
            'sop',
            'sop_trainer',
            'fdg',
            'fdg_trainer',
            'pestisida',
            'pestisida_trainer',
            'manajemen_api',
            'manajemen_api_trainer',
            'pengendalian_hpt',
            'pengendalian_hpt_trainer',
            'nkt',
            'nkt_trainer',
            'updated_at'
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['id_petani'],
                item['nama_petani'],
                item['nama_kelompok'],
                item['jenis_kelamin_label'],
                'Sudah' if item['pnc'] else 'Belum',
                item['pnc_trainer'],
                'Sudah' if item['k3'] else 'Belum',
                item['k3_trainer'],
                'Sudah' if item['sl'] else 'Belum',
                item['sl_trainer'],
                'Sudah' if item['sop'] else 'Belum',
                item['sop_trainer'],
                'Sudah' if item['fdg'] else 'Belum',
                item['fdg_trainer'],
                'Sudah' if item['pestisida'] else 'Belum',
                item['pestisida_trainer'],
                'Sudah' if item['manajemen_api'] else 'Belum',
                item['manajemen_api_trainer'],
                'Sudah' if item['pengendalian_hpt'] else 'Belum',
                item['pengendalian_hpt_trainer'],
                'Sudah' if item['nkt'] else 'Belum',
                item['nkt_trainer'],
                item['updated_at'],
            ])
        return list_data


class DiklatUpdateView(generics.UpdateAPIView):
    serializer_class = DiklatSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Diklat.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        diklat = self.get_object()
        data = request.data.copy()
        data['petani'] = diklat.petani_id

        serializer = self.get_serializer(diklat, data=data, partial=partial)
        if not serializer.is_valid():
            return Response(custom_response(
                status="error",
                message="Data tidak valid",
                errors=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)
            
        self.perform_update(serializer)
        return Response(custom_response(
            status="success",
            message="Berhasil mengubah data diklat",
            data=serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class DiklatDetailView(generics.RetrieveAPIView):
    serializer_class = DiklatSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = Diklat.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data diklat",
            data=response.data,
            status="success"
        ), status=response.status_code)


class DiklatStatisticView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get(self, request, *args, **kwargs):
        queryset = Diklat.objects.all()

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(petani__kabupaten_id=kab_sekadau_id)

        # Aggregate statistics for each diklat field
        statistics = queryset.aggregate(
            pnc_sudah=Count('id', filter=Q(pnc=True)),
            pnc_belum=Count('id', filter=Q(pnc=False)),
            k3_sudah=Count('id', filter=Q(k3=True)),
            k3_belum=Count('id', filter=Q(k3=False)),
            sl_sudah=Count('id', filter=Q(sl=True)),
            sl_belum=Count('id', filter=Q(sl=False)),
            sop_sudah=Count('id', filter=Q(sop=True)),
            sop_belum=Count('id', filter=Q(sop=False)),
            fdg_sudah=Count('id', filter=Q(fdg=True)),
            fdg_belum=Count('id', filter=Q(fdg=False)),
            pestisida_sudah=Count('id', filter=Q(pestisida=True)),
            pestisida_belum=Count('id', filter=Q(pestisida=False)),
            manajemen_api_sudah=Count('id', filter=Q(manajemen_api=True)),
            manajemen_api_belum=Count('id', filter=Q(manajemen_api=False)),
            pengendalian_hpt_sudah=Count('id', filter=Q(pengendalian_hpt=True)),
            pengendalian_hpt_belum=Count('id', filter=Q(pengendalian_hpt=False)),
            nkt_sudah=Count('id', filter=Q(nkt=True)),
            nkt_belum=Count('id', filter=Q(nkt=False)), 
            total_petani=Count('id')
        )
        
        # Format the response data
        response_data = {
            'pnc': {
                'sudah': statistics['pnc_sudah'],
                'belum': statistics['pnc_belum']
            },
            'k3': {
                'sudah': statistics['k3_sudah'],
                'belum': statistics['k3_belum']
            },
            'sl': {
                'sudah': statistics['sl_sudah'],
                'belum': statistics['sl_belum']
            },
            'sop': {
                'sudah': statistics['sop_sudah'],
                'belum': statistics['sop_belum']
            },
            'fdg': {
                'sudah': statistics['fdg_sudah'],
                'belum': statistics['fdg_belum']
            },
            'pestisida': {
                'sudah': statistics['pestisida_sudah'],
                'belum': statistics['pestisida_belum']
            },
            'manajemen_api': {
                'sudah': statistics['manajemen_api_sudah'],
                'belum': statistics['manajemen_api_belum']
            },
            'pengendalian_hpt': {
                'sudah': statistics['pengendalian_hpt_sudah'],
                'belum': statistics['pengendalian_hpt_belum']
            },
            'nkt': {
                'sudah': statistics['nkt_sudah'],
                'belum': statistics['nkt_belum']
            },
            'total_petani': statistics['total_petani']
        }
        
        return Response(custom_response(
            message="Berhasil mendapatkan statistik diklat",
            data=response_data,
            status="success"
        ), status=status.HTTP_200_OK)


class KelompokTaniListView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search', None)
        if search:
            kelompok_tani = Petani.objects.filter(nama_kelompok__icontains=search).values('nama_kelompok').distinct().order_by('nama_kelompok')
        else:
            kelompok_tani = Petani.objects.values('nama_kelompok').distinct().order_by('nama_kelompok')
            
        # Group case-insensitively to avoid duplicates with different letter casing
        seen_lower = {}
        data = []
        
        for kelompok in kelompok_tani:
            nama_kelompok = kelompok['nama_kelompok']
            if nama_kelompok:  # Skip if None or empty
                nama_lower = nama_kelompok.lower()
                
                # If no name with the same lowercase value has been seen yet
                if nama_lower not in seen_lower:
                    seen_lower[nama_lower] = nama_kelompok
                    data.append({
                        'value': nama_kelompok,
                        'label': nama_kelompok
                    })
        
        # Sort data by label (case-insensitive)
        data.sort(key=lambda x: x['label'].lower())
            
        return Response(custom_response(
            message="Berhasil mendapatkan data kelompok tani",
            data=data,
            status="success"
        ), status=status.HTTP_200_OK)
        

class PekerjaListView(generics.ListAPIView):
    serializer_class = PekerjaPetaniListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self):
        queryset = Petani.objects.all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(kabupaten_id=kab_sekadau_id)

        search = self.request.query_params.get('search', None)
        kelompok_tani = self.request.query_params.get('kelompok_tani', None)
        
        if kelompok_tani:
            queryset = queryset.filter(nama_kelompok__icontains=kelompok_tani)
                        
        if search:
            queryset = queryset.filter(
                Q(nama__icontains=search) | Q(nama__icontains=search) | Q(id_petani__icontains=search)
            )
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data pekerja",
            data=response.data,
            status="success"
        ), status=response.status_code)
        

class PekerjaListViewV2(generics.ListAPIView):
    serializer_class = PekerjaPetaniListSerializerV2
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self):
        queryset = Pekerja.objects.all().order_by('-created_at')

        # Filter by district for the DISBUNAK_SEKADAU role
        if UserRole.DISBUNAK_SEKADAU in self.request.user.roles:
            kab_sekadau_id = settings.WILAYAH_ADM_ID['kab_sekadau']
            queryset = queryset.filter(petani__kabupaten_id=kab_sekadau_id)

        search = self.request.query_params.get('search', None)
        kelompok_tani = self.request.query_params.get('kelompok_tani', None)
        jns_kelamin = self.request.query_params.get('jns_kelamin', None)
        status_pekerja = self.request.query_params.get('status_pekerja', None)
        
        if kelompok_tani:
            queryset = queryset.filter(petani__nama_kelompok__icontains=kelompok_tani)

        if jns_kelamin:
            queryset = queryset.filter(jns_kelamin=jns_kelamin)

        if status_pekerja:
            queryset = queryset.filter(status_pekerja=status_pekerja)
                        
        if search:
            queryset = queryset.filter(
                Q(nama__icontains=search) | Q(petani__nama__icontains=search) | Q(petani__id_petani__icontains=search)
            )
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data pekerja",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PekerjaDownloadView(DownloadListMixin, PekerjaListViewV2):
    filename_download = "cukk_pekerja_data"
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create_header(self):
        return [
            'id_petani',
            'nama_petani',
            'nama_kelompok',
            'no_ktp',
            'no_kk',
            'luas_kebun',
            'jumlah_pekerja',
            'jenis_kelamin'
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['id_petani'],
                item['nama_petani'],
                item['nama_kelompok'],
                item['no_ktp'],
                item['no_kk'],
                item['luas_kebun'],
                item['jumlah_pekerja'],
                item['jenis_kelamin_label']
            ])
        return list_data


class PekerjaByPetaniListView(generics.ListAPIView):
    serializer_class = PekerjaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self, *args, **kwargs):
        petani_id = self.kwargs.get('petani_id')
        queryset = Pekerja.objects.filter(petani_id=petani_id).order_by('-created_at')
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data pekerja",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PekerjaDetailView(generics.RetrieveAPIView):
    serializer_class = PekerjaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = Pekerja.objects.select_related('petani').all()
    
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data pekerja",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PekerjaCreateView(generics.CreateAPIView):
    serializer_class = PekerjaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data['petani'] = data['petani_id']
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
            message="Berhasil menambahkan data pekerja",
            data=serializer.data
        ), status=status.HTTP_201_CREATED, headers=headers)


class PekerjaUpdateView(generics.UpdateAPIView):
    serializer_class = PekerjaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Pekerja.objects.select_related('petani').all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        data['petani'] = data['petani_id']
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
            message="Berhasil mengubah data pekerja",
            data=serializer.data
        ), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class PekerjaDeleteView(generics.DestroyAPIView):
    serializer_class = PekerjaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Pekerja.objects.select_related('petani').all()
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data pekerja",
            data=None,
            status="success"
        ), status=response.status_code)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class PekerjaStatistikView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]

    def get(self, request, *args, **kwargs):
        # Deduplicate pekerja by no_ktp by taking the latest record for each no_ktp.
        latest_ids_per_ktp = (
            Pekerja.objects
            .exclude(no_ktp__isnull=True)
            .exclude(no_ktp='')
            .values('no_ktp')
            .annotate(latest_id=Max('id'))
            .values_list('latest_id', flat=True)
        )
        unique_pekerja = Pekerja.objects.filter(id__in=latest_ids_per_ktp)

        response_data = {
            'total_pekerja': unique_pekerja.count(),
            'total_pekerja_pria': unique_pekerja.filter(jns_kelamin=JenisKelamin.LAKI_LAKI).count(),
            'total_pekerja_wanita': unique_pekerja.filter(jns_kelamin=JenisKelamin.PEREMPUAN).count(),
        }

        for status_choice in StatusPekerja:
            status_key = slugify(status_choice.label).replace('-', '_')
            response_data[f'total_status_pekerja_{status_key}'] = unique_pekerja.filter(
                status_pekerja=status_choice.value
            ).count()

        return Response(custom_response(
            message="Berhasil mendapatkan statistik pekerja",
            data=response_data,
            status="success"
        ), status=status.HTTP_200_OK)


class PetaniGenderStatisticView(generics.GenericAPIView):
    """
    View for farmer gender statistics.
    Shows counts and percentages for male, female, and total.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get(self, request, *args, **kwargs):
        # Filter petani aktif
        queryset = Petani.objects.all()
        keanggotaan = request.query_params.get('keanggotaan', None)
        
        if keanggotaan is not None:
            queryset = queryset.filter(keanggotaan=keanggotaan)
        
        # Count by gender
        statistics = queryset.aggregate(
            laki_laki=Count('id', filter=Q(jns_kelamin=JenisKelamin.LAKI_LAKI)),
            perempuan=Count('id', filter=Q(jns_kelamin=JenisKelamin.PEREMPUAN)),
            tidak_diset=Count('id', filter=Q(jns_kelamin__isnull=True) | Q(jns_kelamin='')),
            total=Count('id')
        )
        
        total = statistics['total']
        laki_laki = statistics['laki_laki']
        perempuan = statistics['perempuan']
        tidak_diset = statistics['tidak_diset']
        
        # Hitung persentase
        persentase_laki_laki = round((laki_laki / total * 100), 2) if total > 0 else 0
        persentase_perempuan = round((perempuan / total * 100), 2) if total > 0 else 0
        persentase_tidak_diset = round((tidak_diset / total * 100), 2) if total > 0 else 0
        
        response_data = {
            'laki_laki': {
                'jumlah': laki_laki,
                'persentase': persentase_laki_laki
            },
            'perempuan': {
                'jumlah': perempuan,
                'persentase': persentase_perempuan
            },
            'tidak_diset': {
                'jumlah': tidak_diset,
                'persentase': persentase_tidak_diset
            },
            'total': {
                'jumlah': total,
                'persentase': 100
            }
        }
        
        return Response(custom_response(
            message="Berhasil mendapatkan statistik jenis kelamin petani",
            data=response_data,
            status="success"
        ), status=status.HTTP_200_OK)


class PetaniDokumenStatisticView(generics.GenericAPIView):
    """
    View for farmer document completeness statistics.
    Shows counts and percentages of farmers who have completed:
    - KTP (file_ktp)
    - KK (file_kk)
    - Photo (thumb_ktp - photo derived from KTP)
    - SPPL (tgl_terbit_sppl)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get(self, request, *args, **kwargs):
        # Filter petani
        queryset = Petani.objects.all()
        keanggotaan = request.query_params.get('keanggotaan', None)
        
        if keanggotaan is not None:
            queryset = queryset.filter(keanggotaan=keanggotaan)
        
        total_petani = queryset.count()
        
        # Hitung jumlah petani yang sudah melengkapi dokumen
        # KTP - dari lampiran file_ktp
        jumlah_ktp = Lampiran.objects.filter(
            petani__in=queryset,
            file_ktp__isnull=False
        ).exclude(file_ktp='').count()
        
        # KK - dari lampiran file_kk
        jumlah_kk = Lampiran.objects.filter(
            petani__in=queryset,
            file_kk__isnull=False
        ).exclude(file_kk='').count()
        
        # Photo - use thumb_ktp as a photo proxy
        jumlah_foto = Lampiran.objects.filter(
            petani__in=queryset,
            thumb_ktp__isnull=False
        ).exclude(thumb_ktp='').count()
        
        # SPPL - dari petani tgl_terbit_sppl
        jumlah_sppl = queryset.filter(
            tgl_terbit_sppl__isnull=False
        ).count()
        
        # Hitung persentase
        persentase_ktp = round((jumlah_ktp / total_petani * 100), 2) if total_petani > 0 else 0
        persentase_kk = round((jumlah_kk / total_petani * 100), 2) if total_petani > 0 else 0
        persentase_foto = round((jumlah_foto / total_petani * 100), 2) if total_petani > 0 else 0
        persentase_sppl = round((jumlah_sppl / total_petani * 100), 2) if total_petani > 0 else 0
        
        response_data = {
            'ktp': {
                'jumlah': jumlah_ktp,
                'persentase': persentase_ktp
            },
            'kk': {
                'jumlah': jumlah_kk,
                'persentase': persentase_kk
            },
            'foto': {
                'jumlah': jumlah_foto,
                'persentase': persentase_foto
            },
            'sppl': {
                'jumlah': jumlah_sppl,
                'persentase': persentase_sppl
            },
            'total_petani': total_petani
        }
        
        return Response(custom_response(
            message="Berhasil mendapatkan statistik dokumen anggota",
            data=response_data,
            status="success"
        ), status=status.HTTP_200_OK)
