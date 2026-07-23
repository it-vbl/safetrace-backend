from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status, generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.shortcuts import render
from django.conf import settings
from utils.serializers import custom_response
from utils.decorators import role_required
from layer_static.models import LayerStatic, PetaStatis
from layer_static.serializers import (
    LayerStaticSerializer, LayerStaticListSerializer, PetaStatisSerializer, PetaStatisListSerializer
)


def preview_arcgis_server(request):
    return render(request, 'layer_static/preview.html')


class LayerStaticListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]

    def get(self, request):
        static_layers = LayerStatic.objects.filter(is_active=True)
        serializer = LayerStaticListSerializer(static_layers, read_only=True, many=True)
        return Response(custom_response("success", "Successfully fetched data", serializer.data),
                        status=status.HTTP_200_OK)


class LayerStaticView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]

    @method_decorator(cache_page(settings.CACHE_STATIC_LAYER))
    def get(self, request, slug):
        static_layer = get_object_or_404(LayerStatic, slug=slug)
        serializer = LayerStaticSerializer(static_layer, read_only=True)
        return Response(custom_response("success", "Successfully fetched data", serializer.data),
                        status=status.HTTP_200_OK)


class PetaStatisCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]

    def post(self, request):
        serializer = PetaStatisSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(custom_response("success", "Berhasil membuat data", serializer.data),
                            status=status.HTTP_201_CREATED)
        return Response(custom_response("error", "Gagal membuat data", serializer.errors),
                        status=status.HTTP_400_BAD_REQUEST)


class PetaStatisListView(generics.ListAPIView):
    serializer_class = PetaStatisListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]

    def get_queryset(self):
        queryset = PetaStatis.objects.all()
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Daftar pekebun berhasil diambil.",
            data=response.data,
            status="success"
        ), status=response.status_code)


class PetaStatisDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]

    def get(self, request, pk):
        peta_statis = get_object_or_404(PetaStatis, pk=pk)
        serializer = PetaStatisSerializer(peta_statis, read_only=True)
        return Response(custom_response("success", "Berhasil mendapatkan data", serializer.data),
                        status=status.HTTP_200_OK)


class PetaStatisUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]
    
    def post(self, request, pk):
        peta_statis = get_object_or_404(PetaStatis, pk=pk)
        serializer = PetaStatisSerializer(peta_statis, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(custom_response("success", "Berhasil update data", serializer.data),
                            status=status.HTTP_200_OK)
        return Response(custom_response("error", "Gagal update data", serializer.errors),
                        status=status.HTTP_400_BAD_REQUEST)


class PetaStatisDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1)]  
    
    def get(self, request, pk):
        peta_statis = get_object_or_404(PetaStatis, pk=pk)
        peta_statis.delete()
        return Response(custom_response("success", "Berhasil menghapus data", None),
                        status=status.HTTP_204_NO_CONTENT)
