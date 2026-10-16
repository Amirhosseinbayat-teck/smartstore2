
from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("add/", views.product_create, name="product_create"),

    path(
        "ai/product-description/",
        views.product_ai_description,
        name="product_ai_description",
    ),
    path(
        "ai/product-category-suggestions/",
        views.product_ai_category_suggestions,
        name="product_ai_category_suggestions",
    ),
    path(
        "ai/product-category-create/",
        views.product_ai_category_create,
        name="product_ai_category_create",
    ),
    path(
        "ai/product-analysis/",
        views.product_ai_analysis,
        name="product_ai_analysis",
    ),

    path("categories/", views.category_list, name="category_list"),
    path("categories/add/", views.category_create, name="category_create"),
    path(
        "categories/ai-suggestions/",
        views.category_ai_suggestions,
        name="category_ai_suggestions",
    ),

    path(
        "<int:product_id>/edit/",
        views.product_edit,
        name="product_edit",
    ),
    path(
        "<int:product_id>/toggle/",
        views.product_toggle,
        name="product_toggle",
    ),
]
