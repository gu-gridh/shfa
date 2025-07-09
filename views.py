from . import models, serializers
from django.db.models import Q, Count, Prefetch
from diana.abstract.views import DynamicDepthViewSet, GeoViewSet
from diana.abstract.models import get_fields, DEFAULT_FIELDS
from django.views.decorators.csrf import csrf_exempt
from .oai_cat import *
from django.contrib.gis.geos import Polygon
from django.contrib.gis.gdal.envelope import Envelope
from functools import reduce
from rest_framework import viewsets, status
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from collections import defaultdict
from diana.forms import ContactForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.gis.db.models import Extent
from django.db.models.query import QuerySet
# myapp/pagination.py
from rest_framework.pagination import PageNumberPagination

# Custom pagination class to allow dynamic page size
class CustomPageNumberPagination(PageNumberPagination):
    page_size = 25  # default limit if not provided
    page_size_query_param = 'limit'  # allows ?limit=50
    max_page_size = 100  # optional: prevent abuse


class SiteViewSet(DynamicDepthViewSet):
    serializer_class = serializers.SiteSerializer
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


class NullVisualizationGroupViewset(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer
    queryset = models.Image.objects.filter(
        group__isnull=False, published=True).order_by('type__order')
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
                Q(text__icontains=q) | Q(category__icontains=q)).distinct().order_by('text', 'category')
        else:
            queryset = models.KeywordTag.objects.filter(Q(english_translation__icontains=q) | Q(
                category_translation__icontains=q)).distinct().order_by('text', 'category')
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


class RegionSearchViewSet(DynamicDepthViewSet):
    serializer_class = serializers.SiteCoordinatesExcludeSerializer

    def get_queryset(self):
        q = self.request.GET["region_name"]
        # Search amoung parishes, municipalities and provinces names    
        queryset = models.Site.objects.filter(
            Q(parish__name__icontains=q) | Q(municipality__name__icontains=q) | Q(province__name__icontains=q)
        )
        return queryset
    filterset_fields = get_fields(
        models.Site, exclude=DEFAULT_FIELDS + ['coordinates'])

