"""Great-circle geofencing using the Haversine formula (stdlib math only)."""
import math

from django.conf import settings

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two WGS-84 points, in kilometres."""
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c


def distance_from_restaurant_km(latitude, longitude):
    return haversine_km(
        settings.RESTAURANT_LAT, settings.RESTAURANT_LNG, latitude, longitude
    )


def within_delivery_radius(latitude, longitude):
    """True if the customer coordinates fall inside the delivery radius."""
    return (
        distance_from_restaurant_km(latitude, longitude)
        <= settings.DELIVERY_RADIUS_KM
    )
