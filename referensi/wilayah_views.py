from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from utils.serializers import custom_response
from wilayah_indonesia import views
from utils.mixins import WilayahDetailMixin


class WilayahProvinsiView(APIView, views.ProvinsiListView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        queryset = self.get_queryset(request)
        data = self.get_response_data(queryset)
        return Response(custom_response("success", "Successfully fetched data", data),
                        status=status.HTTP_200_OK)
    

class WilayahKabupatenView(APIView, views.KabupatenListView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, provinsi_id):
        queryset = self.get_queryset(request, provinsi_id=provinsi_id)
        data = self.get_response_data(queryset)
        return Response(custom_response("success", "Successfully fetched data", data),
                        status=status.HTTP_200_OK)
    

class WilayahKecamatanView(APIView, views.KecamatanListView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, kabupaten_id):
        queryset = self.get_queryset(request, kabupaten_id=kabupaten_id)
        data = self.get_response_data(queryset)
        return Response(custom_response("success", "Successfully fetched data", data),
                        status=status.HTTP_200_OK)
    

class WilayahDesaView(APIView, views.DesaListView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, kecamatan_id):
        queryset = self.get_queryset(request, kecamatan_id=kecamatan_id)
        data = self.get_response_data(queryset)
        return Response(custom_response("success", "Successfully fetched data", data),
                        status=status.HTTP_200_OK)
        
        
class WilayahProvinsiDetailView(WilayahDetailMixin, APIView, views.ProvinsiDetailView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class WilayahKabupatenDetailView(WilayahDetailMixin, APIView, views.KabupatenDetailView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    
class WilayahKecamatanDetailView(WilayahDetailMixin, APIView, views.KecamatanDetailView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    
class WilayahDesaDetailView(WilayahDetailMixin, APIView, views.DesaDetailView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]


class WilayahKecamatanSanggauView(APIView, views.KecamatanListView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        kab_sanggau_id = 6105
        queryset = self.get_queryset(request, kabupaten_id=kab_sanggau_id)
        data = self.get_response_data(queryset)
        return Response(custom_response("success", "Successfully fetched data", data),
                        status=status.HTTP_200_OK)