# Add general search query
class GeneralSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        if not q:
            return models.Image.objects.none()

        queryset = models.Image.objects.select_related(
            'site__parish', 'site__municipality', 'site__province', 'institution', 'type'
        ).prefetch_related(
            'dating_tags', 'people', 'keywords', 'rock_carving_object'
        ).filter(
            Q(dating_tags__text__icontains=q) |
            Q(dating_tags__english_translation__icontains=q) |
            Q(people__name__icontains=q) |
            Q(people__english_translation__icontains=q) |
            Q(type__text__icontains=q) |
            Q(type__english_translation__icontains=q) |
            Q(site__raa_id__icontains=q) |
            Q(site__lamning_id__icontains=q) |
            Q(site__askeladden_id__icontains=q) |
            Q(site__lokalitet_id__icontains=q) |
            Q(site__placename__icontains=q) |
            Q(keywords__text__icontains=q) |
            Q(keywords__english_translation__icontains=q) |
            Q(keywords__category__icontains=q) |
            Q(keywords__category_translation__icontains=q) |
            Q(rock_carving_object__name__icontains=q) |
            Q(institution__name__icontains=q) |
            Q(site__parish__name__icontains=q) |
            Q(site__municipality__name__icontains=q) |
            Q(site__province__name__icontains=q)
        ).filter(
            published=True
        ).distinct().order_by('-id', 'type__order')

        return queryset

    filterset_fields = ['id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])


class AdvancedSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        query_params = self.request.GET

        query_conditions = []

        # Define mapping between query params and model fields
        field_mapping = {
            "site_name": ["site__raa_id", "site__lamning_id", "site__askeladden_id",
                          "site__lokalitet_id", "site__placename", "site__ksamsok_id"],
            "keyword": ["keywords__text", "keywords__english_translation", "keywords__category", "keywords__category_translation"],
            "author_name": ["people__name", "people__english_translation"],
            "dating_tag": ["dating_tags__text", "dating_tags__english_translation"],
            "image_type": ["type__text", "type__english_translation"],
            "institution_name": ["institution__name"],
            "region_name": ["site__parish__name", "site__municipality__name", "site__province__name"],
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
            lambda x, y: x & y, query_conditions), published=True).order_by('-id', 'type__order')

        return queryset

    filterset_fields = [
        'id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

# Add gallery view
class GalleryViewSet(DynamicDepthViewSet):  

    """A viewset to return images in a gallery format with advanced search capabilities."""


    serializer_class = serializers.GallerySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return (
            models.Image.objects
            .filter(published=True)
            .select_related('type', 'institution', 'site__province')
            .prefetch_related('keywords', 'people')
            .defer('iiif_file', 'file')
            .order_by('type__order')
        )


    def list(self, request, *args, **kwargs):
        """Handles GET requests, returning paginated image results with summary by creator and institution."""

        params = request.GET
        search_type = request.GET.get("search_type")
        box = request.GET.get("in_bbox")
        site = request.GET.get("site")
        category_type = request.GET.get("category_type")
        # opertor = request.GET.get("operator")

        if not search_type and not box and not site and not category_type:
            return Response([])
        
        queryset = self.get_queryset()

        # Apply site filter
        if site:
            queryset = queryset.filter(site_id=site)

        # Apply bbox filter
        if box:
            box = list(map(float, box.strip().split(',')))
            bounding_box = Envelope(box)  # Assuming spatial filtering
            site_ids = models.Site.objects.filter(coordinates__intersects=bounding_box.wkt).values_list("id", flat=True)
            queryset = queryset.filter(site_id__in=site_ids)

        # Apply search types
        if search_type == "advanced":
            queryset = self.get_advanced_search_queryset()
        elif search_type == "general":
            queryset = self.get_general_search_queryset()
        else:
            queryset = self.filter_queryset(self.get_queryset())

        # Apply image type filter
        if category_type:
            queryset = queryset.filter(Q(type__text=category_type) |
                                       Q(type__english_translation=category_type))
        else:
            # Categorize images by type
            return Response({
                "results": self.categorize_by_type(queryset),
            })

        # Apply pagination and limit it bases on limit parameter

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            # Get bbox from current page only
            if isinstance(page, QuerySet):
                bbox = page.aggregate(Extent('site__coordinates'))['site__coordinates__extent']
            else:
                image_ids = [img.id for img in page]
                bbox = models.Image.objects.filter(id__in=image_ids).aggregate(
                    Extent('site__coordinates')
                )['site__coordinates__extent']

            paginated_response.data['bbox'] = [*bbox] if bbox else None
            return paginated_response


        # If pagination is disabled, return full results with summary
        serializer = self.get_serializer(queryset, many=True)


        return Response({
            "results": serializer.data,
        })

    def categorize_by_type(self, queryset):
        """Groups queryset results by `type__text` with counts and paginates images per type."""

        # Step 1: Group data by type with translation and count
        grouped_data = (
            queryset
            .values("type__id", "type__text", "type__english_translation")
            .annotate(img_count=Count("id", distinct=True))
            .order_by("type__id")
        )

        # Step 2: Prepare dictionary for categories
        category_dict = {
            entry["type__id"]: {
                "type": entry["type__text"],
                "type_translation": entry.get("type__english_translation", "Unknown"),
                "count": entry["img_count"],
                # "images": [],
            }
            for entry in grouped_data
        }
        return list(category_dict.values())

    def get_advanced_search_queryset(self):
        """Handles advanced search with query parameters."""
        params = self.request.GET
        operator = params.get("operator", "OR")
        query_conditions = []
        queryset = self.get_queryset()

        field_mapping = {
            "site_name": ["site__raa_id", "site__lamning_id", "site__askeladden_id",
                        "site__lokalitet_id", "site__placename", "site__ksamsok_id"],
            "author_name": ["people__name", "people__english_translation"],
            "dating_tag": ["dating_tags__text", "dating_tags__english_translation"],
            "image_type": ["type__text", "type__english_translation"],
            "institution_name": ["institution__name"],
            "region_name": ["site__parish__name", "site__municipality__name", "site__province__name"],
            "visualization_group": ["group__name"],
        }

        # Handle all fields including support for multi-value query params
        for param, fields in field_mapping.items():
            raw_values = self.parse_multi_values(params.getlist(param))

            values = []
            for val in raw_values:
                values.extend([v.strip() for v in val.split(",") if v.strip()])
            values = list(set(values))

            if values:
                field_condition = Q()
                for value in values:
                    or_conditions = [Q(**{f"{field}__icontains": value}) for field in fields]
                    field_condition |= reduce(lambda x, y: x | y, or_conditions)
                query_conditions.append(field_condition)

        # Handle keywords
        raw_keywords = self.parse_multi_values(params.getlist("keyword"))

        keywords = []
        for item in raw_keywords:
            keywords.extend([k.strip() for k in item.split(",") if k.strip()])
        keywords = list(set(keywords))

        if keywords:
            keyword_condition = Q()
            for keyword in keywords:
                keyword_condition |= (
                    Q(keywords__text__icontains=keyword) |
                    Q(keywords__english_translation__icontains=keyword)
                )
            query_conditions.append(keyword_condition)

        # Combine all conditions with correct operator
        if query_conditions:
            if operator == "AND":
                queryset = queryset.filter(reduce(lambda x, y: x & y, query_conditions))
            else:  # Default to OR
                queryset = queryset.filter(reduce(lambda x, y: x | y, query_conditions))

        return queryset.filter(published=True).distinct()

    def parse_multi_values(self, param_list):
        return list(set(v.strip() for val in param_list for v in val.split(",") if v.strip()))



    def get_general_search_queryset(self):
        """Handles general search with 'q' parameter."""
        q = self.request.GET.get("q", "")
        queryset = self.get_queryset()

        if not q:
            return self.queryset.none()

        return queryset.select_related(
            "institution", "type").prefetch_related(
            "dating_tags", "people", "keywords", "rock_carving_object"
            ).filter(
            Q(dating_tags__text__icontains=q)
            | Q(dating_tags__english_translation__icontains=q)
            | Q(people__name__icontains=q)
            | Q(people__english_translation__icontains=q)
            | Q(type__text__icontains=q)
            | Q(type__english_translation__icontains=q)
            | Q(site__raa_id__icontains=q)
            | Q(site__lamning_id__icontains=q)
            | Q(site__askeladden_id__icontains=q)
            | Q(site__lokalitet_id__icontains=q)
            | Q(site__placename__icontains=q)
            | Q(keywords__text__icontains=q)
            | Q(keywords__english_translation__icontains=q)
            | Q(keywords__category__icontains=q)
            | Q(keywords__category_translation__icontains=q)
            | Q(rock_carving_object__name__icontains=q)
            | Q(institution__name__icontains=q)
            | Q(site__parish__name__icontains=q)
            | Q(site__municipality__name__icontains=q)
            | Q(site__province__name__icontains=q)
        ).filter(published=True).distinct()


# Add autocomplete for general search from rest_framework.viewsets import ViewSet
class GeneralSearchAutocomplete(ViewSet):
    """Return suggestions for search autocomplete with source info."""

    def list(self, request, *args, **kwargs):
        q = request.GET.get("q", "").strip().lower()
        if not q:
            return Response([])

        limit = 5
        suggestions = []

        def add_suggestions(filtered_qs, label):
            seen = set()
            for row in filtered_qs:
                for val in row if isinstance(row, (tuple, list)) else [row]:
                    if val:
                        val_str = str(val).strip()
                        if q in val_str.lower() and val_str.lower() not in seen:
                            suggestions.append({"value": val_str, "source": label})
                            seen.add(val_str.lower())

        # Keywords
        keywords_filtered = models.Image.objects.filter(
            Q(keywords__text__icontains=q) |
            Q(keywords__english_translation__icontains=q) |
            Q(keywords__category__icontains=q) |
            Q(keywords__category_translation__icontains=q)
        ).values_list(
            "keywords__text", "keywords__english_translation",
            "keywords__category", "keywords__category_translation"
        ).distinct()[:limit]

        add_suggestions(keywords_filtered, "keywords")

        # People
        people_filtered = models.Image.objects.filter(
            Q(people__name__icontains=q) |
            Q(people__english_translation__icontains=q)
        ).values_list("people__name", "people__english_translation").distinct()[:limit]

        add_suggestions(people_filtered, "people")

        # Site
        site_filtered = models.Image.objects.filter(
            Q(site__placename__icontains=q) |
            Q(site__raa_id__icontains=q) 
            # Q(site__lamning_id__icontains=q) |
            # Q(site__askeladden_id__icontains=q) |
            # Q(site__lokalitet_id__icontains=q) |
            # Q(site__ksamsok_id__icontains=q)
        # ).values_list(
        #     "site__placename", "site__raa_id", "site__lamning_id",
        #     "site__askeladden_id", "site__lokalitet_id", "site__ksamsok_id"
        # ).distinct()[:limit]
        ).values_list(
            "site__placename", "site__raa_id"
        ).distinct()[:limit]

        add_suggestions(site_filtered, "site")

        # Type
        type_filtered = models.Image.objects.filter(
            Q(type__text__icontains=q) |
            Q(type__english_translation__icontains=q)
        ).values_list("type__text", "type__english_translation").distinct()[:limit]

        add_suggestions(type_filtered, "type")

        # Institution
        institution_filtered = models.Image.objects.filter(
            institution__name__icontains=q
        ).values_list("institution__name", flat=True).distinct()[:limit]

        add_suggestions(institution_filtered, "institution")

        # Dating Tags
        tags_filtered = models.Image.objects.filter(
            Q(dating_tags__text__icontains=q) |
            Q(dating_tags__english_translation__icontains=q)
        ).values_list("dating_tags__text", "dating_tags__english_translation").distinct()[:limit]

        add_suggestions(tags_filtered, "dating tag")

        # Rock Carving
        rc_filtered = models.Image.objects.filter(
            rock_carving_object__name__icontains=q
        ).values_list("rock_carving_object__name", flat=True).distinct()[:limit]

        add_suggestions(rc_filtered, "rock carving")

        # Region
        region_filtered = models.Image.objects.filter(
            Q(site__parish__name__icontains=q) |
            Q(site__municipality__name__icontains=q) |
            Q(site__province__name__icontains=q)
        ).values_list(
            "site__parish__name", "site__municipality__name", "site__province__name"
        ).distinct()[:limit]

        add_suggestions(region_filtered, "region")

        # duplicate and sort
        unique_suggestions = {(s["value"], s["source"]) for s in suggestions}
        sorted_suggestions = sorted(
            [{"value": v, "source": s} for v, s in unique_suggestions],
            key=lambda x: x["value"]
        )[:20]

        return Response(sorted_suggestions)


class SummaryViewSet(DynamicDepthViewSet):
    """A separate viewset to return summary data for images grouped by creator and institution and etc."""
    queryset = models.Image.objects.filter(published=True).order_by('type__order')
    serializer_class = serializers.SummarySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

    def list(self, request, *args, **kwargs):
        """Handles GET requests, returning paginated image results with summary by creator and institution."""

        search_type = request.GET.get("search_type")
        box = request.GET.get("in_bbox")
        site = request.GET.get("site")

        queryset = self.queryset

        # Apply site filter
        if site:
            queryset = queryset.filter(site_id=site)

        # Apply bbox filter
        if box:
            box = list(map(float, box.strip().split(',')))
            bounding_box = Envelope(box)  # Assuming spatial filtering
            sites = models.Site.objects.filter(coordinates__intersects=bounding_box.wkt)
            queryset = queryset.filter(site_id__in=sites)

        # Apply search types
        elif search_type == "advanced":
            queryset = self.get_advanced_search_queryset()
        elif search_type == "general":
            queryset = self.get_general_search_queryset()
        else:
            queryset = self.filter_queryset(self.get_queryset())

        # Generate summary BEFORE pagination
        summary_data = self.summarize_results(queryset)
        
        return Response(summary_data)

    def summarize_results(self, queryset):
        """Summarizes search results by creator and institution."""
        # we should add Summarise search results by geographic data too: TODO
        # Summarise by ADM0, ADM1, ADM2, socken, kommun, landskap/län: TODO
        # motif: Two level summary with keyword categories and subcategories: Done
        # Count of documentation types by site: Done
        # Show number of images for each year: Done
        # Summarise search results by creator and institution : Done

        summary = {
            "creators": [],
            "institutions": [],
            "year": [],
            "types": [],
            "motifs": [],
            "geographic": [],
            "site": []
        }

        # Count images per creator
        creator_counts = (
            queryset
            .values("people__name")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )

        # Count images per institution
        institution_counts = (
            queryset
            .values("institution__name")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )
        # Count of documentation types by site
        type_counts = (
            queryset
            .values("type__text", "type__english_translation")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )
        # Summarise search results by motif type
        motif_counts = (
            queryset
            .values("keywords__text", "keywords__english_translation" ,"keywords__category_translation", "keywords__figurative")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )
        # Show number of images for each year 
        year_counts = (
            queryset
            .values("year")
            .annotate(count=Count("id", distinct=True))
            .order_by("year")
        )

        site_counts = (
            queryset
            .values("site__raa_id", "site__lamning_id", "site__askeladden_id",
                    "site__lokalitet_id", "site__placename", "site__ksamsok_id")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )

        # Gorgraphic summary can be a json object with counts for each level of geographic data
        # ADM0, ADM1, ADM2, socken, kommun, landskap/län
    
        geographic_counts = (
            queryset
            .values("site__municipality__name", "site__parish__name", "site__province__name", 
                    "site__province__country__name", "site__municipality__superregion__superregion__superregion__superregion__name")
            .annotate(count=Count("id", distinct=True))
            .order_by("-count")
        )

        # Format summary
        summary["creators"] = [
            {"creator": entry["people__name"], "count": entry["count"]}
            for entry in creator_counts if entry["people__name"]
        ]

        summary["site"] = [
            {
                "raa_id": entry.get("site__raa_id"),
                "lamning_id": entry.get("site__lamning_id"),
                "askeladden_id": entry.get("site__askeladden_id"),
                "lokalitet_id": entry.get("site__lokalitet_id"),
                "placename": entry.get("site__placename"),
                "ksamsok_id": entry.get("site__ksamsok_id"),
                "count": entry["count"]
            }
            for entry in site_counts
            if any([
                entry.get("site__raa_id"),
                entry.get("site__lamning_id"),
                entry.get("site__askeladden_id"),
                entry.get("site__lokalitet_id"),
                entry.get("site__placename"),
                entry.get("site__ksamsok_id")
            ])
        ]

        summary["institutions"] = [
            {"institution": entry["institution__name"], "count": entry["count"]}
            for entry in institution_counts if entry["institution__name"]
        ]   

        summary["types"] = [
            {
                "type": entry["type__text"],
                "translation": entry.get("type__english_translation"),
                "count": entry["count"]
            }
            for entry in type_counts if entry["type__text"]
        ]
        
        summary["motifs"] = [
            {
                "motif": entry["keywords__text"],
                "translation": entry.get("keywords__english_translation"),
                "count": entry["count"]
            }
            for entry in motif_counts
            if "figure" in (entry.get("keywords__category_translation") or "").lower()
        ] + [
            {
                "figurative motif": entry["keywords__text"],
                "translation": entry.get("keywords__english_translation"),
                "count": entry["count"]
            }
            for entry in motif_counts
            if entry.get("keywords__figurative") is True
        ]

        summary["year"] = [
            {"year": entry["year"], "count": entry["count"]}
            for entry in year_counts if entry["year"]
        ]

        # Geographic summary 
        summary["province"] = [
            {
                "province": entry["site__province__name"],
                "country": entry["site__province__country__name"],
                "count": entry["count"]
            }
            for entry in geographic_counts if entry["site__province__name"]
        ]

        summary["municipality"] = [
            {
                "municipality": entry["site__municipality__name"],
                "country": entry["site__province__country__name"] or entry["site__municipality__superregion__superregion__superregion__superregion__name"],
                "count": entry["count"]
            } 
            for entry in geographic_counts if entry["site__municipality__name"]
        ]

        summary["parish"] = [
            {
                "parish": entry["site__parish__name"],
                "province": entry["site__province__name"],
                "country": entry["site__province__country__name"],
                "count": entry["count"]
            }
            for entry in geographic_counts if entry["site__parish__name"]
        ]
        
        summary["geographic"] = [
            {
                "municipality": entry["site__municipality__name"], 
                "parish": entry["site__parish__name"], 
                "province": entry["site__province__name"], 
                "country": entry["site__province__country__name"] or entry["site__municipality__superregion__superregion__superregion__superregion__name"],
                "count": entry["count"]
            }
            for entry in geographic_counts
        ]

        return summary


    def get_advanced_search_queryset(self):
        """Handles advanced search with query parameters."""
        query_params = self.request.GET
        query_conditions = []

        field_mapping = {
            "site_name": ["site__raa_id", "site__lamning_id", "site__askeladden_id",
                          "site__lokalitet_id", "site__placename", "site__ksamsok_id"],
            "keyword": ["keywords__text", "keywords__english_translation", "keywords__category", "keywords__category_translation"],
            "author_name": ["people__name", "people__english_translation"],
            "dating_tag": ["dating_tags__text", "dating_tags__english_translation"],
            "image_type": ["type__text", "type__english_translation"],
            "institution_name": ["institution__name"],
            "region_name": ["site__parish__name", "site__municipality__name", "site__province__name"],
        }

        for param, fields in field_mapping.items():
            if param in query_params:
                value = query_params[param]
                or_conditions = [Q(**{f"{field}__icontains": value}) for field in fields]
                query_conditions.append(reduce(lambda x, y: x | y, or_conditions))

        if not query_conditions:
            return self.queryset.none()

        return self.queryset.filter(reduce(lambda x, y: x & y, query_conditions), published=True).order_by('type__order')

    def get_general_search_queryset(self):
        """Handles general search with 'q' parameter."""
        q = self.request.GET.get("q", "")

        if not q:
            return self.queryset.none()

        return self.queryset.filter(
            Q(dating_tags__text__icontains=q)
            | Q(dating_tags__english_translation__icontains=q)
            | Q(people__name__icontains=q)
            | Q(people__english_translation__icontains=q)
            | Q(type__text__icontains=q)
            | Q(type__english_translation__icontains=q)
            | Q(site__raa_id__icontains=q)
            | Q(site__lamning_id__icontains=q)
            | Q(site__askeladden_id__icontains=q)
            | Q(site__lokalitet_id__icontains=q)
            | Q(site__placename__icontains=q)
            | Q(keywords__text__icontains=q)
            | Q(keywords__english_translation__icontains=q)
            | Q(keywords__category__icontains=q)
            | Q(keywords__category_translation__icontains=q)
            | Q(rock_carving_object__name__icontains=q)
            | Q(institution__name__icontains=q)
            | Q(site__parish__name__icontains=q)
            | Q(site__municipality__name__icontains=q)
            | Q(site__province__name__icontains=q)
        ).filter(published=True).order_by('-id', 'type__order').distinct()

    
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
        elif verb == "ListSets":
            output = get_list_set(request, params)
        else:
            output = verb_error(request)

    return output


# Add contact form view
class ContactFormViewSet(viewsets.ViewSet):
    def create(self, request):
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                # Process the form data
                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                subject = form.cleaned_data['subject']
                message = form.cleaned_data['message']
                
                # Send an email
                send_mail(
                    f'From {name}, Subject: {subject}',
                    f'Message: {message}\n',
                    email,  # From email
                    [settings.EMAIL_HOST_USER],  # To email
                    fail_silently=False,
                )
            return Response({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)
        else:
            form = ContactForm()
        return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
