from django.shortcuts import render
from . import models, serializers
from django.views.decorators.csrf import csrf_exempt

def get_records(params, request):    
    template = "../templates/bild.template.xml"
    if "metadataPrefix" in params:
        metadata_prefix = params.pop("metadataPrefix")
        if len(metadata_prefix) == 1:
            metadata_prefix = metadata_prefix[0]
            if "identifier" in params:
                identifier = params.pop("identifier")[-1]
                queryset = models.Image.objects.filter(id=identifier)
                site = models.Site.objects.filter(
                            id__in=list(queryset.values_list('site', flat=True)
                            ))
                type = models.ImageTypeTag.objects.filter(
                            id__in=list(queryset.values_list('type', flat=True)
                            ))
                rock_carving_object = models.RockCarvingObject.objects.filter(
                            id__in=list(queryset.values_list('rock_carving_object', flat=True)
                            ))
                institution = models.Institution.objects.filter(
                            id__in=list(queryset.values_list('institution', flat=True)
                ))
                collection = models.Collection.objects.filter(
                            id__in=list(queryset.values_list('collection', flat=True))
                )
                author = models.Author.objects.filter(
                            id__in=list(queryset.values_list('author', flat=True)
                ))
                municipality = models.geography.LocalAdministrativeUnit.objects.filter(
                            id__in=list(site.values_list('municipality', flat=True)
                ))
                data =  models.Image.objects.get(id=identifier)
                keywords = data.keywords.all()
    
    # data = queryset.values()[0]
    type = type.values()[0]
    site = site.values()[0]
    institution = institution.values()[0]
    rock_carving_object = rock_carving_object.values()[0]
    collection = collection.values()[0]
    author = author.values()[0]
    municipality = municipality.values()[0]

    xml_output = render(
        request,
        template,
        {'data': data,
         'type': type,
         'site': site,
         'rock_carving_object' : rock_carving_object,
         'institution': institution,
         'collection': collection,
         'coordinates': site['coordinates'][0:2],
         'author': author,
         'municipality': municipality,
         'keywords': keywords
         },
        content_type="text/xml",
    )
    return xml_output