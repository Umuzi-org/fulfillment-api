from django.contrib import admin

from .models import Product, Warehouse

admin.site.register(Warehouse)
admin.site.register(Product)