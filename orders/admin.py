from django.contrib import admin

from .models import FulfillmentOrder, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 1


@admin.register(FulfillmentOrder)
class FulfillmentOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "account", "status", "created_at")
    inlines = [OrderLineInline]
