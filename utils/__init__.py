import random
import string
import os
import calendar
import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from datetime import datetime
from django.contrib.gis.geos import Point

logger = logging.getLogger(__name__)


def polygon_points_and_lengths(polygon_obj):
    """
    Extract polygon points and calculate the lengths of sides between them.
    
    Args:
        polygon_obj: A polygon geometry object with a geom attribute.
        
    Returns:
        tuple: A tuple containing:
            - results (list): List of dictionaries with point labels and DMS coordinates
            - lengths (list): List of dictionaries with distance between consecutive points in meters
    """
    poly = polygon_obj.geom
    if poly.geom_type == 'MultiPolygon':
        poly = poly[0]
    
    # Extract outer ring coordinates
    coords = list(poly.coords[0])[:-1]  # without closing point
    
    results = []
    for i, coord in enumerate(coords):
        lat, lon = coord[1], coord[0]  # GEOSPolygon uses (x=lon, y=lat)
        label = f"C{i+1}"
        results.append({
            "label": label,
            "coord": f"{lon_to_dms(lon)}, {lat_to_dms(lat)}"
        })
    
    # Calculate side lengths
    lengths = []
    for i in range(len(coords)):
        start = coords[i]
        end = coords[(i+1) % len(coords)]  # wrap to C1
        
        p1 = Point(start, srid=4326)
        p2 = Point(end, srid=4326)
        _ = p1.distance(p2)  # default: degrees
        
        # Convert to meters (transform to SRID 3857)
        p1.transform(3857)
        p2.transform(3857)
        dist_m = p1.distance(p2)  # in meters
        
        lengths.append({
            "from": f"C{i+1}",
            "to": f"C{(i+1)%len(coords) + 1}",
            "length_m": round(dist_m, 2)
        })
    
    return results, lengths


def lon_to_dms(lon):
    """
    Convert longitude from decimal degrees to Degrees, Minutes, Seconds (DMS) format.
    
    Args:
        lon (float): Longitude in decimal degrees.
        
    Returns:
        str: Longitude in DMS format with E/W indicator.
    """
    deg = int(lon)
    min_ = abs((lon - deg) * 60)
    sec = (min_ - int(min_)) * 60
    return f"{abs(deg)}°{int(min_)}'{sec:.2f}\"{'E' if lon >= 0 else 'W'}"


def lat_to_dms(lat):
    """
    Convert latitude from decimal degrees to Degrees, Minutes, Seconds (DMS) format.
    
    Args:
        lat (float): Latitude in decimal degrees.
        
    Returns:
        str: Latitude in DMS format with N/S indicator.
    """
    deg = int(lat)
    min_ = abs((lat - deg) * 60)
    sec = (min_ - int(min_)) * 60
    return f"{abs(deg)}°{int(min_)}'{sec:.2f}\"{'N' if lat >= 0 else 'S'}"


def str_to_bool(val):
    """
    Convert various data types to boolean.
    
    Args:
        val: Value to convert (bool, str, int, or other).
        
    Returns:
        bool: Boolean representation of the value.
    """
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes")
    if isinstance(val, int):
        return val == 1
    return False


def generate_username_from_email(email):
    """
    Generate a unique username from an email address.
    If the username already exists, append random digits until a unique one is found.
    
    Args:
        email (str): Email address to generate username from.
        
    Returns:
        str: Unique username based on email.
    """
    username = email.split("@")[0]
    while get_user_model().objects.filter(username=username).exists():
        rand_suffix = ''.join(random.choices(string.digits, k=4))
        username = f"{username}{rand_suffix}"
    return username


class PaginationDefault(PageNumberPagination):
    """
    Default pagination configuration for API responses.
    
    Attributes:
        page_size (int): Default number of items per page (25).
        page_size_query_param (str): Query parameter name for custom page size.
        max_page_size (int): Maximum allowed page size (100).
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100
    

def get_start_and_end_of_month(year, month):
    """
    Get the first and last day of a given month as datetime objects.
    
    Args:
        year (int): The year.
        month (int): The month (1-12).
        
    Returns:
        tuple: A tuple containing (start_date, end_date) as datetime objects.
    """
    start_date = datetime(year, month, 1)

    _, last_day = calendar.monthrange(year, month)
    end_date = datetime(year, month, last_day)

    return start_date, end_date


def delete_unused_media_file(model):
    """
    Delete media files that are no longer being used by any model instances.
    
    Scans the MEDIA_ROOT directory for files and compares them against active model instances.
    Any files not referenced by the model are deleted. Errors are logged but do not interrupt execution.
    
    Args:
        model: Django model class to check for file field usage.
    """
    try:
        # Get all media files in MEDIA_ROOT
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            return
            
        used_files = set()
        
        for field in model._meta.get_fields():
            if hasattr(field, 'upload_to'):  # FileField or ImageField
                for obj in model.objects.all():
                    file_field = getattr(obj, field.name)
                    if file_field and hasattr(file_field, 'path'):
                        try:
                            used_files.add(os.path.abspath(file_field.path))
                        except ValueError:
                            continue
        
        # Find and delete unused files
        for root, dirs, files in os.walk(media_root):
            for file in files:
                file_path = os.path.abspath(os.path.join(root, file))
                if file_path not in used_files:
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted unused media file: {file_path}")
                    except OSError as e:
                        logger.error(f"Error deleting file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning up media files: {e}")