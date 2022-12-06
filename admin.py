from django.contrib.gis.db import models
from .models import *
from django.utils.html import format_html
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _
from diana.utils import get_fields, DEFAULT_FIELDS, DEFAULT_EXCLUDE
from admin_auto_filters.filters import AutocompleteFilter
from rangefilter.filters import NumericRangeFilter
from django.contrib.admin import EmptyFieldListFilter
from django.conf import settings

class SiteFilter(AutocompleteFilter):
    title = _('Site') # display title
    field_name = 'site' # name of the foreign key field

class InstitutionFilter(AutocompleteFilter):
    title = _('Institution') # display title
    field_name = 'institution' # name of the foreign key field

class CollectionFilter(AutocompleteFilter):
    title = _('Collection') # display title
    field_name = 'collection' # name of the foreign key field

class AuthorFilter(AutocompleteFilter):
    title = _('Creator') # display title
    field_name = 'author' # name of the foreign key field




@admin.register(Image)
class ImageModel(admin.ModelAdmin):

    fields              = ['image_preview', *get_fields(Image, exclude=['id'])]
    readonly_fields     = ['legacy_id', 'iiif_file', 'uuid', 'image_preview', *DEFAULT_FIELDS]
    autocomplete_fields = ['site', 'collection', 'author', 'institution', 
                            'type', 'keywords', 'carving_tags', 'rock_carving_object', 
                            'dating_tags']
    list_display        = ['thumbnail_preview', 'site', 'rock_carving_object', 
                            'year', 'collection', 'author', 'institution', 'type']
    search_fields       = ['site__lamning_id', 'site__raa_id', 'rock_carving_object__name', 
                            'site__municipality__name', 'site__parish__name']
    list_filter         = [
        ('year', NumericRangeFilter), 
        ('site', EmptyFieldListFilter), 
        'type', 
        InstitutionFilter,
        CollectionFilter,
        AuthorFilter,
        SiteFilter]
    list_per_page = 10

    def image_preview(self, obj):
        return format_html(f'<img src="{settings.ORIGINAL_URL}/{obj.file}" height="300" />')

    def thumbnail_preview(self, obj):
        return format_html(f'<img src="{settings.ORIGINAL_URL}/{obj.file}" height="100" />')

    # image_preview.short_description = 'Image preview'
    # image_preview.allow_tags = True
    # thumbnail_preview.short_description = 'Image thumbnail'
    # thumbnail_preview.allow_tags = True

@admin.register(Site)
class SiteAdmin(admin.GISModelAdmin):
    fields = get_fields(Site, exclude=DEFAULT_EXCLUDE+["id"])
    readonly_fields = [*DEFAULT_FIELDS]
    list_display = ['raa_id', 'lamning_id', 'askeladden_id', 'get_ksamsok_link']
    search_fields = ['lamning_id', 'raa_id']

    @admin.display(description=_('Read at Fornsök'))
    def get_ksamsok_link(self, obj):
        
        return format_html("<a href='{url}' target='_blank' rel='noopener noreferrer'>{ksamsok_id}</a>", 
                            url="https://kulturarvsdata.se/raa/lamning/" + obj.ksamsok_id,
                            ksamsok_id=obj.ksamsok_id)


@admin.register(Compilation)
class CompilationAdmin(admin.ModelAdmin):

    list_display = ["name"]
    search_fields = ["name"]
    autocomplete_fields = ["images"]

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["name"]
    search_fields = ["name"]

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["name"]
    search_fields = ["name"]

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["name", "address", "url", "email"]
    search_fields = ["name"]

@admin.register(ImageTypeTag)
class ImageTypeTagAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["text"]
    search_fields = ["text"]

@admin.register(RockCarvingObject)
class RockCarvingObjectAdmin(admin.ModelAdmin):

    list_display = ["name", "code"]
    search_fields = ["name"]

@admin.register(KeywordTag)
class KeywordTagAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["text"]
    search_fields = ["text"]

@admin.register(DatingTag)
class DatingTagAdmin(admin.ModelAdmin):

    readonly_fields = ['legacy_id']
    list_display = ["text"]
    search_fields = ["text"]

@admin.register(CarvingTag)
class CarvingTagAdmin(admin.ModelAdmin):

    list_display = ["text"]
    search_fields = ["text"]