from diana.abstract.serializers import DynamicDepthSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from diana.utils import get_fields, DEFAULT_FIELDS
from .models import *
from rest_framework import serializers
import requests
from django.conf import settings
from typing import Dict, List

class DynamicDepthModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if request:
            try:
                self.Meta.depth = int(request.query_params.get('depth', 0))  # Default 0
            except (ValueError, TypeError):
                self.Meta.depth = 0  
        else:
            self.Meta.depth = 0  

class SiteCoordinatesExcludeSerializer(GeoFeatureModelSerializer):
    parish = serializers.CharField(source='parish.name', default=None)
    municipality = serializers.CharField(source='municipality.name', default=None)
    province = serializers.CharField(source='province.name', default=None)

    class Meta:
        model = Site
        fields = ['id'] + get_fields(Site, exclude=['coordinates'])
        geo_field = 'coordinates'
        depth = 0  # Set a default depth for related objects

class TIFFImageSerializer(DynamicDepthSerializer):
    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()

    def get_width(self, obj):
        info = self.get_iiif_info(obj)
        return info.get("width")

    def get_height(self, obj):
        info = self.get_iiif_info(obj)
        return info.get("height")

    def get_iiif_info(self, obj):

        base_url = "https://img.dh.gu.se/diana/static/"
        if not obj.iiif_file:
            return {}
        # Convert to URL string
        iiif_file_url = getattr(obj.iiif_file, 'url', None)
        if not iiif_file_url:
            return {}

        # Fix relative paths
        if not iiif_file_url.startswith("http"):
            iiif_file_url = base_url + iiif_file_url.lstrip("/")

        info_url = f"{iiif_file_url}/info.json"

        response = requests.get(info_url, timeout=3)
        if response.status_code == 200:
            return response.json()

        return {}
    class Meta:
        model = Image
        fields = ['id', 'width', 'height'] + get_fields(Image, exclude=['created_at', 'updated_at'])
class SummarySerializer(DynamicDepthSerializer):

    class Meta:
        model = Image
        fields = ['id']+get_fields(Image, exclude=['created_at', 'updated_at', 'iiif_file', 'file', 'uuid'])

class SiteSerializer(DynamicDepthSerializer):
    # parish = serializers.CharField(source='parish.name', default=None)
    # municipality = serializers.CharField(source='municipality.name', default=None)
    # province = serializers.CharField(source='province.name', default=None)
    class Meta:
        model = Site
        fields = ['id']+get_fields(Site, exclude=DEFAULT_FIELDS)

class SiteGeoSerializer(GeoFeatureModelSerializer):
    # parish = serializers.CharField(source='parish.name', default=None)
    # municipality = serializers.CharField(source='municipality.name', default=None)
    # province = serializers.CharField(source='province.name', default=None)
    
    class Meta:
        model = Site
        fields = ['id']+get_fields(Site, exclude=DEFAULT_FIELDS)
        geo_field = 'coordinates'

class KeywordsSerializer(DynamicDepthSerializer):

    class Meta:
        model = KeywordTag
        fields = ['id']+get_fields(KeywordTag, exclude=DEFAULT_FIELDS)

class RockCarvingSerializer(DynamicDepthSerializer):

    class Meta:
        model = RockCarvingObject
        fields = ['id']+get_fields(RockCarvingObject, exclude=DEFAULT_FIELDS)

class AuthorSerializer(DynamicDepthSerializer):

    class Meta:
        model = Author
        fields = ['id']+get_fields(Author, exclude=DEFAULT_FIELDS)

class InstitutionSerializer(DynamicDepthSerializer):

    class Meta:
        model = Institution
        fields = ['id']+get_fields(Institution, exclude=DEFAULT_FIELDS)

class DatingTagSerializer(DynamicDepthSerializer):

    class Meta:
        model = DatingTag
        fields = ['id']+get_fields(DatingTag, exclude=DEFAULT_FIELDS)


class CompilationSerializer(DynamicDepthSerializer):

    class Meta:
        model = Compilation
        fields = ['id']+get_fields(Compilation, exclude=DEFAULT_FIELDS)


