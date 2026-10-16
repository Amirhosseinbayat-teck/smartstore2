
from django.contrib import admin
from django.urls import path, include
from stores import views as store_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("users/", include("users.urls")),
    path("stores/", include("stores.urls")),
    path("products/", include("products.urls")),
    path("store/<slug:slug>/", store_views.public_store, name="public_store"),
    path("", store_views.home, name="home"),
]
