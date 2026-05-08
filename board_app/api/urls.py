from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BoardViewSet,
    TestApiView,
    EmailCheckView,
    AssignedToMeView,
    TaskViewSet,
    ReviewingView,
    CommentListCreateView,
)

router = DefaultRouter()
router.register(r"boards", BoardViewSet, basename="board")
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("tasks/assigned-to-me/", AssignedToMeView.as_view(), name="assigned-to-me"),
    path("tasks/reviewing/", ReviewingView.as_view(), name="reviewing"),
    path("tasks/<int:pk>/comments/", CommentListCreateView.as_view()),
    path("", include(router.urls)),
    path("test/", TestApiView.as_view(), name="api-test"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
]