class ImageTypeSerializer(DynamicDepthSerializer):

    class Meta:
        model = ImageTypeTag
        fields = ['id']+get_fields(ImageTypeTag, exclude=DEFAULT_FIELDS)

class SHFA3DMeshSerializer(DynamicDepthSerializer):

    class Meta:
        model = SHFA3DMesh
        fields = ['id']+get_fields(SHFA3DMesh, exclude=DEFAULT_FIELDS+['dimensions'])

class PeopleSerializer(DynamicDepthSerializer):

    class Meta:
        model = People
        fields = ['id']+get_fields(People, exclude=DEFAULT_FIELDS)

class KeywordSerializer(DynamicDepthSerializer):
    class Meta:
        model = KeywordTag
        fields = ['id']+get_fields(KeywordTag, exclude=DEFAULT_FIELDS)

class DatingSerializer(DynamicDepthSerializer):
    class Meta:
        model = DatingTag
        fields = ['id']+get_fields(DatingTag, exclude=DEFAULT_FIELDS)
    

class CreatorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = People
        fields = ['id']+get_fields(People, exclude=DEFAULT_FIELDS)
    
class GeologySerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Geology
        fields = ['id']+get_fields(Geology, exclude=DEFAULT_FIELDS)
        geo_field = 'coordinates'


class CameraLensSerializer(DynamicDepthSerializer):
    class Meta:
        model = CameraLens
        fields = ['id']+get_fields(CameraLens, exclude=DEFAULT_FIELDS)


class CamerModelSerializer(DynamicDepthSerializer):
    class Meta:
        model = CameraModel
        fields = ['id']+get_fields(CameraModel, exclude=DEFAULT_FIELDS)

class CameraSpecificationSerializer(DynamicDepthSerializer):
    mm35_equivalent = serializers.SerializerMethodField()
    camera_lens = CameraLensSerializer()
    camera_model = CamerModelSerializer()
    class Meta:
        model = CameraMeta
        fields = ['id']+get_fields(CameraMeta, exclude=DEFAULT_FIELDS)+['mm35_equivalent']

    
    def get_mm35_equivalent(self, obj):
        return obj.mm35_equivalent

class SiteSerializerExcludeCoordinates(serializers.ModelSerializer):
    class Meta:
        model = Site
        exclude = ['coordinates']  # Exclude the coordinates field

class SHFA3DSerializer(DynamicDepthSerializer):

    class Meta:
        model = SHFA3D
        fields = ['id']+get_fields(SHFA3D, exclude=DEFAULT_FIELDS)
        depth = 1  # Set a default depth for related objects

class SHFA3DSerializerExcludeCoordinates(DynamicDepthSerializer):
    site=SiteSerializerExcludeCoordinates()
    image = CameraSpecificationSerializer()
    class Meta:
        model = SHFA3D
        fields = ['id']+get_fields(SHFA3D, exclude=DEFAULT_FIELDS)+['image']

class TIFFImageExcludeSiteSerializer(DynamicDepthSerializer):

    class Meta:
        model = Image
        fields = ['id']+get_fields(Image, exclude=['created_at', 'updated_at', 'site'])

class VisualizationGroupSerializer(DynamicDepthSerializer):
    visualization_group_count = serializers.IntegerField()
    shfa_3d_data = SHFA3DSerializerExcludeCoordinates(many=True, read_only=True, source='shfa3d_set')
    colour_images = TIFFImageExcludeSiteSerializer(many=True, read_only=True, source='images_set')
    class Meta:
        model = Group
        fields = ['id', 'text', 'visualization_group_count', 'shfa_3d_data', 'colour_images']
        depth = 1  # Ensure a default depth is set

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        depth = self.context.get('depth', 1)
        if depth > 1:
            nested_data = []
            images_nested_data = [] 
            for shfa3d_instance in instance.shfa3d_set.all():
                nested_representation = SHFA3DSerializerExcludeCoordinates(shfa3d_instance, context={'depth': depth - 1}).data
                nested_data.append(nested_representation)
            representation['shfa_3d_data'] = nested_data
            for image_instance in instance.images_set.all():
                nested_representation = TIFFImageExcludeSiteSerializer(image_instance, context={'depth': depth - 1}).data
                images_nested_data.append(nested_representation)
            representation['colour_images'] = images_nested_data
        return representation


