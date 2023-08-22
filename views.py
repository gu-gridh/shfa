from unittest.mock import DEFAULT
from rest_framework import viewsets
from . import models, serializers
from django.db.models import Q, Count
from diana.abstract.views import DynamicDepthViewSet, GeoViewSet
from diana.abstract.models import get_fields, DEFAULT_FIELDS
from functools import reduce
import operator

class IIIFImageViewSet(DynamicDepthViewSet):
    """
    retrieve:
    Returns a single image instance.

    list:
    Returns a list of all the existing images in the database, paginated.

    count:
    Returns a count of the existing images after the application of any filter.
    """
    serializer_class = serializers.TIFFImageSerializer
    queryset = models.Image.objects.all().order_by('type__order')
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])


class CompilationViewset(DynamicDepthViewSet):
    serializer_class = serializers.CompilationSerializer
    queryset = models.Compilation.objects.all()
    filterset_fields = ['id']+get_fields(models.Compilation, exclude=DEFAULT_FIELDS + ['images__iiif_file', 'images__file'])


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
    serializer_class = serializers.SiteGeoSerializer

    def get_queryset(self):

        q = self.request.GET["site_name"]
        images = models.Image.objects.all()
        queryset = models.Site.objects.filter(Q (raa_id__icontains=q) |
                                              Q(lamning_id__icontains=q)  &
                                              Q (id__in=list(images.values_list('site', flat=True))
                                                ))

        return queryset
    
    filterset_fields = get_fields(models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True


class SearchKeywords(DynamicDepthViewSet):
    serializer_class = serializers.KeywordsSerializer

    def get_queryset(self):
        q = self.request.GET["keyword"]
        queryset = models.KeywordTag.objects.filter(text__icontains=q)

        return queryset
    
class SearchRockCarving(DynamicDepthViewSet):
    serializer_class = serializers.RockCarvingSerializer

    def get_queryset(self):
        q = self.request.GET["carving_object"]
        queryset = models.RockCarvingObject.objects.filter(name__icontains=q)
        return queryset
    

class SearchAuthor(DynamicDepthViewSet):
    serializer_class = serializers.AuthorSerializer

    def get_queryset(self):
        q = self.request.GET["auhtor_name"]
        images = models.Image.objects.all()
        queryset = models.Author.objects.filter(Q(name__icontains=q) & 
                                                Q (id__in=list(images.values_list('author', flat=True))
                                                   ))
        return queryset
    
    
class SearchInstitution(DynamicDepthViewSet):
    serializer_class = serializers.InstitutionSerializer

    def get_queryset(self):
        q = self.request.GET["institution_name"]
        queryset = models.Institution.objects.filter(name__icontains=q)

        return queryset
    
class SearchDatinTag(DynamicDepthViewSet):
    serializer_class = serializers.DatingTagSerializer

    def get_queryset(self):
        q = self.request.GET["dating_tag"]
        queryset = models.DatingTag.objects.filter(text__icontains=q)
        return queryset

class TypeSearchViewSet(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET["image_type"]
        queryset = models.Image.objects.filter(type__text__icontains=q)
        return queryset
    
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])
    
# Add general search query
class GeneralSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.Image.objects.filter( Q(dating_tags__text__icontains=q)
                                                |Q(author__name__icontains=q)
                                                |Q(type__text__icontains=q)
                                                |Q(site__raa_id__icontains=q)
                                                |Q(keywords__text__icontains=q)
                                                |Q(rock_carving_object__name__icontains=q)
                                                |Q(institution__name__icontains=q)
                                                ).order_by('type__order')

        return queryset
    
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

# Add mixed search option
class AdvancedSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):

        query_array = []
        if ("site_name" in self.request.GET):
            site_name = self.request.GET["site_name"]
            query_array.append(Q(site__raa_id__icontains=site_name) | Q (site__lamning_id__icontains=site_name))
            
        if ("keyword" in self.request.GET):
            keyword = self.request.GET["keyword"]
            keyword = keyword.split(',')
            if len(keyword) == 1:
                query_array.append(Q(keywords__text__icontains=keyword[0]))
            else:
                print(keyword)
                query_array.append(reduce(operator.and_, (Q(keywords__text__icontains=(i)) for i in keyword)))

        if ("author_name" in self.request.GET):
            author_name = self.request.GET["author_name"]
            author_name = author_name.split('and')

            if len(author_name) == 1 :
                query_array.append(Q(author__name__icontains=author_name[0]))
            else :
                query_array.append(reduce(operator.or_, (Q(author__name__icontains=i) for i in author_name)))

        if ("dating_tag" in self.request.GET):
            dating_tag = self.request.GET["dating_tag"]
            dating_tag = dating_tag.split('and')
            if len(dating_tag) == 1 :
                query_array.append(Q(dating_tags__text__icontains=dating_tag))
            else:
                query_array.append(reduce(operator.or_, (Q(dating_tags__text__icontains=i) for i in dating_tag)))

        if ("image_type" in self.request.GET):
            image_type = self.request.GET["image_type"]
            image_type = image_type.split('and')
            if len(image_type) == 1:
                query_array.append(Q(type__text__icontains=image_type))
            else:
                query_array.append(reduce(operator.or_, (Q(type__text__icontains=i) for i in image_type)))


        if ("institution_name" in self.request.GET):
            institution_name = self.request.GET["institution_name"]
            query_array.append(Q(institution__name__icontains=institution_name))

        if len(query_array)==0:
            pass # User has not provided a single field, throw error
        processed_query = reduce(operator.and_, (Q(i) for i in query_array))

        # processed_query = query_array[0]

        # for index in range(1, len(query_array)):
        #     processed_query = processed_query & query_array[index]

        print(processed_query)
        queryset = models.Image.objects.filter(processed_query).order_by('type__order')

        return queryset
    
    filterset_fields = ['id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])