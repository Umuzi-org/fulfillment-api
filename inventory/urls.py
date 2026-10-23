from rest_framework.routers import DefaultRouter

from inventory.views import ProductViewSet, WarehouseViewSet

router = DefaultRouter()
router.register("warehouses", WarehouseViewSet, basename="warehouse")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls
