from . import models, serializers
from django.db.models import Q, Count, Prefetch
from diana.abstract.views import DynamicDepthViewSet, GeoViewSet
from diana.abstract.models import get_fields, DEFAULT_FIELDS
from django.views.decorators.csrf import csrf_exempt
from .oai_cat import *
from django.contrib.gis.geos import Polygon
from django.contrib.gis.gdal.envelope import Envelope
from functools import reduce
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg


class SiteViewSet(DynamicDepthViewSet):
    serializer_class = serializers.SiteGeoSerializer
    queryset = models.Site.objects.all()

    filterset_fields = get_fields(
        models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True


class SiteGeoViewSet(GeoViewSet):

    serializer_class = serializers.SiteGeoSerializer
    images = models.Image.objects.all()
    queryset = models.Site.objects.filter(
        id__in=list(images.values_list('site', flat=True))
    ).order_by('raa_id', 'lamning_id', 'placename')

    filterset_fields = get_fields(
        models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True

# Add 3D views


class SHFA3DViewSet(DynamicDepthViewSet):
    serializer_class = serializers.SHFA3DSerializer
    tree_d_data_group = models.Group.objects.all()
    queryset = models.SHFA3D.objects.filter(
        group_id__in=list(tree_d_data_group.values_list('id', flat=True)))
    filterset_fields = get_fields(models.SHFA3D, exclude=DEFAULT_FIELDS)


class VisualizationGroupViewset(DynamicDepthViewSet):
    serializer_class = serializers.VisualizationGroupSerializer

    def get_queryset(self):
        shfa3d_prefetch = Prefetch(
            'shfa3d_set', queryset=models.SHFA3D.objects.all())
        images_prefetch = Prefetch(
            'images_set', queryset=models.Image.objects.all().order_by('subtype__order'))

        queryset = models.Group.objects.all().annotate(
            visualization_group_count=Count('shfa3d_set')
        ).prefetch_related(shfa3d_prefetch, images_prefetch)

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        depth = self.request.query_params.get('depth', 1)
        try:
            depth = int(depth)
        except ValueError:
            depth = 1
        context['depth'] = depth
        return context

    filterset_fields = get_fields(models.Group, exclude=DEFAULT_FIELDS)


class GeologyViewSet(GeoViewSet):
    serializer_class = serializers.GeologySerializer
    queryset = models.Geology.objects.all()
    filterset_fields = get_fields(
        models.Geology, exclude=DEFAULT_FIELDS + ['coordinates', ])


class SHFA3DMeshViewset(DynamicDepthViewSet):
    serializer_class = serializers.SHFA3DMeshSerializer
    queryset = models.SHFA3DMesh.objects.all()
    filterset_fields = get_fields(
        models.SHFA3DMesh, exclude=DEFAULT_FIELDS + ['dimensions'])


class CameraSpecificationViewSet(DynamicDepthViewSet):
    serializer_class = serializers.CameraSpecificationSerializer
    queryset = models.CameraMeta.objects.all()
    filterset_fields = get_fields(
        models.CameraMeta, exclude=DEFAULT_FIELDS)

  # Search views


class SiteSearchViewSet(GeoViewSet):
    serializer_class = serializers.SiteGeoSerializer

    def get_queryset(self):
        q = self.request.GET["site_name"]
        images = models.Image.objects.all()
        queryset = models.Site.objects.filter(Q
                                              (Q(raa_id__icontains=q)
                                               | Q(lamning_id__icontains=q)
                                               | Q(ksamsok_id__icontains=q)
                                               | Q(placename__icontains=q)
                                               | Q(askeladden_id__icontains=q)
                                               | Q(lokalitet_id__icontains=q)
                                               )
                                              & Q
                                              (id__in=list(images.values_list('site', flat=True)))
                                              ).order_by('raa_id', 'lamning_id', 'placename', 'ksamsok_id', 'askeladden_id', 'lokalitet_id')

        return queryset

    filterset_fields = get_fields(
        models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])
    search_fields = ['raa_id', 'lamning_id', 'ksamsok_id', 'placename']
    bbox_filter_field = 'coordinates'
    bbox_filter_include_overlapping = True


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
    queryset = models.Image.objects.filter(
        published=True).order_by('type__order')
    filterset_fields = [
        'id']+get_fields(models.Image, exclude=['created_at', 'updated_at'] + ['iiif_file', 'file'])


class SearchBoundingBoxImageViewSet(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        box = self.request.GET["in_bbox"]
        box = box.strip().split(',')
        bbox_coords = [
            float(box[0]), float(box[1]),
            float(box[2]), float(box[3]),
        ]
        bounding_box = Polygon.from_bbox((bbox_coords))
        bounding_box = Envelope((bbox_coords))
        sites = models.Site.objects.filter(
            coordinates__intersects=bounding_box.wkt)
        queryset = models.Image.objects.filter(Q(site_id__in=sites)
                                               & Q(published=True)).order_by('type__order')
        return queryset

    filterset_fields = [
        'id']+get_fields(models.Image, exclude=['created_at', 'updated_at'] + ['iiif_file', 'file'])


class CompilationViewset(DynamicDepthViewSet):
    serializer_class = serializers.CompilationSerializer
    queryset = models.Compilation.objects.all()
    filterset_fields = ['id']+get_fields(models.Compilation, exclude=DEFAULT_FIELDS + [
                                         'images__iiif_file', 'images__file'])


class SearchKeywords(DynamicDepthViewSet):
    serializer_class = serializers.KeywordsSerializer

    def get_queryset(self):
        q = self.request.GET["keyword"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.KeywordTag.objects.filter(
                text__icontains=q).order_by('text')
        else:
            queryset = models.KeywordTag.objects.filter(
                english_translation__icontains=q).order_by('text')

        return queryset


class SearchRockCarving(DynamicDepthViewSet):
    serializer_class = serializers.RockCarvingSerializer

    def get_queryset(self):
        q = self.request.GET["carving_object"]
        queryset = models.RockCarvingObject.objects.filter(
            name__icontains=q).order_by('name')
        return queryset


class SearchAuthor(DynamicDepthViewSet):
    serializer_class = serializers.AuthorSerializer

    def get_queryset(self):
        q = self.request.GET["auhtor_name"]
        images = models.Image.objects.all()
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.Author.objects.filter(Q(name__icontains=q) &
                                                    Q(id__in=list(images.values_list('author', flat=True))
                                                      )).order_by('name')
        else:
            queryset = models.Author.objects.filter(Q(english_translation__icontains=q) &
                                                    Q(id__in=list(images.values_list('author', flat=True))
                                                      )).order_by('name')
        return queryset


class SearchPeople(DynamicDepthViewSet):
    serializer_class = serializers.PeopleSerializer

    def get_queryset(self):
        q = self.request.GET["auhtor_name"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.People.objects.filter(
                name__icontains=q).order_by('name')
        else:
            queryset = models.People.objects.filter(
                english_translation__icontains=q).order_by('name')

        return queryset


class SearchInstitution(DynamicDepthViewSet):
    serializer_class = serializers.InstitutionSerializer

    def get_queryset(self):
        q = self.request.GET["institution_name"]
        queryset = models.Institution.objects.filter(
            name__icontains=q).order_by('name')
        return queryset


class SearchDatinTag(DynamicDepthViewSet):
    serializer_class = serializers.DatingTagSerializer

    def get_queryset(self):
        q = self.request.GET["dating_tag"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.DatingTag.objects.filter(
                text__icontains=q).order_by('text')
        else:
            queryset = models.DatingTag.objects.filter(
                english_translation__icontains=q).order_by('text')
        return queryset


class TypeSearchViewSet(DynamicDepthViewSet):
    serializer_class = serializers.ImageTypeSerializer

    def get_queryset(self):
        q = self.request.GET["image_type"]
        language = self.request.GET["language"]
        if language == "sv":
            queryset = models.ImageTypeTag.objects.filter(
                text__icontains=q).order_by('text')
        else:
            queryset = models.ImageTypeTag.objects.filter(
                english_translation__icontains=q).order_by('text')
        return queryset


# Add general search query
class GeneralSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.Image.objects.filter(Q(dating_tags__text__icontains=q)
                                               | Q(dating_tags__english_translation__icontains=q)
                                               | Q(author__name__icontains=q)
                                               | Q(author__english_translation__icontains=q)
                                               | Q(type__text__icontains=q)
                                               | Q(type__english_translation__icontains=q)
                                               | Q(site__raa_id__icontains=q)
                                               | Q(site__lamning_id__icontains=q)
                                               | Q(site__askeladden_id__icontains=q)
                                               | Q(site__lokalitet_id__icontains=q)
                                               | Q(site__placename__icontains=q)
                                               | Q(keywords__text__icontains=q)
                                               | Q(keywords__english_translation__icontains=q)
                                               | Q(rock_carving_object__name__icontains=q)
                                               | Q(institution__name__icontains=q)
                                               ).filter(published=True).distinct().order_by('type__order')
        return queryset

    filterset_fields = [
        'id']+get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])


class AdvancedSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        query_params = self.request.GET

        query_conditions = []

        # Define mapping between query params and model fields
        field_mapping = {
            "site_name": ["site__raa_id", "site__lamning_id", "site__askeladden_id",
                          "site__lokalitet_id", "site__placename", "site__ksamsok_id"],
            "keyword": ["keywords__text", "keywords__english_translation"],
            "author_name": ["author__name", "author__english_translation"],
            "dating_tag": ["dating_tags__text", "dating_tags__english_translation"],
            "image_type": ["type__text", "type__english_translation"],
            "institution_name": ["institution__name"]
        }

        for param, fields in field_mapping.items():
            if param in query_params:
                value = query_params[param]
                # Creating OR conditions for each field
                or_conditions = [Q(**{field + '__icontains': value})
                                 for field in fields]
                query_conditions.append(
                    reduce(lambda x, y: x | y, or_conditions))

        if not query_conditions:
            # Handle no query parameters provided
            # You might want to raise an error or return an empty queryset
            # For now, returning an empty queryset
            return models.Image.objects.none()

        queryset = models.Image.objects.filter(reduce(
            lambda x, y: x & y, query_conditions), published=True).order_by('type__order')

        return queryset

    filterset_fields = [
        'id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])


# VIEW FOR OAI_CAT

@csrf_exempt
def oai(request):
    params = request.POST.copy() if request.method == "POST" else request.GET.copy()
    verb = None

    if "verb" in params:
        verb = params.pop("verb")[-1]
        if verb == "GetRecord":
            output = get_records(params, request)
        elif verb == "Identify":
            output = get_identify(request)
        elif verb == "ListRecords":
            output = get_list_records(verb, request, params)
        elif verb == "ListMetadataFormats":
            output = get_list_metadata(request, params)
        else:
            output = verb_error(request)

    return output
