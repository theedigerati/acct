from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter

from apps.organisation.views import OrganisationViewSet
from apps.user.views import UserViewSet


@api_view()
@authentication_classes([])
@permission_classes([])
def main(request):
    return Response({"message": "Accounting API!"})


urlpatterns = [
    path("", main, name="home"),
    path("admin/", admin.site.urls),
    # docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-docs",
    ),
    # auth
    path("auth/login/", TokenObtainPairView.as_view(), name="jwt-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="jwt-refresh"),
]

router = SimpleRouter()
router.register(r"organisations", OrganisationViewSet)
router.register(r"users", UserViewSet)

urlpatterns += router.urls
urlpatterns += staticfiles_urlpatterns()

handler500 = "rest_framework.exceptions.server_error"
