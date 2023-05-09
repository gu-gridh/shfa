from unittest.mock import DEFAULT
from rest_framework import viewsets
from . import models, serializers
from django.db.models import Q
from diana.abstract.views import DynamicDepthViewSet, GeoViewSet
from diana.abstract.models import get_fields, DEFAULT_FIELDS

class IIIFImageViewSet(DynamicDepthViewSet):
    """
    retrieve:
    Returns a single image instance.

    list:
    Returns a list of all the existing images in the database, paginated.

    count:
    Returns a count of the existing images after the application of any filter.
    """
    
    queryset = models.Image.objects.all()
    serializer_class = serializers.TIFFImageSerializer
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

class SiteGeoViewSet(GeoViewSet):

    # queryset = models.Site.objects.all()

    images = models.Image.objects.all()
    queryset = models.Site.objects.filter(id__in=list(images.values_list('site', flat=True)))
    serializer_class = serializers.SiteGeoSerializer
    filterset_fields = get_fields(models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True

    
class SiteSearchViewSet(GeoViewSet):
    
    def get_queryset(self):

        q = self.request.GET["q"]
        images = models.Image.objects.all()
        queryset = models.Site.objects.filter(Q(raa_id__contains=q) and Q (id__in=list(images.values_list('site', flat=True))))
        return queryset
    
    serializer_class = serializers.SiteGeoSerializer
    filterset_fields = get_fields(models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True


class SearchKeywords(DynamicDepthViewSet):
    serializer_class = serializers.KeywordsSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.KeywordTag.objects.filter(text__contains=q)
        return queryset
    
class SearchRockCarving(DynamicDepthViewSet):
    serializer_class = serializers.RockCarvingSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.RockCarvingObject.objects.filter(name__contains=q)
        return queryset
    
class SearchInstitution(DynamicDepthViewSet):
    serializer_class = serializers.InstitutionSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.Institution.objects.filter(name__contains=q)
        return queryset
    
class SearchDatinTag(DynamicDepthViewSet):
    serializer_class = serializers.DatingTagSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.DatingTag.objects.filter(text__contains=q)
        return queryset
    
# # Add general search query
# class SearchGeneral(DynamicDepthViewSet):
#     def get_queryset(self):
#         q = self.request.GET["q"]
#         images = models.Image.objects.all()
#         queryset = models.Site.objects.filter(Q(raa_id__contains=q) and Q(id__in=list(images.values_list('site', flat=True))))
#         #                                       | Q(models.KeywordTag.objects.filter(text__contains=q))
#         #                                       | Q(models.RockCarvingObject.objects.filter(name__contains=q))
#         #                                       | Q(models.Institution.objects.filter(name__contains=q))
#         #                                       | Q(models.DatingTag.objects.filter(text__contains=q))
#         #                                       | Q(models.Image.objects.filter(type__in=q)))
#         return queryset
    
# Add mixed search option