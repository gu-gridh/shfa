from django.urls import path, include
from rest_framework import routers
from . import views
import diana.utils as utils


router = routers.DefaultRouter()
endpoint = utils.build_app_endpoint("shfa")
documentation = utils.build_app_api_documentation("shfa", endpoint)

router.register(rf'{endpoint}/image', views.IIIFImageViewSet, basename='image')
router.register(rf'{endpoint}/geojson/site', views.SiteGeoViewSet, basename='site as geojson')
router.register(rf'{endpoint}/site', views.SiteViewSet, basename='site')

urlpatterns = [
    path('', include(router.urls)),

    # Automatically generated views
    *utils.get_model_urls('shfa', endpoint, 
        exclude=['image', 'site', 'image_keywords', 
                'image_carving_tags', 'image_dating_tags', 'compilation_images']),

    *utils.get_model_urls('shfa', f'{endpoint}', exclude=['image', 'site']),
    *documentation
]