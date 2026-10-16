
from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_store, name="create_store"),
    path("design/edit/", views.edit_store_design, name="edit_store_design"),
    path("design/regenerate/", views.regenerate_store_design, name="regenerate_store_design"),
    path("my-stores/", views.my_stores, name="my_stores"),
]
