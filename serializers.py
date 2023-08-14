from diana.abstract.serializers import DynamicDepthSerializer, GenericSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from . import models
from diana.utils import get_fields, DEFAULT_FIELDS
from .models import *


class TIFFImageSerializer(DynamicDepthSerializer):

    class Meta:
        model = Image
        fields = ['id']+get_fields(Image, exclude=DEFAULT_FIELDS)

class SiteSerializer(DynamicDepthSerializer):

    class Meta:
        model = Site
        fields = ['id']+get_fields(Site, exclude=DEFAULT_FIELDS)

class SiteGeoSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = Site
        fields = ['id']+get_fields(Site, exclude=DEFAULT_FIELDS)
        geo_field = 'coordinates'


class KeywordsSerializer(DynamicDepthSerializer):

    class Meta:
        model = KeywordTag
        fields = ['id']+get_fields(KeywordTag, exclude=DEFAULT_FIELDS)

class RockCarvingSerializer(DynamicDepthSerializer):

    class Meta:
        model = RockCarvingObject
        fields = ['id']+get_fields(RockCarvingObject, exclude=DEFAULT_FIELDS)

class AuthorSerializer(DynamicDepthSerializer):

    class Meta:
        model = Author
        fields = ['id']+get_fields(Author, exclude=DEFAULT_FIELDS)

class InstitutionSerializer(DynamicDepthSerializer):

    class Meta:
        model = Institution
        fields = ['id']+get_fields(Institution, exclude=DEFAULT_FIELDS)

class DatingTagSerializer(DynamicDepthSerializer):

    class Meta:
        model = DatingTag
        fields = ['id']+get_fields(DatingTag, exclude=DEFAULT_FIELDS)
