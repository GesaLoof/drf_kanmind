from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BoardViewSet, TestApiView

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')

urlpatterns = [
    path('', include(router.urls)),
    path('test/', TestApiView.as_view(), name='api-test'),
]