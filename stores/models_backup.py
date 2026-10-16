
from django.db import models
from django.contrib.auth.models import User


class Store(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="stores",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class BusinessInformation(models.Model):
    BUSINESS_TYPES = [
        ("clothing", "پوشاک"),
        ("electronics", "لوازم الکترونیکی"),
        ("food", "مواد غذایی"),
        ("beauty", "زیبایی و آرایشی"),
        ("other", "سایر"),
    ]

    store = models.OneToOneField(
        Store,
        on_delete=models.CASCADE,
        related_name="business_information",
    )
    business_type = models.CharField(
        max_length=50,
        choices=BUSINESS_TYPES,
    )
    target_audience = models.CharField(max_length=200)
    style = models.CharField(max_length=100)
    additional_description = models.TextField(blank=True)

    def __str__(self):
        return f"اطلاعات کسب‌وکار: {self.store.name}"


class StoreDesign(models.Model):
    store = models.OneToOneField(
        Store,
        on_delete=models.CASCADE,
        related_name="design",
    )
    hero_title = models.CharField(
        max_length=100,
        default="Welcome to our store",
    )
    footer_tagline = models.CharField(
        max_length=200,
        default="Discover something new",
    )
    primary_color = models.CharField(max_length=7)
    secondary_color = models.CharField(max_length=7)
    style = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"طراحی فروشگاه: {self.store.name}"


class StoreDesignHistory(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="design_history",
    )
    hero_title = models.CharField(max_length=100)
    footer_tagline = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"تاریخچه طراحی: {self.store.name}"
