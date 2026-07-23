from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from utils.serializers import custom_response
from utils.decorators import role_required
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from alerts.serializers import DeforeStationSerializer
from alerts.models import DeforeStation
from django.db.models import Q



class AlertDeforestationListView(generics.ListAPIView):
    serializer_class = DeforeStationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, role_required(1, 3, 4, 5, 6)]
    
    def get_queryset(self):
        queryset = DeforeStation.objects.all().order_by('-created_at')
        search = self.request.query_params.get('search', None)
        alert_type = self.request.query_params.get('source_type', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        kabupaten = self.request.query_params.get('kabupaten', None)
        kecamatan = self.request.query_params.get('kecamatan', None)
        
        if alert_type:
            queryset = queryset.filter(source_type=alert_type)
            
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )

        if kabupaten:
            queryset = queryset.filter(administrative_area__DistCode=kabupaten)

        if kecamatan:
            queryset = queryset.filter(administrative_area__SubdisCode=kecamatan)
        
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search)
            )
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(custom_response(
            message="Berhasil mendapatkan data deforestation",
            data=response.data,
            status="success"
        ), status=status.HTTP_200_OK)