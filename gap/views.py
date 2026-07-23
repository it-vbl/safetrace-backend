from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from utils.serializers import custom_response
from utils.decorators import role_required
from utils.mixins import KebunGAPQueryMixin, DownloadListMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from kebun.models import Kebun
from gap.serializers import (
    ProduksiSerializer, PenggunaanPestisidaSerializer, LB3Serializer, PenggunaanPupukSerializer, 
    KebunGAPProduksiListSerializer, KebunGAPestisidaListSerializer, KebunGALB3ListSerializer,
    KebunGAPPupukListSerializer
)
from gap.models import Produksi, PenggunaanPestisida, LB3, PenggunaanPupuk


class ProduksiListView(KebunGAPQueryMixin, generics.ListAPIView):
    serializer_class = KebunGAPProduksiListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun",
            data=response.data,
            status="success"
        ), status=response.status_code)


class ProduksiDownloadView(DownloadListMixin, ProduksiListView):
    filename_download = "produksi_data"
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create_header(self):
        return [
            'ID', 
            'ID Kebun', 
            'Nama Petani', 
            'Kelompok Tani', 
            'Total Produksi', 
            'Umur Tanaman', 
            'Luas Kebun', 
            'Tahun Tanam', 
            'Produksi per Ha per Tahun'
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['kebun_id'],
                item['id_kebun'],
                item['nama_petani'],
                item['kelompok_tani'],
                item['total_produksi'],
                item['umur_tanaman'],
                item['luas_kebun'],
                item['tahun_tanam'],
                item['prod_ha_th'],
            ])
        return list_data


class ProduksiByKebunListView(generics.ListAPIView):
    serializer_class = ProduksiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self):
        kebun_id = self.kwargs.get('kebun_id')
        queryset = Produksi.objects.filter(kebun_id=kebun_id).order_by('-updated_at')
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Produksi",
            data=response.data,
            status="success"
        ), status=response.status_code)
        

class KebunGAPProduksiDetailView(generics.RetrieveAPIView):
    serializer_class = KebunGAPProduksiListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = Kebun.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun",
            data=response.data,
            status="success"
        ), status=response.status_code)

        
class ProduksiDetailView(generics.RetrieveAPIView):
    serializer_class = ProduksiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Produksi.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun",
            data=response.data,
            status="success"
        ), status=response.status_code)  


class ProduksiCreateView(generics.CreateAPIView):
    serializer_class = ProduksiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil membuat data Produksi",
            data=response.data,
            status="success"
        ), status=response.status_code)


class ProduksiUpdateView(generics.UpdateAPIView):
    serializer_class = ProduksiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Produksi.objects.all()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil memperbarui data Produksi",
            data=response.data,
            status="success"
        ), status=response.status_code)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class ProduksiDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = Produksi.objects.all()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data Produksi",
            data=None,
            status="success"
        ), status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class PenggunaanPestisidaListView(KebunGAPQueryMixin, generics.ListAPIView):
    serializer_class = KebunGAPestisidaListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Penggunaan Pestisida",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PenggunaanPestisidaDownloadView(DownloadListMixin, PenggunaanPestisidaListView):
    filename_download = "penggunaan_pestisida_data"
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create_header(self):
        return [
            'ID', 
            'ID Kebun', 
            'Nama Petani', 
            'Kelompok Tani', 
            'Total Pestisida', 
            'Umur Tanaman', 
            'Luas Kebun', 
            'Tahun Tanam',
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['kebun_id'],
                item['id_kebun'],
                item['nama_petani'],
                item['kelompok_tani'],
                item['total_pestisida'],
                item['umur_tanaman'],
                item['luas_kebun'],
                item['tahun_tanam'],
            ])
        return list_data


class PenggunaanPestisidaByKebunListView(generics.ListAPIView):
    serializer_class = PenggunaanPestisidaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self):
        kebun_id = self.kwargs.get('kebun_id')
        queryset = PenggunaanPestisida.objects.filter(kebun_id=kebun_id).order_by('-updated_at')
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Penggunaan Pestisida",
            data=response.data,
            status="success"
        ), status=response.status_code)
        

class KebunGAPPestisidaDetailView(generics.RetrieveAPIView):
    serializer_class = KebunGAPestisidaListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = Kebun.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun",
            data=response.data,
            status="success"
        ), status=response.status_code)
        
        
class PenggunaanPestisidaDetailView(generics.RetrieveAPIView):
    serializer_class = PenggunaanPestisidaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = PenggunaanPestisida.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Penggunaan Pestisida",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PenggunaanPestisidaCreateView(generics.CreateAPIView):
    serializer_class = PenggunaanPestisidaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil membuat data Penggunaan Pestisida",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PenggunaanPestisidaUpdateView(generics.UpdateAPIView):
    serializer_class = PenggunaanPestisidaSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = PenggunaanPestisida.objects.all()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil memperbarui data Penggunaan Pestisida",
            data=response.data,
            status="success"
        ), status=response.status_code)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class PenggunaanPestisidaDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = PenggunaanPestisida.objects.all()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data Penggunaan Pestisida",
            data=None,
            status="success"
        ), status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class LB3ListView(KebunGAPQueryMixin, generics.ListAPIView):
    serializer_class = KebunGALB3ListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data LB3",
            data=response.data,
            status="success"
        ), status=response.status_code)


