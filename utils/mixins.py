import csv
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from kebun.models import Kebun
from utils.serializers import custom_response
from datetime import datetime
from utils import get_start_and_end_of_month


class WilayahDetailMixin:
    """
    Mixin for handling detail view responses for a specific region (wilayah).
    Provides a GET method that retrieves response data and returns it in a standardized format.
    """
    
    def get(self, request, *args, **kwargs):
        try:
            data = self.get_response_data() # type: ignore
            return Response(custom_response("success", "Successfully fetched data", data),
                            status=status.HTTP_200_OK)
        except self.model.DoesNotExist: # type: ignore
            return Response(custom_response("error", "Data not found"), status=status.HTTP_400_BAD_REQUEST)


class DateParserMixin:
    """
    Mixin for parsing and extracting date ranges from request parameters.
    Supports filtering by month, year, or custom start/end dates.
    """
    def get_date_range(self, request):
        month = request.GET.get('month', None)
        year = request.GET.get('year', None)
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)

        if month and not year:
            now = datetime.now()
            start_date, end_date = get_start_and_end_of_month(now.year, int(month))
        elif not month and year:
            start_date, _ = get_start_and_end_of_month(int(year), 1)
            _, end_date = get_start_and_end_of_month(int(year), 12)
        elif month and year:
            start_date, end_date = get_start_and_end_of_month(int(year), int(month))
        elif start_date and end_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            now = datetime.now()
            start_date = datetime(year=now.year, month=1, day=1)
            end_date = now

        return start_date, end_date

class DownloadListMixin:
    """
    Mixin for downloading data in CSV format.
    Subclasses must implement create_header() and create_data() methods.
    """
    filename_download = "safetrace_data_download"
    pagination_class = None
    
    def create_header(self):
        """Create CSV header row.
        
        Example:
            return ['header1', 'header2', 'header3']
        """
        raise NotImplementedError("Subclasses must implement create_header() method")
        
    def create_data(self, data):
        """Transform data into list of rows for CSV export.
        
        Example:
            list_data = []
            for item in data:
                list_data.append([item['field1'], item['field2'], item['field3']])
            return list_data
        """
        raise NotImplementedError("Subclasses must implement create_data() method")
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Override data response
        data = response.data.get('data')

        # Create CSV file response
        response = HttpResponse(content_type='text/csv')
        now = datetime.now()
        response['Content-Disposition'] = f'attachment; filename="{self.filename_download}-{now}.csv"'
        # Write data to response
        writer = csv.writer(response)
        writer.writerow(self.create_header())  # Header
        
        list_data = self.create_data(data)
        for d in list_data:
            writer.writerow(d)
        return response


class KebunGAPQueryMixin:
    """
    Mixin for performing query filtering on Kebun queryset in the GAP application.
    Provides filtering by farmer groups (kelompok), year (tahun), sorting, and search functionality.
    """
    tahun_filter = None
    
    def get_queryset(self):
        kelompok = self.request.GET.getlist('kelompok', None)
        tahun = self.request.GET.get('tahun', None)
        sort = self.request.GET.get('sort', None)
        search = self.request.GET.get('search', None)
        queryset = Kebun.objects.all().order_by('-created_at')
        
        if kelompok:
            queryset = queryset.filter(petani__nama_kelompok__in=kelompok)
            
        if tahun:
            self.tahun_filter = tahun
        
        if sort == 'oldest':
            queryset = queryset.order_by('updated_at')    
        else:
            queryset = queryset.order_by('-updated_at')
            
        if search:
            queryset = queryset.filter(
                petani__nama__icontains=search
            ) | queryset.filter(
                petani__no_ktp__icontains=search
            ) | queryset.filter(
                id_kebun__icontains=search
            )
        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Override to pass tahun_filter (year filter) directly to serializer.
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        kwargs['tahun'] = self.tahun_filter  # Add year filter
        return serializer_class(*args, **kwargs)