class GallerySerializer(DynamicDepthModelSerializer):
    site = SiteCoordinatesExcludeSerializer()


    def get_width(self, obj):
        return TIFFImageSerializer().get_width(obj)

    def get_height(self, obj):
        return TIFFImageSerializer().get_height(obj)

    class Meta:
        model = Image
        fields = ['id'] + get_fields(Image, exclude=DEFAULT_FIELDS)
        depth = 0
        geo_field = 'coordinates'


class IIIFManifestSerializer:
    """Generate IIIF Presentation API 3.0 compliant manifests for rock carving images."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'IIIF_BASE_URL', 'ORIGINAL_URL')
    
    def create_manifest_for_image(self, image) -> Dict:
        """Create a IIIF manifest for a single rock carving image."""
        if not image.iiif_file:
            raise ValueError("Image must have an IIIF file")
        
        # Build IIIF image URL
        iiif_file_url = getattr(image.iiif_file, 'url', None)
        if not iiif_file_url.startswith("http"):
            iiif_file_url = self.base_url.rstrip('/') + '/' + iiif_file_url.lstrip("/")
        
        # Use database fields directly - NO HTTP REQUESTS!
        width = image.width or 1000  # fallback if not set
        height = image.height or 800
        
        # Fix URL construction
        base_manifest_url = getattr(settings, 'SITE_URL')
        manifest_id = f"{base_manifest_url}/api/shfa/iiif/manifest/{image.id}"
        canvas_id = f"{manifest_id}/canvas/1"
        annotation_page_id = f"{canvas_id}/annotation-page/1"
        annotation_id = f"{annotation_page_id}/annotation/1"
        
        # Create meaningful titles and descriptions
        title = self._get_image_title(image)
        summary = self._get_summary(image)
        
        manifest = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": manifest_id,
            "type": "Manifest",
            "label": {
                "en": [title["en"]],
                "sv": [title["sv"]]
            },
            "metadata": self._build_metadata(image),
            "summary": {
                "en": [summary["en"]],
                "sv": [summary["sv"]]
            },
            "thumbnail": [
                {
                    "id": f"{iiif_file_url}/full/300,/0/default.jpg",
                    "type": "Image",
                    "format": "image/jpeg",
                    "width": 300,
                    "height": int(300 * height / width) if width > 0 else 300
                }
            ],
            "items": [
                {
                    "id": canvas_id,
                    "type": "Canvas",
                    "label": {
                        "en": [f"Canvas 1 - {title['en']}"],
                        "sv": [f"Canvas 1 - {title['sv']}"]
                    },
                    "width": width,
                    "height": height,
                    "items": [
                        {
                            "id": annotation_page_id,
                            "type": "AnnotationPage",
                            "items": [
                                {
                                    "id": annotation_id,
                                    "type": "Annotation",
                                    "motivation": "painting",
                                    "target": canvas_id,
                                    "body": {
                                        "id": f"{iiif_file_url}/full/max/0/default.jpg",
                                        "type": "Image",
                                        "format": "image/jpeg",
                                        "width": width,
                                        "height": height,
                                        "service": [
                                            {
                                                "id": iiif_file_url,
                                                "type": "ImageService3",
                                                "profile": "level1"
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ],
            # Enhanced provider information
            "provider": [
                {
                    "id": "https://diana.gu.se/api/shfa/",
                    "type": "Agent",
                    "label": {
                        "en": ["Centre for Digital Humanities, University of Gothenburg"],
                        "sv": ["Centrum för digital humaniora, Göteborgs universitet"]
                    },
                    "homepage": [
                        {
                            "id": "https://shfa.dh.gu.se/",
                            "type": "Text",
                            "label": {
                                "en": ["DIANA - Rock Carvings Database"],
                                "sv": ["SHFA - Hällristningsdatabas"]
                            },
                            "format": "text/html"
                        }
                    ]
                }
            ],
            # Rights and attribution
            "rights": "https://creativecommons.org/licenses/by-sa/4.0/",
            "requiredStatement": {
                "label": {
                    "en": ["Attribution"],
                    "sv": ["Källhänvisning"]
                },
                "value": {
                    "en": [self._get_attribution(image, "en")],
                    "sv": [self._get_attribution(image, "sv")]
                }
            },
            # Add seeAlso for machine-readable data
            "seeAlso": [
                {
                    "id": f"{base_manifest_url}/api/shfa/image/{image.id}/",
                    "type": "Dataset",
                    "label": {
                        "en": ["Full metadata"],
                        "sv": ["Fullständiga metadata"]
                    },
                    "format": "application/json"
                }
            ]
        }
        
        return manifest
    
    def create_collection_manifest(self, images: List, title: str = "Rock Carving Collection") -> Dict:
        """Create a IIIF collection manifest for multiple rock carving images."""
        base_manifest_url = getattr(settings, 'IIIF_URL')
        collection_id = f"{base_manifest_url}/api/shfa/iiif/collection"
        
        manifests = []
        for image in images:
            if image.iiif_file:
                manifest_id = f"{base_manifest_url}/api/shfa/iiif/manifest/{image.id}"
                
                # Create thumbnail
                iiif_file_url = getattr(image.iiif_file, 'url', None)
                if not iiif_file_url.startswith("http"):
                    iiif_file_url = self.base_url.rstrip('/') + '/' + iiif_file_url.lstrip("/")
                
                width = getattr(image, 'width', 1000)
                height = getattr(image, 'height', 800)
                title = self._get_image_title(image)
                
                manifests.append({
                    "id": manifest_id,
                    "type": "Manifest",
                    "label": {
                        "en": [title["en"]],
                        "sv": [title["sv"]]
                    },
                    "thumbnail": [
                        {
                            "id": f"{iiif_file_url}/full/300,/0/default.jpg",
                            "type": "Image",
                            "format": "image/jpeg",
                            "width": 300,
                            "height": int(300 * height / width) if width > 0 else 300
                        }
                    ]
                })
        
        collection = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": collection_id,
            "type": "Collection",
            "label": {
                "en": [title],
                "sv": [title]
            },
            "summary": {
                "en": ["Collection of rock carving documentation images from the DIANA database"],
                "sv": ["Samling av hällristningsdokumentationsbilder från DIANA-databasen"]
            },
            "items": manifests,
            "provider": [
                {
                    "id": "https://dh.gu.se/",
                    "type": "Agent",
                    "label": {
                        "en": ["Centre for Digital Humanities, University of Gothenburg"],
                        "sv": ["Centrum för digital humaniora, Göteborgs universitet"]
                    }
                }
            ]
        }
        
        return collection
    
    def _get_image_title(self, image) -> Dict[str, str]:
        """Generate a meaningful title for the rock carving image."""
        # Build title based on available information
        parts_en = ["Rock carving"]
        parts_sv = ["Hällristning"]
        
        # Add site information
        if image.site:
            if image.site.placename:
                parts_en.append(f"at {image.site.placename}")
                parts_sv.append(f"vid {image.site.placename}")
            elif image.site.raa_id:
                parts_en.append(f"at {image.site.raa_id}")
                parts_sv.append(f"vid {image.site.raa_id}")
            elif image.site.lamning_id:
                parts_en.append(f"at {image.site.lamning_id}")
                parts_sv.append(f"vid {image.site.lamning_id}")
        
        # Add rock carving object
        if image.rock_carving_object:
            parts_en.append(f"({image.rock_carving_object.name})")
            parts_sv.append(f"({image.rock_carving_object.name})")
        
        # Add year if available
        if image.year:
            parts_en.append(f"- {image.year}")
            parts_sv.append(f"- {image.year}")
        
        # Fallback to image ID if no other info
        if len(parts_en) == 1:  # Only "Rock carving"
            parts_en.append(f"(Image {image.id})")
            parts_sv.append(f"(Bild {image.id})")
        
        return {
            "en": " ".join(parts_en),
            "sv": " ".join(parts_sv)
        }
    
    def _get_summary(self, image) -> Dict[str, str]:
        """Generate a meaningful summary for the rock carving image."""
        # Check for explicit description first
        if hasattr(image, 'description') and image.description:
            return {"en": image.description, "sv": image.description}
        
        # Build summary from available metadata
        summary_parts_en = []
        summary_parts_sv = []
        
        # Add image type
        if image.type:
            type_en = image.type.english_translation or image.type.text
            summary_parts_en.append(f"{type_en} documentation")
            summary_parts_sv.append(f"{image.type.text}-dokumentation")
        else:
            summary_parts_en.append("Rock carving documentation")
            summary_parts_sv.append("Hällristningsdokumentation")
        
        # Add site info
        if image.site and image.site.placename:
            summary_parts_en.append(f"from {image.site.placename}")
            summary_parts_sv.append(f"från {image.site.placename}")
        
        # Add year
        if image.year:
            summary_parts_en.append(f"photographed in {image.year}")
            summary_parts_sv.append(f"fotograferat {image.year}")
        
        # Add collection info
        if image.collection:
            summary_parts_en.append(f"Part of the {image.collection.name} collection")
            summary_parts_sv.append(f"Del av samlingen {image.collection.name}")
        
        summary_parts_en.append("from the DIANA database.")
        summary_parts_sv.append("från DIANA-databasen.")
        
        return {
            "en": " ".join(summary_parts_en),
            "sv": " ".join(summary_parts_sv)
        }
    
    def _get_attribution(self, image, lang: str) -> str:
        """Generate attribution statement."""
        parts = []
        
        if image.author:
            if lang == "en":
                parts.append(f"Photographer: {image.author.english_translation or image.author.name}")
            else:
                parts.append(f"Fotograf: {image.author.name}")
        
        if image.institution:
            if lang == "en":
                parts.append(f"Institution: {image.institution.name}")
            else:
                parts.append(f"Institution: {image.institution.name}")
        
        if lang == "en":
            parts.append(f"DIANA Rock Carvings Database. Image ID: {image.id}")
        else:
            parts.append(f"DIANA Hällristningsdatabas. Bild-ID: {image.id}")
        
        return ". ".join(parts)
    
    def _build_metadata(self, image) -> List[Dict]:
        """Build comprehensive metadata array for IIIF manifest."""
        metadata = []
        
        # Site information
        if image.site:
            if image.site.raa_id:
                metadata.append({
                    "label": {"en": ["RAÄ Number"], "sv": ["RAÄ-nummer"]},
                    "value": {"en": [image.site.raa_id], "sv": [image.site.raa_id]}
                })
            
            if image.site.lamning_id:
                metadata.append({
                    "label": {"en": ["Lämning ID"], "sv": ["Lämnings-ID"]},
                    "value": {"en": [image.site.lamning_id], "sv": [image.site.lamning_id]}
                })
            
            if image.site.placename:
                metadata.append({
                    "label": {"en": ["Location"], "sv": ["Plats"]},
                    "value": {"en": [image.site.placename], "sv": [image.site.placename]}
                })
            
            if image.site.municipality:
                metadata.append({
                    "label": {"en": ["Municipality"], "sv": ["Kommun"]},
                    "value": {"en": [image.site.municipality.name], "sv": [image.site.municipality.name]}
                })
            
            if image.site.province:
                metadata.append({
                    "label": {"en": ["Province"], "sv": ["Landskap"]},
                    "value": {"en": [image.site.province.name], "sv": [image.site.province.name]}
                })
        
        # Rock carving object/area
        if image.rock_carving_object:
            metadata.append({
                "label": {"en": ["Rock Carving Area"], "sv": ["Hällristningsområde"]},
                "value": {"en": [image.rock_carving_object.name], "sv": [image.rock_carving_object.name]}
            })
        
        # Documentation information
        if image.year:
            metadata.append({
                "label": {"en": ["Documentation Year"], "sv": ["Dokumentationsår"]},
                "value": {"en": [str(image.year)], "sv": [str(image.year)]}
            })
        
        # Image type and subtype
        if image.type:
            type_en = image.type.english_translation or image.type.text
            metadata.append({
                "label": {"en": ["Image Type"], "sv": ["Bildtyp"]},
                "value": {"en": [type_en], "sv": [image.type.text]}
            })
        
        if image.subtype:
            subtype_en = image.subtype.english_translation or image.subtype.text
            metadata.append({
                "label": {"en": ["Image Subtype"], "sv": ["Bildundertyp"]},
                "value": {"en": [subtype_en], "sv": [image.subtype.text]}
            })
        
        # Creator information
        if image.author:
            author_en = image.author.english_translation or image.author.name
            metadata.append({
                "label": {"en": ["Creator/Photographer"], "sv": ["Skapare/Fotograf"]},
                "value": {"en": [author_en], "sv": [image.author.name]}
            })
        
        # People (additional creators)
        people = getattr(image, 'people', None)
        if people:
            try:
                people_list = people.all()
                if people_list:
                    en_people = [p.english_translation or p.name for p in people_list]
                    sv_people = [p.name for p in people_list]
                    metadata.append({
                        "label": {"en": ["Additional Creators"], "sv": ["Ytterligare skapare"]},
                        "value": {"en": en_people, "sv": sv_people}
                    })
            except:
                pass
        
        # Institution
        if image.institution:
            metadata.append({
                "label": {"en": ["Institution"], "sv": ["Institution"]},
                "value": {"en": [image.institution.name], "sv": [image.institution.name]}
            })
        
        # Collection
        if image.collection:
            metadata.append({
                "label": {"en": ["Collection"], "sv": ["Samling"]},
                "value": {"en": [image.collection.name], "sv": [image.collection.name]}
            })
        
        # Keywords/subjects
        keywords = getattr(image, 'keywords', None)
        if keywords:
            try:
                keyword_list = keywords.all()
                if keyword_list:
                    en_keywords = [k.english_translation or k.text for k in keyword_list]
                    sv_keywords = [k.text for k in keyword_list]
                    metadata.append({
                        "label": {"en": ["Subjects/Motifs"], "sv": ["Motiv"]},
                        "value": {"en": en_keywords, "sv": sv_keywords}
                    })
            except:
                pass
        
        # Dating information
        dating_tags = getattr(image, 'dating_tags', None)
        if dating_tags:
            try:
                dating_list = dating_tags.all()
                if dating_list:
                    en_datings = [d.english_translation or d.text for d in dating_list]
                    sv_datings = [d.text for d in dating_list]
                    metadata.append({
                        "label": {"en": ["Dating"], "sv": ["Datering"]},
                        "value": {"en": en_datings, "sv": sv_datings}
                    })
            except:
                pass
        
        # Technical metadata
        if image.width and image.height:
            metadata.append({
                "label": {"en": ["Dimensions"], "sv": ["Dimensioner"]},
                "value": {
                    "en": [f"{image.width} × {image.height} pixels"],
                    "sv": [f"{image.width} × {image.height} pixlar"]
                }
            })
        
        # References
        if image.reference:
            metadata.append({
                "label": {"en": ["References"], "sv": ["Referenser"]},
                "value": {"en": [image.reference], "sv": [image.reference]}
            })
        
        # Group information
        if image.group:
            metadata.append({
                "label": {"en": ["Visualization Group"], "sv": ["Visualiseringsgrupp"]},
                "value": {"en": [image.group.text], "sv": [image.group.text]}
            })
        
        # Legacy ID for reference
        if image.legacy_id:
            metadata.append({
                "label": {"en": ["Legacy ID"], "sv": ["Äldre ID"]},
                "value": {"en": [str(image.legacy_id)], "sv": [str(image.legacy_id)]}
            })
        
        return metadata