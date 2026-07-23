import json
from datetime import datetime, timedelta
from typing import Dict, List
from django.contrib.gis.geos import GEOSGeometry
from alerts.models import DeforeStation
from django.contrib.gis.geos import MultiPolygon
from alerts.models import AdmDesaArea
from layer_static.models import LayerStatic
from kebun.models import Kebun


def convert_yydoy_to_date(yydoy: str) -> datetime:
    """
    yydoy: YYDOY (Year Day of Year) ex. 24120
    """
    # split YY and DOY
    year = int(yydoy[:2])
    day_of_year = int(yydoy[2:])

    # if year less than 50, adding 2000
    if year < 50:
        year += 2000
    else:
        year += 1900

    # Create first date and month
    date = datetime(year, 1, 1)

    # Adding DOY
    date = date + timedelta(days=day_of_year - 1)
    return date


def convert_doy_to_date(doy: str, year='') -> datetime:
    """
    year: 2 digit of year
    doy: number of day
    """
    if not year:
        year = str(datetime.now().year)
    year_2_digit = year[-2:]
    datestr = f"{year_2_digit}{doy}"
    return convert_yydoy_to_date(datestr)


def _normalize_to_multipolygon(geom: GEOSGeometry) -> MultiPolygon:
    if geom.geom_type == 'Polygon':
        return MultiPolygon(geom)
    if geom.geom_type == 'MultiPolygon':
        return geom
    raise ValueError(f"Unsupported geometry type: {geom.geom_type}")


def _parse_geojson_geometry(geometry_data):
    if not geometry_data:
        return None

    geom = GEOSGeometry(json.dumps(geometry_data))
    if geom.srid is None:
        geom.srid = 4326
    return _normalize_to_multipolygon(geom)


def _parse_layer_static_geometries(layer: LayerStatic) -> List[MultiPolygon]:
    try:
        geojson_data = layer.to_geojson()
    except Exception:
        return []

    if not isinstance(geojson_data, dict):
        return []

    features = geojson_data.get('features', [])
    geometries = []

    for feature in features:
        try:
            geom = _parse_geojson_geometry(feature.get('geometry'))
        except Exception:
            continue

        if geom:
            geometries.append(geom)

    return geometries


def _load_active_layer_static_geometries() -> List[Dict]:
    """
    Load all active static layers and parse all GeoJSON feature geometries once.
    """
    parsed_layers = []
    active_layers = LayerStatic.objects.filter(is_active=True).order_by('order')

    for layer in active_layers:
        layer_geoms = _parse_layer_static_geometries(layer)

        if layer_geoms:
            parsed_layers.append({
                'id': layer.id,
                'slug': layer.slug,
                'name': layer.name,
                'geometries': layer_geoms,
            })

    return parsed_layers


def get_intersected_layer_static(area: MultiPolygon, parsed_layers: List[Dict]) -> List[Dict]:
    """
    Return active LayerStatic metadata that intersects with provided area geometry.
    """
    impacted_layers = []
    for layer in parsed_layers:
        if any(area.intersects(layer_geom) for layer_geom in layer['geometries']):
            impacted_layers.append({
                'id': layer['id'],
                'slug': layer['slug'],
                'name': layer['name'],
            })
    return impacted_layers


def get_impacted_kebun(area: MultiPolygon, radius_meter: int = 500) -> List[Dict]:
    """
    Find impacted kebun by intersecting area with candidate kebun within radius from area centroid.
    """
    if not area:
        return []

    centroid = area.centroid
    if centroid.srid is None:
        centroid.srid = 4326

    # Use buffer + intersects to avoid dwithin which internally queries
    # spatial_ref_sys (missing SRID 4326 causes DoesNotExist error).
    # 1 degree ≈ 111,320 m at the equator.
    degree_radius = radius_meter / 111320.0
    buffered = centroid.buffer(degree_radius)

    candidate_kebun = Kebun.objects.filter(
        geom__isnull=False,
        geom__intersects=buffered,
    ).select_related('petani')

    impacted = []
    for kebun in candidate_kebun:
        try:
            if not kebun.geom or not area.intersects(kebun.geom):
                continue
        except Exception:
            continue

        impacted.append({
            'id': kebun.id,
            'id_kebun': kebun.id_kebun,
            'petani_id': kebun.petani_id,
            'petani': str(kebun.petani.nama) if kebun.petani else "",
        })

    return impacted


def save_data_deforestation(file_path, source_type='glad') -> List[int]:
    try:
        with open(file_path, 'r') as f:
            geojson_data = json.load(f)
    except TypeError:
        geojson_data = json.load(file_path)

    ids = []
    parsed_layers = _load_active_layer_static_geometries()
    for feature in geojson_data['features']:
        geometry = feature['geometry']
        properties = feature['properties']

        # Convert geometry to MultiPolygon
        geom = _parse_geojson_geometry(geometry)

        # Get label and date
        label = properties.get('label')
        if not label:
            continue

        if source_type == 'glad':
            date = convert_doy_to_date(str(label))
        else:
            date = convert_yydoy_to_date(str(label))

        # Save to model
        impacted_layers = get_intersected_layer_static(geom, parsed_layers)
        impacted_kebun = get_impacted_kebun(geom, radius_meter=500)

        deforestation, _ = DeforeStation.objects.update_or_create(
            label=label,
            source_type=source_type,
            defaults={
                'geom': geom,
                'properties': properties,
                'date': date,
                'area_ha': properties.get('area_ha', 0.0),
                'raw_data': {
                    'layer_static_intersections': impacted_layers,
                    'layer_static_intersection_count': len(impacted_layers),
                    'impacted_kebun': impacted_kebun,
                    'impacted_kebun_count': len(impacted_kebun),
                },
            },
        )
        
        # intersection ke wilayah administrasi desa
        adm_desa = get_adm_desa_by_area(deforestation.geom)
        deforestation.save_adm_desa_data(adm_desa)
        ids.append(deforestation.id)
    return list(set(ids))


def import_geojson(file_path, source_type='glad') -> None:
    save_data_deforestation(file_path, source_type=source_type)
    # send notification if needed, for example using signals or directly here after saving data

        
def get_adm_desa_by_area(area: MultiPolygon) -> dict:
    desa_area = AdmDesaArea.objects.filter(geom__contains=area).first()
    if desa_area:
        return desa_area.properties
    else:
        return {}