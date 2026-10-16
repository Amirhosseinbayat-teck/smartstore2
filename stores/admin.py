

from django.contrib import admin

from .models import Store, BusinessInformation, StoreDesign


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'owner__username')


@admin.register(BusinessInformation)
class BusinessInformationAdmin(admin.ModelAdmin):
    list_display = ('store', 'business_type', 'target_audience', 'style')
    list_filter = ('business_type',)
    search_fields = ('store__name', 'target_audience')


@admin.register(StoreDesign)
class StoreDesignAdmin(admin.ModelAdmin):
    list_display = (
        'store',
        'primary_color',
        'secondary_color',
        'style',
        'updated_at',
    )
    search_fields = ('store__name', 'style')