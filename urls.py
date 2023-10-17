from django.urls import path, include
from rest_framework import routers
from . import views
import diana.utils as utils


router = routers.DefaultRouter()
endpoint = utils.build_app_endpoint("shfa")
documentation = utils.build_app_api_documentation("shfa", endpoint)

router.register(rf'{endpoint}/image', views.IIIFImageViewSet, basename='image')
router.register(rf'{endpoint}/bild/rdf', views.IIIFImageXMLViewSet, basename='bild')

router.register(rf'{endpoint}/geojson/site', views.SiteGeoViewSet, basename='site as geojson')
router.register(rf'{endpoint}/compilation', views.CompilationViewset, basename='compilation')
# urls for advanced search options 
router.register(rf'{endpoint}/search/site', views.SiteSearchViewSet, basename='site')
router.register(rf'{endpoint}/search/type', views.TypeSearchViewSet, basename='site')
router.register(rf'{endpoint}/search/keywords', views.SearchKeywords, basename='keywords')
router.register(rf'{endpoint}/search/carving', views.SearchRockCarving, basename='search rock carving')
router.register(rf'{endpoint}/search/author', views.SearchAuthor, basename='search for image creator')
router.register(rf'{endpoint}/search/institution', views.SearchInstitution, basename='institution')
router.register(rf'{endpoint}/search/dating', views.SearchDatinTag, basename='dating Tag')
router.register(rf'{endpoint}/search/advance', views.AdvancedSearch, basename='advanced search')
# General search url
router.register(rf'{endpoint}/search', views.GeneralSearch, basename='search')

# add oai-pmh end points
router.register(rf'{endpoint}/oai', views.OAI_PMHView, basename='OAI_PMH')


urlpatterns = [
    path('', include(router.urls)),

    # Automatically generated views
    *utils.get_model_urls('shfa', endpoint, 
        exclude=['image', 'site', 'compilation', 'image_keywords', 
                'image_carving_tags', 'image_dating_tags', 'compilation_images']),

    *utils.get_model_urls('shfa', f'{endpoint}', exclude=['image', 'site']),
    *documentation
]