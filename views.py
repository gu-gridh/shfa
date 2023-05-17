from unittest.mock import DEFAULT
from rest_framework import viewsets
from . import models, serializers
from django.db.models import Q, Prefetch
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

        q = self.request.GET["site_name"]
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
        q = self.request.GET["keyword"]
        queryset = models.KeywordTag.objects.filter(text__contains=q)
        return queryset
    
class SearchRockCarving(DynamicDepthViewSet):
    serializer_class = serializers.RockCarvingSerializer

    def get_queryset(self):
        q = self.request.GET["carving_tag"]
        queryset = models.RockCarvingObject.objects.filter(name__contains=q)
        return queryset
    
class SearchInstitution(DynamicDepthViewSet):
    serializer_class = serializers.InstitutionSerializer

    def get_queryset(self):
        q = self.request.GET["institution_name"]
        queryset = models.Institution.objects.filter(name__contains=q)
        return queryset
    
class SearchDatinTag(DynamicDepthViewSet):
    serializer_class = serializers.DatingTagSerializer

    def get_queryset(self):
        q = self.request.GET["dating_tag"]
        queryset = models.DatingTag.objects.filter(text__contains=q)
        return queryset

class TypeSearchViewSet(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.Image.objects.filter(type__text__contains=q)
        return queryset
    
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])
    
# Add general search query
class GeneralSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.Image.objects.filter( Q(carving_tags__text__in=q)
                                               |Q(type__text__contains=q)
                                               |Q(site__raa_id__contains=q)
                                               |Q(keywords__text__contains=q)
                                               |Q(dating_tags__text__contains=q)
                                               |Q(institution__name__contains=q))
        return queryset
    
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

# Add mixed search option
class AdvancedSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        site_name = self.request.GET["site_name"]
        keyword = self.request.GET["keyword"]
        carving_tag = self.request.GET["carving_tag"]
        dating_tag = self.request.GET["dating_tag"]
        type = self.request.GET["type"]
        institution_name = self.request.GET["institution_name"]

        ##########################################
        query_array = []
        if site_name is not None and site_name != "":
            query_array.append(Q(site__raa_id__contains=site_name))
        if keyword is not None and keyword != "":
            query_array.append(Q(keywords__text__contains=keyword))
        if carving_tag is not None and carving_tag != "":
            query_array.append(Q(carving_tags__text__in=carving_tag))
        if dating_tag is not None and dating_tag != "":
            query_array.append(Q(dating_tags__text__contains=dating_tag))
        if type is not None and type != "":
            query_array.append(Q(type__text__contains=type))
        if institution_name is not None and institution_name != "":
            query_array.append(Q(institution__name__contains=institution_name))
        if len(query_array)==0:
            pass # User has not provided a single field, throw error
        processed_query = query_array[0]
        for index in range(1, len(query_array)):
            processed_query = processed_query & query_array[index]
        queryset = models.Image.objects.filter(processed_query)
        ##########################################


        # queryset = models.Image.objects.filter( 
        #                                         Q(carving_tags__text__in=carving_tag)
        #                                        |Q(type__text__contains=type)
        #                                        |Q(site__raa_id__contains=site_name)
        #                                        |Q(keywords__text__contains=keyword)
        #                                        |Q(dating_tags__text__contains=dating_tag)
        #                                        |Q(institution__name__contains=institution_name)
        #                                        )
        return queryset
    
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])