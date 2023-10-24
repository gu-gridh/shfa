from django.shortcuts import render
from . import models, serializers
from django.views.decorators.csrf import csrf_exempt

def get_records(params, request):   
    template = "../templates/bild.template.xml"
    error_output = None
    if "metadataPrefix" in params:
        metadata_prefix = params.pop("metadataPrefix")
        if len(metadata_prefix) == 1:
            metadata_prefix = metadata_prefix[0]
            if "identifier" in params:
                identifier = params.pop("identifier")[-1]
                try:
                    queryset = models.Image.objects.filter(id=identifier)
                    output = get_image_values(request, queryset, identifier, template)
                except models.Image.DoesNotExist:                  
                    error_output = generate_error(request, "idDoesNotExist", identifier)
            else:
                error_output = generate_error(request, "badArgument", "identifier")
        else:
                    
            error_output = generate_error(request, "badArgument_single", ";".join(metadata_prefix))     
            metadata_prefix = None
    else:
        error_output = generate_error(request, "badArgument", "metadataPrefix")

    template_output = output if not error_output else error_output
    return template_output


def get_image_values(request, query, identifier, template):
    site = models.Site.objects.filter(
                id__in=list(query.values_list('site', flat=True)
                ))
    type = models.ImageTypeTag.objects.filter(
                id__in=list(query.values_list('type', flat=True)
                ))
    rock_carving_object = models.RockCarvingObject.objects.filter(
                id__in=list(query.values_list('rock_carving_object', flat=True)
                ))
    institution = models.Institution.objects.filter(
                id__in=list(query.values_list('institution', flat=True)
    ))
    collection = models.Collection.objects.filter(
                id__in=list(query.values_list('collection', flat=True))
    )
    author = models.Author.objects.filter(
                id__in=list(query.values_list('author', flat=True)
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


def get_identify(request):
    template = "../templates/identify.xml"
    identify_output =  render(
        request,
        template_name=template, 
        # context= {
        #     'error':error_xml
        #     },
        content_type="text/xml")
    return identify_output

def generate_error(request, code, *args):
    template = "../templates/error.xml"
    error_xml = {}
    if code == "badArgument":
        error_xml = {
            "code": "badArgument",
            "msg": f'The required argument "{args[0]}" is missing in the request.',
        }
    elif code == "badArgument_granularity":
        error_xml = {
            "code": "badArgument",
            "msg": 'The granularity of the arguments "from" and "until" do not match.',
        }
    elif code == "badArgument_single":
        error_xml = {
            "code": "badArgument",
            "msg": "Only a single metadataPrefix argument is allowed, got "
            + f'"{args[0]}".',
        }
    elif code == "badArgument_valid":
        error_xml = {
            "code": "badArgument",
            "msg": f'The value "{args[0]}" of the argument "{args[1]}" is not valid.',
        }
    elif code == "badResumptionToken":
        error_xml = {
            "code": "badResumptionToken",
            "msg": f'The resumptionToken "{args[0]}" is invalid.',
        }
    elif code == "badResumptionToken_expired":
        error_xml = {
            "code": "badResumptionToken",
            "msg": f'The resumptionToken "{args[0]}" is expired.',
        }
    elif code == "badVerb" and len(args) == 0:
        error_xml = {"code": "badVerb", "msg": "The request does not provide any verb."}
    elif code == "badVerb":
        error_xml = {
            "code": "badVerb",
            "msg": f'The verb "{args[0]}" provided in the request is illegal.',
        }
    elif code == "cannotDisseminateFormat":
        error_xml = {
            "code": "cannotDisseminateFormat",
            "msg": f'The value of the metadataPrefix argument "{args[0]}" is not '
            + " supported.",
        }
    elif code == "idDoesNotExist":
        error_xml = {
            "code": "idDoesNotExist",
            "msg": f'A record with the identifier "{args[0]}" does not exist.',
        }
    elif code == "noMetadataFormats" and len(args) == 0:
        error_xml = {
            "code": "noMetadataFormats",
            "msg": "There are no metadata formats available.",
        }
    elif code == "noMetadataFormats":
        error_xml = {
            "code": "noMetadataFormats",
            "msg": "There are no metadata formats available for the record with "
            + f'identifier "{args[0]}".',
        }
    elif code == "noRecordsMatch":
        error_xml = {
            "code": "noRecordsMatch",
            "msg": "The combination of the values of the from, until, and set "
            + "arguments results in an empty list.",
        }
    elif code == "noSetHierarchy":
        error_xml = {
            "code": "noSetHierarchy",
            "msg": "This repository does not support sets.",
        }

    error_output =  render(
        request,
        template, 
        context= {
            'error':error_xml
            },
        content_type="text/xml")
   
    return error_output