from django.shortcuts import render
from . import models
from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage
import xml.etree.ElementTree as ET
from django.http import HttpResponse

NUM_PER_PAGE = 1


def get_records(params, request):   
    template = "../templates/bild.template.xml"
    error_output = None
    output = None
    if "metadataPrefix" in params:
        metadata_prefix = params.pop("metadataPrefix")
        if len(metadata_prefix) == 1:
            metadata_prefix = metadata_prefix[0]
            if not models.MetadataFormat.objects.filter(
                prefix=metadata_prefix
            ).exists():
                error_output = generate_error(request, "cannotDisseminateFormat", metadata_prefix)
            if "identifier" in params:
                identifier = params.pop("identifier")[-1]
                try:
                    queryset = models.Image.objects.filter(id=identifier)
                    header_list = models.Header.objects.filter(identifier=identifier)
                    
                    if not header_list :
                        header_list = generate_header(identifier, metadata_prefix)

                    output = get_image_values(queryset, identifier)
                except models.Image.DoesNotExist:                  
                    error_output = generate_error(request, "idDoesNotExist", identifier)
            else:
                error_output = generate_error(request, "badArgument", "identifier")
        else:
                    
            error_output = generate_error(request, "badArgument_single", ";".join(metadata_prefix))     
            metadata_prefix = None
    else:
        error_output = generate_error(request, "badArgument", "metadataPrefix")

    # check_bad_arguments(request, params)
    template_output = template if not error_output else error_output
    
    xml_output = render(
        request,
        template_name=template_output,
        context=output,
        content_type="text/xml"
    )
    return xml_output


def get_image_values(query, identifier):
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

    output =   {'data': data,
                    'type': type,
                    'site': site,
                    'rock_carving_object' : rock_carving_object,
                    'institution': institution,
                    'collection': collection,
                    'coordinates': site['coordinates'][0:2],
                    'author': author,
                    'municipality': municipality,
                    'keywords': keywords
                }
           
    return output


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


def check_bad_arguments(request, params, msg=None):
    for k, v in params.copy().items():
        error = generate_error(
            request,
            {   
                "code": "badArgument",
                "msg": f'The argument "{k}" (value="{v}") included in the request is '
                + "not valid."
                + (f" {msg}" if msg else ""),
            }
        )
        params.pop(k)

def get_list_records(verb, request, params):
    template  = "../templates/listrecords.xml"
    errors_output = None

    if "resumptionToken" in params:
        header_list = models.Header.objects.all()
        image_list = models.Image.objects.all()
        # Generate resumptionToken
        (
            paginator,
            images,
            headers,
            resumption_token,
            metadata_prefix,
            from_timestamp,
            until_timestamp,
        ) =  _do_resumption_token(request, params, errors_output, header_list, image_list)

    elif "metadataPrefix" in params:
        metadata_prefix = params.pop("metadataPrefix")
        if len(metadata_prefix) == 1:
            metadata_prefix = metadata_prefix[0]
            if not models.MetadataFormat.objects.filter(
                prefix=metadata_prefix
            ).exists():
                errors_output = generate_error(request, "cannotDisseminateFormat", metadata_prefix)
            else:
                images = get_all_images_info(metadata_prefix)
                header_list = models.Header.objects.filter(
                            metadata_formats__prefix=metadata_prefix)

                from_timestamp, until_timestamp = check_timestamps(request, params)
                if from_timestamp:
                    header_list = header_list.filter(
                            timestamp__gte=from_timestamp)
                if until_timestamp:
                        header_list = header_list.filter(
                            timestamp__lte=until_timestamp)

                if header_list.count() == 0 :
                        errors = generate_error(request, "noRecordsMatch")
                else:
                    paginator = Paginator(header_list, NUM_PER_PAGE)
                    paginator_images = Paginator(images, NUM_PER_PAGE)
                    images = paginator_images.page(1)
                    headers = paginator.page(1)
        else:
                errors_output = generate_error(request, "badArgument_single", ";".join(metadata_prefix))
                metadata_prefix = None
    else:
                errors_output = generate_error(request, "badArgument", "metadataPrefix")
    
    xml_output = render(
        request,
        template if not errors_output else errors_output,
        context=
        {'images':images,
         'verb': verb,
         'headers':headers,
         'paginator': paginator,
         'metadata_prefix': metadata_prefix,
         'from_timestamp':from_timestamp,
         'until_timestamp':until_timestamp},
        content_type="text/xml",
    )
    return xml_output

