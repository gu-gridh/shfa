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
from rest_framework.response import Response
from collections import defaultdict
from diana.forms import ContactForm
from django.core.mail import send_mail
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Window
from django.db.models.functions import RowNumber

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


# Add general search query
class GeneralSearch(DynamicDepthViewSet):
    serializer_class = serializers.TIFFImageSerializer

    def get_queryset(self):
        q = self.request.GET["q"]
        queryset = models.Image.objects.filter(Q(dating_tags__text__icontains=q)
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
                                               ).filter(published=True).distinct().order_by('-id', 'type__order')
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
            "keyword": ["keywords__text", "keywords__english_translation", "keywords__category", "keywords__category_translation"],
            "author_name": ["people__name", "people__english_translation"],
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
            lambda x, y: x & y, query_conditions), published=True).order_by('-id', 'type__order')

        return queryset

    filterset_fields = [
        'id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

# Add gallery view
class GalleryViewSet(DynamicDepthViewSet):  

    queryset = models.Image.objects.filter(published=True).order_by('type__order')
    serializer_class = serializers.TIFFImageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id'] + get_fields(models.Image, exclude=DEFAULT_FIELDS + ['iiif_file', 'file'])

    def list(self, request, *args, **kwargs):
        """Handles the GET request for categorized image results."""
        search_type = request.GET.get("search_type")
        box = request.GET.get("in_bbox")  # Check for bbox filtering
        site = request.GET.get("site")

        # If no search_type and no filtering (like bbox), return an empty response
        if not search_type and not box and not site:
            return Response([])


        queryset = self.queryset

        # Handle site filtering if provided
        if site:
            queryset = queryset.filter(site_id=site)

        # Handle bbox filtering if provided
        if box:
            box = box.strip().split(',')
            bbox_coords = [
                float(box[0]), float(box[1]),
                float(box[2]), float(box[3]),
            ]
            bounding_box = Polygon.from_bbox((bbox_coords))
            bounding_box = Envelope((bbox_coords))
            sites = models.Site.objects.filter(
                coordinates__intersects=bounding_box.wkt)
            queryset = queryset.filter(site_id__in=sites)
                                                
        # Handle different search types
        elif search_type == "advanced":
            queryset = self.get_advanced_search_queryset()
        elif search_type == "general":
            queryset = self.get_general_search_queryset()
        else:
            queryset = self.filter_queryset(self.get_queryset())  # Apply default filters

        # Apply categorization if bbox or search_type is used
        if box or search_type or site:
            categorized_data = self.categorize_by_type(queryset)
            return Response(categorized_data)

        # Otherwise, return normal serialized data
        return Response(self.get_serializer(queryset, many=True).data)

    def categorize_by_type(self, queryset):
        """Groups queryset results by `type__text` with counts."""
        category_dict = defaultdict(lambda: {"count": 0, "images": []})

        for image in queryset:
            type_text = image.type.text if image.type else "Unknown"
            type_translation = image.type.english_translation if image.type else "Unknown"
            category_dict[type_text]["count"] += 1
            category_dict[type_text]["images"].append(serializers.TIFFImageSerializer(image).data)

        return [{"type": type_text,
                 "type_translation": type_translation, 
                 "count": data["count"], 
                 "images": data["images"]}

                for type_text, data in category_dict.items()]

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
            "institution_name": ["institution__name"]
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
            return render(request, 'contact.html', {'form': form})
