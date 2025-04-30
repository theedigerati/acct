from django.contrib import admin
from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
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
from apps.purchase.bill.views import BillViewSet, PaymentMadeViewSet
from apps.purchase.expense.views import ExpenseViewSet
from apps.purchase.vendor.views import VendorViewSet
from apps.sales.client.views import ClientViewSet
from apps.sales.invoice.views import InvoiceViewSet, PaymentReceivedViewSet
from apps.user.views import UserViewSet
from apps.department.views import DepartmentViewSet
from apps.user.views import PermissionViewSet
from apps.inventory.item.views import ItemViewSet
from apps.inventory.item.views import ServiceViewSet
from apps.tax.views import TaxViewSet
from apps.accounting.views import AccountViewSet, JournalEntryViewSet


@api_view()
@authentication_classes([])
@permission_classes([])
def main(request):
    return Response({"message": "Accounting API!"})


urlpatterns = [
    path("", main, name="home"),
    path("admin/", admin.site.urls),
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
router.register(r"departments", DepartmentViewSet)
router.register(r"permissions", PermissionViewSet)
router.register(r"items", ItemViewSet)
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"taxes", TaxViewSet, basename="tax")
router.register(r"accounts", AccountViewSet)
router.register(r"journal-entries", JournalEntryViewSet, basename="journal-entry")
router.register(r"clients", ClientViewSet)
router.register(r"invoices", InvoiceViewSet)
router.register(
    r"payments-received", PaymentReceivedViewSet, basename="payment-received"
)
router.register(r"vendors", VendorViewSet)
router.register(r"bills", BillViewSet)
router.register(r"payments-made", PaymentMadeViewSet, basename="payment-made")
router.register(r"expenses", ExpenseViewSet)

urlpatterns += router.urls
urlpatterns += staticfiles_urlpatterns()

handler500 = "rest_framework.exceptions.server_error"