def get_all_images_info(metadata_prefix):
    images = models.Image.objects.all()
    id_list = list(images.values_list('id', flat=True))
    tmp = []
    for id in id_list:
        image_xml_output = get_image_values(images, id)
        header_list = models.Header.objects.filter(
                identifier=id)
        if not header_list :
                    header_list = generate_header(id, metadata_prefix)
        tmp.append(image_xml_output)
    return tmp

def generate_header(identifier, metadata):
    id_identifier = models.Image.objects.get(id=identifier)
    id_metadata= models.MetadataFormat.objects.get(prefix=metadata)
    models.Header.objects.update_or_create(
        name=str(id_identifier.file.name),
        identifier=id_identifier.id,
        metadata_formats=id_metadata
    )
    return

def _do_resumption_token(request, params, errors, header_obj, image_objs):
    metadata_prefix = None
    from_timestamp = None
    until_timestamp = None
    resumption_token = None
    

    if "resumptionToken" in params:
        resumption_token = params.pop("resumptionToken")[-1]
        try:
            rt = models.ResumptionToken.objects.get(token=resumption_token)
            if timezone.now() > rt.expiration_date:
                errors = generate_error(request, "badResumptionToken_expired.", resumption_token)
            else:
                if rt.metadata_prefix:
                    objs = header_obj.filter(metadata_formats=rt.metadata_prefix)
                    metadata_prefix = rt.metadata_prefix.prefix
                if rt.from_timestamp:
                    objs = header_obj.filter(timestamp__gte=rt.from_timestamp)
                    from_timestamp = rt.from_timestamp
                if rt.until_timestamp:
                    objs = header_obj.filter(timestamp__gte=rt.until_timestamp)
                    until_timestamp = rt.until_timestamp

                image_objs = get_all_images_info(metadata_prefix)
                paginator = Paginator(objs, NUM_PER_PAGE)
                image_paginator = Paginator(image_objs, NUM_PER_PAGE)

                try:
                    page = paginator.page(rt.cursor / NUM_PER_PAGE + 1)
                    images = image_paginator.page(rt.cursor / NUM_PER_PAGE + 1)

                except EmptyPage:
                    errors = generate_error(request, "badResumptionToken", resumption_token)

        except models.ResumptionToken.DoesNotExist:
            paginator = Paginator(objs, NUM_PER_PAGE)
            image_objs = get_all_images_info('ksamsok-rdf')
            image_paginator = Paginator(image_objs, NUM_PER_PAGE)
            page = paginator.page(1)
            images = image_paginator.page(1)
            errors = generate_error(request, "badResumptionToken", resumption_token)

        # check_bad_arguments(
        #     params,
        #     errors,
        #     msg="The usage of resumptionToken allows no other arguments.",
        # )
    else:
            image_objs = get_all_images_info('ksamsok-rdf')
            paginator = Paginator(objs, NUM_PER_PAGE)
            image_paginator = Paginator(image_objs, NUM_PER_PAGE)
            page = paginator.page(1)
            images = image_paginator.page(1)

    return (
        paginator,
        images,
        page,
        resumption_token,
        metadata_prefix,
        from_timestamp,
        until_timestamp,
    )


def check_timestamps(request, params):
    from_timestamp = None
    until_timestamp = None

    granularity = None
    if "from" in params:
        f = params.pop("from")[-1]
        granularity = "%Y-%m-%dT%H:%M:%SZ %z" if "T" in f else "%Y-%m-%d %z"
        try:
            from_timestamp = datetime.strptime(f + " +0000", granularity)
        except Exception:
            errors = generate_error(request, "badArgument_valid", f, "from")

    if "until" in params:
        u = params.pop("until")[-1]
        ugranularity = "%Y-%m-%dT%H:%M:%SZ %z" if "T" in u else "%Y-%m-%d %z"
        if ugranularity == granularity or not granularity:
            try:
                until_timestamp = datetime.strptime(u + " +0000", granularity)
            except Exception:
                errors = generate_error(request, "badArgument_valid", u, "until")
        else:
            errors = generate_error(request,"badArgument_granularity")
    return from_timestamp, until_timestamp


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