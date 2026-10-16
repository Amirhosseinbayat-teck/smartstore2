from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "description")
    list_filter = ("store",)
    search_fields = ("name", "store__name", "description")
    list_per_page = 20


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "store",
        "category",
        "price",
        "stock",
        "is_active",
    )
    list_filter = ("is_active", "category", "store")
    search_fields = ("name", "store__name", "description")
    list_per_page = 20