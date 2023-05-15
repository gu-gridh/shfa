from django.urls import path, include
from rest_framework import routers
from . import views
import diana.utils as utils


router = routers.DefaultRouter()
endpoint = utils.build_app_endpoint("shfa")
documentation = utils.build_app_api_documentation("shfa", endpoint)

router.register(rf'{endpoint}/image', views.IIIFImageViewSet, basename='image')
router.register(rf'{endpoint}/geojson/site', views.SiteGeoViewSet, basename='site as geojson')
# Searching for match objects
router.register(rf'{endpoint}/search/site', views.SiteSearchViewSet, basename='site')
router.register(rf'{endpoint}/search/keywords', views.SearchKeywords, basename='keywords')
router.register(rf'{endpoint}/search/carving', views.SearchRockCarving, basename='search rock carving')
router.register(rf'{endpoint}/search/institution', views.SearchInstitution, basename='institution')
router.register(rf'{endpoint}/search/dating', views.SearchDatinTag, basename='dating Tag')
router.register(rf'{endpoint}/search/advance', views.AdvancedSearch, basename='advanced search')
router.register(rf'{endpoint}/search', views.GeneralSearch, basename='search')


urlpatterns = [
    path('', include(router.urls)),

    # Automatically generated views
    *utils.get_model_urls('shfa', endpoint, 
        exclude=['image', 'site', 'image_keywords', 
                'image_carving_tags', 'image_dating_tags', 'compilation_images']),

    *utils.get_model_urls('shfa', f'{endpoint}', exclude=['image', 'site']),
    *documentation
]