import ee
import json
import os
import re
from datetime import datetime
from django.conf import settings
from alerts.utils import import_geojson


class GEEGetDataDeforestation:
    """
    A class to retrieve and process deforestation alert data from Google Earth Engine (GEE).
    
    This class integrates GLAD (Global Land Analysis & Discovery) and RADD (Radar for Detecting Deforestation)
    alert datasets to monitor deforestation events within the West Kalimantan region. It handles data
    retrieval from GEE, GeoJSON export, and database import.
    
    Attributes:
        export_dir (str): Directory path where GeoJSON files are exported.
        glad_filename (str): Filename for GLAD alert vectors GeoJSON export.
        radd_filename (str): Filename for RADD alert vectors GeoJSON export.
        roi (ee.FeatureCollection): Region of interest as a buffered feature collection.
        buffered_image (ee.Image): Clipped image used for masking GEE operations.
        start_date (str): Start date for filtering alerts (format: YYYY-MM-DD).
        end_date (str): End date for filtering alerts (format: YYYY-MM-DD).
        glad_year (int): The year associated with GLAD alert data.
    """
    
    def __init__(self, start_date: str, end_date: str) -> None:
        """
        Initialize the GEEGetDataDeforestation class and set up Google Earth Engine connection.
        
        Args:
            start_date (str): Start date for alert filtering in 'YYYY-MM-DD' format.
            end_date (str): End date for alert filtering in 'YYYY-MM-DD' format.
            
        Raises:
            FileNotFoundError: If the GEE service account key file is not found.
            ee.EEException: If Earth Engine initialization fails.
        """
        # Initialize Earth Engine
        service_account_key = settings.GEE_SERVICE_ACCOUNT_KEY_PATH
        if not os.path.isabs(service_account_key):
            service_account_key = os.path.join(settings.BASE_DIR, service_account_key)

        credentials = ee.ServiceAccountCredentials(
            settings.GEE_SERVICE_ACCOUNT_EMAIL,
            service_account_key
        )
        ee.Initialize(credentials=credentials)

        # Create the export folder
        self.export_dir = os.path.join(settings.MEDIA_ROOT, 'gee_exports')
        os.makedirs(self.export_dir, exist_ok=True)
        self.glad_filename = 'GLAD_Alert_Vectors.geojson'
        self.radd_filename = 'RADD_Alert_Vectors.geojson'

        # Region of interest (ROI) as a buffered version of the West Kalimantan project boundary
        project_boundary = ee.Geometry.Polygon(
            [[[109.0532566179954159, 1.1999330666189889],
              [109.0532566179954159, -1.3203302776492540],
              [113.4437809674869868, -1.3203302776492540],
              [113.4437809674869868, 1.1999330666189889]]],
            None,
            False
        )
        buffered = ee.FeatureCollection([ee.Feature(project_boundary)]) \
            .map(lambda feature: feature.buffer(2000))  # Buffer in meters (2 km)

        self.buffered_image = ee.Image(1).clip(buffered)
        self.roi = buffered  # Region of interest

        # Set the date range
        self.start_date = start_date
        self.end_date = end_date
        self.glad_year = datetime.now().year

    def get_glad_band_config(self, image):
        # Select the latest available GLAD alert/conf bands from the image.
        band_names = image.bandNames().getInfo()
        candidates = []

        for band in band_names:
            match = re.match(r'^alertDate(\d{2})$', band)
            if not match:
                continue

            suffix = match.group(1)
            conf_band = f'conf{suffix}'
            if conf_band in band_names:
                candidates.append((int(suffix), band, conf_band))

        if not candidates:
            raise ValueError(
                f"Band GLAD tidak ditemukan. Band tersedia: {band_names}"
            )

        _, alert_band, conf_band = max(candidates, key=lambda item: item[0])
        return alert_band, conf_band

    def date_to_julian(self, date_str):
        # Convert the date string to datetime
        date = datetime.strptime(date_str, '%Y-%m-%d')

        # Year in two-digit format (example: 2024 -> 24)
        year = date.year % 100

        # Day of year
        day_of_year = date.timetuple().tm_yday

        # Combine year and day into YYDDD format
        julian_date = f"{year:02d}{day_of_year:03d}"
        return julian_date

    def julian_to_date(self, julian):
        # Convert RADD Julian date (YYDDD) to YYYY-MM-DD
        year = ee.Number.parse(julian.slice(0, 2)).add(2000)
        day_of_year = ee.Number.parse(julian.slice(2))

        # Leap year handling
        is_leap_year = year.mod(4).eq(0).And(year.mod(100).neq(0)).Or(year.mod(400).eq(0))
        days_in_year = ee.Algorithms.If(is_leap_year, 366, 365)

        valid_day_of_year = day_of_year.min(days_in_year)
        date = ee.Date.fromYMD(year, 1, 1).advance(valid_day_of_year.subtract(1), 'day')
        return date.format('YYYY-MM-dd')

    def ddd_to_date(self, ddd, year):
        # Convert GLAD DDD date to YYYY-MM-DD
        date = ee.Date.fromYMD(year, 1, 1).advance(ddd.subtract(1), 'day')
        return date.format('YYYY-MM-dd')

    def datetime_to_ddd(self, date_str, date_format='%Y-%m-%d'):
        # Day of year
        date_obj = datetime.strptime(date_str, date_format)
        day_of_year = date_obj.timetuple().tm_yday

        # Format as three digits (e.g. 001, 032, 365)
        return f"{day_of_year:03d}"

    def add_area_property(self, feature):
        # Compute area in hectares and store it as a property with 2 decimal places
        buffer = feature.geometry().buffer(1)  # Add a small buffer to ensure a valid area calculation
        area_sq_m = buffer.area()  # Area in square meters
        area_ha = area_sq_m.divide(10000)  # Convert to hectares
        area_ha_formatted = ee.Number(area_ha).format('%.2f')  # Format to 2 decimal places
        return feature.set('area_ha', area_ha_formatted)

    def simplify_geometry(self, feature):
        # Simplify the geometry
        simplified = feature.geometry().simplify(1)  # Simplify geometry with a 1 meter tolerance
        return feature.setGeometry(simplified)

    def add_centroid_coordinates(self, feature):
        # Extract centroid coordinates and add them to the feature with an error margin
        centroid = feature.geometry().centroid(1)  # 1 meter error margin
        coordinates = centroid.coordinates()

        return feature.set({
            'centroid_x': coordinates.get(0),  # Longitude
            'centroid_y': coordinates.get(1),  # Latitude
            'centroid': centroid  # Optional: store the centroid geometry too
        })

    def process_radd_feature(self, feature):
        # Extract and process a RADD feature
        label = ee.String(feature.get('label'))

        # Check whether the label is valid and contains the expected date information
        julian_date = label.slice(0, 7)  # Extract the YYDDD part

        # Check the julianDate length
        valid_julian_date = julian_date.length().eq(5)
        date = ee.Algorithms.If(
            valid_julian_date,
            self.julian_to_date(julian_date),
            'Invalid Date'  # Default value for an invalid date
        )

        month = ee.Algorithms.If(valid_julian_date, ee.Date(date).get('month'), None)

        return self.add_centroid_coordinates(self.add_area_property(self.simplify_geometry(feature))) \
            .set('date', date) \
            .set('alert_type', 'RADD') \
            .set('month', month)

    def process_glad_feature(self, feature):
        # Extract and process a GLADGE feature
        label = ee.Number.parse(feature.get('label'))
        ddd = label.mod(1000)  # Ekstrak bagian DDD
        year = self.glad_year
        date = self.ddd_to_date(ddd, year)
        month = ee.Date(date).get('month')

        return self.add_centroid_coordinates(self.add_area_property(self.simplify_geometry(feature))) \
            .set('date', date) \
            .set('alert_type', 'GLAD') \
            .set('month', month)

    def radd_export_geojson(self):
        # Initialize the RADD alerts image collection
        radd_asset = ee.ImageCollection('projects/radar-wur/raddalert/v1')
        # print('RADD image collection:', radd_asset.getInfo())

        # Get the latest RADD alert for Asia
        latest_radd_alert = ee.Image(
            radd_asset.filterMetadata('layer', 'contains', 'alert')
            .filterMetadata('geography', 'contains', 'asia')
            .sort('system:time_end', False)
            .first()
        ).mask(self.buffered_image)

        # print('Latest RADD alert ASIA:', latest_radd_alert.getInfo())

        # Convert the latest RADD alert by selecting and renaming bands
        radd_alert = latest_radd_alert.select(['Date', 'Alert'], ['label', 'conf']) \
            .focal_mode(2, 'square', 'pixels')

        # Mask based on confidence level
        radd_conf = radd_alert.select('conf').remap([3], [2])
        radd_alert_conf = radd_alert.select('label').mask(radd_conf)

        # Add date, area, alert type, and simplified geometry for the RADD vectors
        radd_vectors = radd_alert_conf.reduceToVectors(
            geometry=self.roi,
            scale=10,
            geometryType='polygon',
            eightConnected=False,
            maxPixels=1e10
        ).map(self.process_radd_feature)

        # Filter data by date
        start_date_julian = self.date_to_julian(self.start_date)
        end_date_julian = self.date_to_julian(self.end_date)
        radd_vectors2 = radd_vectors \
            .filterMetadata('label', 'greater_than', int(start_date_julian)) \
            .filterMetadata('label', 'less_than', int(end_date_julian))

        # Retrieve the RADD vector features as GeoJSON from the GEE server
        radd_vectors_geojson = radd_vectors2.select(
            ['label', 'date', 'area_ha', 'alert_type', 'month', 'centroid_x', 'centroid_y']).getInfo()

        # Save to a local GeoJSON file
        file_path = os.path.join(self.export_dir, self.radd_filename)
        with open(file_path, 'w') as geojson_file:
            json.dump(radd_vectors_geojson, geojson_file)

        print("Data saved locally as RADD_Alert_Vectors.geojson.")

    def glad_export_geojson(self):
        # Initialize the GLAD alerts image collection
        glad_asset = ee.ImageCollection('projects/glad/alert/UpdResult')
        # print('GLAD image collection:', glad_asset.getInfo())

        radd_asset = ee.ImageCollection('projects/radar-wur/raddalert/v1')
        # print('RADD image collection:', radd_asset.getInfo())

        # Extract the forest baseline
        forest_baseline = ee.Image(
            radd_asset.filterMetadata('layer', 'contains', 'forest_baseline')
            .filterMetadata('geography', 'contains', 'asia')
            .first()
        ).updateMask(self.buffered_image)

        latest_glad_alert = ee.Image(
            glad_asset.filterMetadata('system:index', 'contains', '_ASIA')
            .sort('system:time_start', False)
            .first()
        ).mask(self.buffered_image)

        # print('Latest GLAD alert ASIA:', latest_glad_alert.getInfo())

        alert_band, conf_band = self.get_glad_band_config(latest_glad_alert)
        self.glad_year = 2000 + int(alert_band[-2:])

        # Convert the latest GLAD alert into an image collection and select/convert bands
        glad_alert = ee.ImageCollection([latest_glad_alert]) \
            .select([alert_band, conf_band], ['label', 'conf']) \
            .mosaic() \
            .focal_mode(2, 'square', 'pixels')

        glad_conf = glad_alert.select('conf').remap([3], [1])
        glad_alert_conf = glad_alert.select('label').mask(glad_conf)

        # Mask GLAD alerts with the forest baseline
        glad_forest_mask = glad_alert_conf.updateMask(forest_baseline)

        # Add date, area, alert type, and simplified geometry for the GLAD vectors
        glad_vectors = glad_forest_mask.reduceToVectors(
            geometry=self.roi,
            scale=30,
            geometryType='polygon',
            eightConnected=False,
            maxPixels=1e10
        ).map(self.process_glad_feature)

        start_date_ddd = self.datetime_to_ddd(self.start_date)
        end_date_ddd = self.datetime_to_ddd(self.end_date)
        glad_vectors2 = glad_vectors \
            .filterMetadata('label', 'greater_than', int(start_date_ddd)) \
            .filterMetadata('label', 'less_than', int(end_date_ddd))

        # Retrieve the GLAD vector features as GeoJSON from the GEE server
        glad_vectors_geojson = glad_vectors2.select(
            ['label', 'date', 'area_ha', 'alert_type', 'month', 'centroid_x', 'centroid_y']).getInfo()

        # Save data to a local GeoJSON file
        file_path = os.path.join(self.export_dir, self.glad_filename)
        with open(file_path, 'w') as geojson_file:
            json.dump(glad_vectors_geojson, geojson_file)

        print("Data saved locally as GLAD_Alert_Vectors.geojson.")

    def import_data_radd_to_db(self):
        radd_file_path = os.path.join(self.export_dir, self.radd_filename)
        import_geojson(radd_file_path,'radd')

    def import_data_glad_to_db(self):
        glad_file_path = os.path.join(self.export_dir, self.glad_filename)
        import_geojson(glad_file_path,'glad')