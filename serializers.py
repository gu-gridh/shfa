from diana.abstract.serializers import DynamicDepthSerializer, GenericSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from . import models
from diana.utils import get_fields, DEFAULT_FIELDS
from .models import *


class TIFFImageSerializer(DynamicDepthSerializer):

    class Meta:
        model = Image
        fields = get_fields(Image, exclude=DEFAULT_FIELDS)

class SiteSerializer(DynamicDepthSerializer):

    class Meta:
        model = Site
        fields = get_fields(Site, exclude=DEFAULT_FIELDS)

class SiteGeoSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = Site
        fields = get_fields(Site, exclude=DEFAULT_FIELDS)
        geo_field = 'coordinates'