
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages
from django.db import transaction
from django.urls import reverse

from .models import (
    Store,
    BusinessInformation,
    StoreDesign,
    StoreDesignHistory,
)
from products.models import Product, Category
from ai_services.store_design_service import (
    generate_store_design,
    save_store_design,
)


class StoreDesignForm(forms.ModelForm):
    class Meta:
        model = StoreDesign
        fields = [
            "hero_title",
            "footer_tagline",
            "primary_color",
            "secondary_color",
            "style",
        ]
        labels = {
            "hero_title": "عنوان اصلی فروشگاه",
            "footer_tagline": "شعار فروشگاه",
            "primary_color": "رنگ اصلی",
            "secondary_color": "رنگ پس‌زمینه",
            "style": "سبک طراحی",
        }
        widgets = {
            "hero_title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "footer_tagline": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "primary_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control",
                }
            ),
            "secondary_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control",
                }
            ),
            "style": forms.TextInput(
                attrs={"class": "form-control"}
            ),
        }


@login_required
def home(request):
    stores = Store.objects.filter(owner=request.user)
    store_id = request.GET.get("store_id")

    if store_id:
        store = get_object_or_404(
            stores.select_related("design"),
            id=store_id,
        )
    else:
        store = (
            stores.order_by("-created_at")
            .select_related("design")
            .first()
        )

    if store is None:
        return redirect("create_store")

    categories = Category.objects.filter(
        store=store
    ).order_by("name")

    products = (
        Product.objects.filter(
            store=store,
            is_active=True,
        )
        .select_related("category")
        .order_by("-created_at")
    )

    category_id = request.GET.get("category")
    selected_category = None

    if category_id:
        selected_category = get_object_or_404(
            categories,
            id=category_id,
        )
        products = products.filter(
            category=selected_category
        )

    return render(
        request,
        "stores/home.html",
        {
            "store": store,
            "products": products,
            "categories": categories,
            "selected_category": selected_category,
        },
    )


def public_store(request, slug):
    store = get_object_or_404(
        Store.objects.select_related("design"),
        slug=slug,
        is_active=True,
    )

    categories = Category.objects.filter(
        store=store
    ).order_by("name")

    products = (
        Product.objects.filter(
            store=store,
            is_active=True,
        )
        .select_related("category")
        .order_by("-created_at")
    )

    category_id = request.GET.get("category")
    selected_category = None

    if category_id:
        selected_category = get_object_or_404(
            categories,
            id=category_id,
        )
        products = products.filter(
            category=selected_category
        )

    return render(
        request,
        "stores/home.html",
        {
            "store": store,
            "products": products,
            "categories": categories,
            "selected_category": selected_category,
            "is_public_store": True,
        },
    )


@login_required
def create_store(request):
    if request.method == "POST":
        business_type = request.POST.get(
            "business_type", ""
        ).strip()
        target_audience = request.POST.get(
            "target_audience", ""
        ).strip()
        style = request.POST.get("style", "").strip()
        additional_description = request.POST.get(
            "additional_description", ""
        ).strip()

        valid_business_types = {
            choice[0]
            for choice in BusinessInformation.BUSINESS_TYPES
        }

        if (
            business_type not in valid_business_types
            or not target_audience
            or len(target_audience) > 200
            or not style
            or len(style) > 100
        ):
            messages.error(
                request,
                "لطفاً اطلاعات فرم را به‌درستی وارد کنید.",
            )
            return render(
                request,
                "stores/create_store.html",
            )

        business_type_label = dict(
            BusinessInformation.BUSINESS_TYPES
        )[business_type]

        business_description = f"""
Business type: {business_type_label}
Target audience: {target_audience}
Desired style: {style}
Additional details: {additional_description}
"""

        try:
            design = generate_store_design(
                business_description
            )

            with transaction.atomic():
                store = Store.objects.create(
                    owner=request.user,
                    name=design.store_name,
                    description=design.store_description,
                )

                BusinessInformation.objects.create(
                    store=store,
                    business_type=business_type,
                    target_audience=target_audience,
                    style=style,
                    additional_description=additional_description,
                )

                save_store_design(store, design)

            return redirect(
                f"{reverse('home')}?store_id={store.id}"
            )

        except Exception:
            messages.error(
                request,
                "ساخت فروشگاه انجام نشد. لطفاً دوباره تلاش کنید.",
            )

    return render(
        request,
        "stores/create_store.html",
    )


