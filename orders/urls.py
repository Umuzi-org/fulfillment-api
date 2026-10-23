from rest_framework.routers import DefaultRouter

from orders.views import FulfillmentOrderViewSet

router = DefaultRouter()
router.register("orders", FulfillmentOrderViewSet, basename="order")

urlpatterns = router.urls
