from diana.abstract.serializers import DynamicDepthSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from . import models
from diana.utils import get_fields, DEFAULT_FIELDS
from .models import *
from rest_framework import serializers


class TIFFImageSerializer(DynamicDepthSerializer):

    class Meta:
        model = Image
        fields = ['id']+get_fields(Image, exclude=['created_at', 'updated_at'])

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


class CompilationSerializer(DynamicDepthSerializer):

    class Meta:
        model = Compilation
        fields = ['id']+get_fields(Compilation, exclude=DEFAULT_FIELDS)


class ImageTypeSerializer(DynamicDepthSerializer):

    class Meta:
        model = ImageTypeTag
        fields = ['id']+get_fields(ImageTypeTag, exclude=DEFAULT_FIELDS)+['creators', 'keywords', 'datings']

class SHFA3DMeshSerializer(DynamicDepthSerializer):

    class Meta:
        model = SHFA3DMesh
        fields = ['id']+get_fields(SHFA3DMesh, exclude=DEFAULT_FIELDS+['dimensions'])



class PeopleSerializer(DynamicDepthSerializer):

    class Meta:
        model = People
        fields = ['id']+get_fields(People, exclude=DEFAULT_FIELDS)

class KeywordSerializer(DynamicDepthSerializer):
    class Meta:
        model = KeywordTag
        fields = ['id']+get_fields(KeywordTag, exclude=DEFAULT_FIELDS)

class DatingSerializer(DynamicDepthSerializer):
    class Meta:
        model = DatingTag
        fields = ['id']+get_fields(DatingTag, exclude=DEFAULT_FIELDS)
    

class CreatorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = People
        fields = ['id']+get_fields(People, exclude=DEFAULT_FIELDS)


class SHFA3DSerializer(DynamicDepthSerializer):

    class Meta:
        model = SHFA3D
        fields = '__all__'  # Include all fields in the SHFA3D model


class VisualizationGroupSerializer(DynamicDepthSerializer):
    visualization_group_count = serializers.IntegerField() 
    shfa_3d_data = SHFA3DSerializer(many=True, read_only=False, source='shfa3d_set')

    class Meta:
        model = Group
        fields =['id', 'text', 'visualization_group_count', 'shfa_3d_data']
        
class GeologySerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Geology
        fields = ['id']+get_fields(Geology, exclude=DEFAULT_FIELDS)
        geo_field = 'coordinates'