@login_required
def edit_store_design(request):
    store_id = (
        request.POST.get("store_id")
        if request.method == "POST"
        else request.GET.get("store_id")
    )

    store = get_object_or_404(
        Store,
        owner=request.user,
        id=store_id,
    )

    design, _ = StoreDesign.objects.get_or_create(
        store=store,
        defaults={
            "primary_color": "#FF5A36",
            "secondary_color": "#F7F5F0",
            "style": "مدرن",
        },
    )

    if request.method == "POST":
        form = StoreDesignForm(
            request.POST,
            instance=design,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "طراحی فروشگاه با موفقیت ذخیره شد.",
            )

            return redirect(
                f"{reverse('home')}?store_id={store.id}"
            )
    else:
        form = StoreDesignForm(instance=design)

    return render(
        request,
        "stores/edit_design.html",
        {
            "store": store,
            "form": form,
        },
    )


@login_required
def regenerate_store_design(request):
    if request.method != "POST":
        return redirect("home")

    store_id = request.POST.get("store_id")

    store = get_object_or_404(
        Store,
        owner=request.user,
        id=store_id,
    )

    try:
        business_info = store.business_information
    except BusinessInformation.DoesNotExist:
        messages.error(
            request,
            "برای این فروشگاه اطلاعات کسب‌وکار ثبت نشده است.",
        )
        return redirect(
            f"{reverse('edit_store_design')}?store_id={store.id}"
        )

    business_type_label = dict(
        BusinessInformation.BUSINESS_TYPES
    ).get(
        business_info.business_type,
        business_info.business_type,
    )

    business_description = f"""
Business type: {business_type_label}
Target audience: {business_info.target_audience}
Desired style: {business_info.style}
Additional details: {business_info.additional_description}
"""

    try:
        history = StoreDesignHistory.objects.filter(
            store=store
        ).order_by("created_at", "id")

        previous_titles = list(
            history.values_list("hero_title", flat=True)
        )
        previous_taglines = list(
            history.values_list("footer_tagline", flat=True)
        )

        current_design = StoreDesign.objects.filter(
            store=store
        ).first()

        if current_design:
            if current_design.hero_title:
                previous_titles.append(
                    current_design.hero_title
                )
            if current_design.footer_tagline:
                previous_taglines.append(
                    current_design.footer_tagline
                )

        generated_design = generate_store_design(
            business_description,
            previous_titles=previous_titles,
            previous_taglines=previous_taglines,
        )

        with transaction.atomic():
            design, _ = StoreDesign.objects.get_or_create(
                store=store,
                defaults={
                    "primary_color": "#526B55",
                    "secondary_color": "#F7F7F2",
                    "style": business_info.style or "مدرن",
                },
            )

            design.hero_title = generated_design.hero_title
            design.footer_tagline = generated_design.footer_tagline
            design.style = generated_design.style
            design.save(
                update_fields=[
                    "hero_title",
                    "footer_tagline",
                    "style",
                    "updated_at",
                ]
            )

            StoreDesignHistory.objects.create(
                store=store,
                hero_title=generated_design.hero_title,
                footer_tagline=generated_design.footer_tagline,
            )

        messages.success(
            request,
            "عنوان و شعار جدید تولید شدند؛ رنگ‌ها و مشخصات فروشگاه حفظ شدند.",
        )

    except Exception:
        messages.error(
            request,
            "تولید طراحی جدید ناموفق بود. "
            "طراحی قبلی حفظ شد؛ لطفاً تنظیمات سرویس هوش مصنوعی را بررسی کنید.",
        )

    return redirect(
        f"{reverse('edit_store_design')}?store_id={store.id}"
    )


@login_required
def my_stores(request):
    stores = (
        Store.objects.filter(owner=request.user)
        .select_related("design")
        .order_by("-created_at")
    )

    return render(
        request,
        "stores/my_stores.html",
        {
            "stores": stores,
        },
    )

