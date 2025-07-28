# URLS for manifest app
from django.urls import path, include
from rest_framework import routers
from .views import ManifestIIIFViewSet  
from . import views

router = routers.DefaultRouter()
router.register(r'manifest', ManifestIIIFViewSet, basename='manifest')

urlpatterns = [
    path('manifest/<int:pk>/',
          ManifestIIIFViewSet.as_view({'get': 'manifest'}),
          name='manifest-detail'),
    path('manifest/collection/',
         ManifestIIIFViewSet.as_view({'get': 'collection'}),
         name='manifest-collection'),
    path('manifest/institution/<int:institution_id>/',
         ManifestIIIFViewSet.as_view({'get': 'institution_manifest'}),
         name='institution-manifest'),
    path('manifest/site/<int:site_id>/',
         ManifestIIIFViewSet.as_view({'get': 'site_collection'}),
         name='site-collection'),
    path('manifest/type/<str:type>/',
         ManifestIIIFViewSet.as_view({'get': 'type_manifest'}),
         name='type-manifest'),
]