class LB3DownloadView(DownloadListMixin, LB3ListView):
    filename_download = "lb3_data"
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create_header(self):
        return [
            'ID', 
            'ID Kebun', 
            'Nama Petani', 
            'Kelompok Tani', 
            'Total LB3', 
            'Umur Tanaman', 
            'Luas Kebun', 
            'Tahun Tanam',
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['kebun_id'],
                item['id_kebun'],
                item['nama_petani'],
                item['kelompok_tani'],
                item['total_lb3'],
                item['umur_tanaman'],
                item['luas_kebun'],
                item['tahun_tanam'],
            ])
        return list_data


class KebunGAPLB3DetailView(generics.RetrieveAPIView):
    serializer_class = KebunGALB3ListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = Kebun.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun LB3",
            data=response.data,
            status="success"
        ), status=response.status_code)
        

class LB3ByKebunListView(generics.ListAPIView):
    serializer_class = LB3Serializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self):
        kebun_id = self.kwargs.get('kebun_id')
        queryset = LB3.objects.filter(kebun_id=kebun_id).order_by('-updated_at')
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data LB3",
            data=response.data,
            status="success"
        ), status=response.status_code)

        
class LB3DetailView(generics.RetrieveAPIView):
    serializer_class = LB3Serializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = LB3.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data LB3",
            data=response.data,
            status="success"
        ), status=response.status_code)


class LB3CreateView(generics.CreateAPIView):
    serializer_class = LB3Serializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil membuat data LB3",
            data=response.data,
            status="success"
        ), status=response.status_code)


class LB3UpdateView(generics.UpdateAPIView):
    serializer_class = LB3Serializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = LB3.objects.all()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil memperbarui data LB3",
            data=response.data,
            status="success"
        ), status=response.status_code)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class LB3DeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = LB3.objects.all()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data LB3",
            data=None,
            status="success"
        ), status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class PenggunaanPupukListView(KebunGAPQueryMixin, generics.ListAPIView):
    serializer_class = KebunGAPPupukListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Penggunaan Pupuk",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PenggunaanPupukDownloadView(DownloadListMixin, PenggunaanPupukListView):
    filename_download = "penggunaan_pupuk_data"
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    
    def create_header(self):
        return [
            'ID', 
            'ID Kebun', 
            'Nama Petani', 
            'Kelompok Tani', 
            'Total Pupuk', 
            'Umur Tanaman', 
            'Jumlah Pokok',
            'Luas Kebun', 
            'Tahun Tanam',
        ]
    
    def create_data(self, data):
        list_data = []
        for item in data:
            list_data.append([
                item['kebun_id'],
                item['id_kebun'],
                item['nama_petani'],
                item['kelompok_tani'],
                item['total_pupuk'],
                item['umur_tanaman'],
                item['jumlah_pokok'],
                item['luas_kebun'],
                item['tahun_tanam'],
            ])
        return list_data


class KebunGAPPupukDetailView(generics.RetrieveAPIView):
    serializer_class = KebunGAPPupukListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = Kebun.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Kebun LB3",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PenggunaanPupukByKebunListView(generics.ListAPIView):
    serializer_class = PenggunaanPupukSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    
    def get_queryset(self):
        kebun_id = self.kwargs.get('kebun_id')
        queryset = PenggunaanPupuk.objects.filter(kebun_id=kebun_id).order_by('-updated_at')
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Penggunaan Pupuk",
            data=response.data,
            status="success"
        ), status=response.status_code)
        
        
class PenggunaanPupukDetailView(generics.RetrieveAPIView):
    serializer_class = PenggunaanPupukSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5)]
    queryset = PenggunaanPupuk.objects.all()

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data Penggunaan Pupuk",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PenggunaanPupukCreateView(generics.CreateAPIView):
    serializer_class = PenggunaanPupukSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil membuat data Penggunaan Pupuk",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PenggunaanPupukUpdateView(generics.UpdateAPIView):
    serializer_class = PenggunaanPupukSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = PenggunaanPupuk.objects.all()

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil memperbarui data Penggunaan Pupuk",
            data=response.data,
            status="success"
        ), status=response.status_code)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class PenggunaanPupukDeleteView(generics.DestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3)]
    queryset = PenggunaanPupuk.objects.all()

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil menghapus data Penggunaan Pupuk",
            data=None,
            status="success"
        ), status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)