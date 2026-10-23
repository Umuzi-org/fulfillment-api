from django.contrib import admin

from .models import Product, Warehouse, StockMovement

admin.site.register(Warehouse)
admin.site.register(Product)
admin.site.register(StockMovement)
