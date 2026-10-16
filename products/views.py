from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError

from stores.models import Store, BusinessInformation
from ai_services.category_service import generate_category_suggestions
from ai_services.product_description_service import generate_product_description
from ai_services.product_analysis_service import analyze_product
from .models import Product, Category
from .forms import ProductForm


@login_required
def product_list(request):
    stores = Store.objects.filter(owner=request.user)
    store_id = request.GET.get("store_id")

    if store_id:
        store = get_object_or_404(stores, id=store_id)
    else:
        store = stores.order_by("-created_at").first()

    if store is None:
        messages.info(request, "ابتدا یک فروشگاه ایجاد کنید.")
        return redirect("create_store")

    products = Product.objects.filter(
        store=store
    ).select_related("category").order_by("-created_at")

    return render(
        request,
        "products/product_list.html",
        {"store": store, "products": products},
    )


@login_required
def product_create(request):
    store_id = request.GET.get("store_id") or request.POST.get("store_id")
    store = get_object_or_404(Store, id=store_id, owner=request.user)

    if request.method == "POST":
        form = ProductForm(request.POST, store=store)

        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()
            messages.success(request, "محصول با موفقیت اضافه شد.")
            return redirect(f"/products/?store_id={store.id}")
    else:
        form = ProductForm(store=store)

    return render(
        request,
        "products/product_form.html",
        {"form": form, "store": store, "page_title": "افزودن محصول"},
    )


@login_required
def product_edit(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related("store"),
        id=product_id,
        store__owner=request.user,
    )
    store = product.store

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product, store=store)

        if form.is_valid():
            form.save()
            messages.success(request, "محصول با موفقیت ویرایش شد.")
            return redirect(f"/products/?store_id={store.id}")
    else:
        form = ProductForm(instance=product, store=store)

    return render(
        request,
        "products/product_form.html",
        {"form": form, "store": store, "page_title": "ویرایش محصول"},
    )


@login_required
def product_toggle(request, product_id):
    if request.method != "POST":
        return redirect("products:product_list")

    product = get_object_or_404(
        Product,
        id=product_id,
        store__owner=request.user,
    )

    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])

    if product.is_active:
        messages.success(request, "محصول فعال شد.")
    else:
        messages.success(request, "محصول غیرفعال شد.")

    return redirect(f"/products/?store_id={product.store_id}")


@login_required
def product_ai_description(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "درخواست نامعتبر است."},
            status=405,
        )

    store_id = request.POST.get("store_id", "").strip()
    name = request.POST.get("name", "").strip()
    category_id = request.POST.get("category", "").strip()
    features = request.POST.get("features", "").strip()

    if not store_id.isdigit():
        return JsonResponse(
            {"error": "فروشگاه معتبر نیست."},
            status=400,
        )

    store = get_object_or_404(
        Store,
        id=int(store_id),
        owner=request.user,
    )

    if not name:
        return JsonResponse(
            {"error": "ابتدا نام محصول را وارد کنید."},
            status=400,
        )

    if len(name) > 200 or len(features) > 2000:
        return JsonResponse(
            {"error": "طول نام یا ویژگی‌های محصول بیش از حد مجاز است."},
            status=400,
        )

    category_name = ""

    if category_id:
        if not category_id.isdigit():
            return JsonResponse(
                {"error": "دسته‌بندی معتبر نیست."},
                status=400,
            )

        category = get_object_or_404(
            Category,
            id=int(category_id),
            store=store,
        )
        category_name = category.name

    try:
        description = generate_product_description(
            name=name,
            category=category_name,
            features=features,
        )
    except Exception:
        return JsonResponse(
            {
                "error": (
                    "تولید توضیحات ناموفق بود. "
                    "تنظیمات API و اتصال اینترنت را بررسی کنید."
                )
            },
            status=502,
        )

    return JsonResponse({"description": description})


@login_required
def product_ai_category_suggestions(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "روش درخواست نامعتبر است."},
            status=405,
        )

    store_id = request.POST.get("store_id", "").strip()
    product_name = request.POST.get("name", "").strip()

    if not store_id.isdigit():
        return JsonResponse(
            {"error": "فروشگاه معتبر نیست."},
            status=400,
        )

    store = get_object_or_404(
        Store,
        id=int(store_id),
        owner=request.user,
    )

    if not product_name:
        return JsonResponse(
            {"error": "ابتدا نام محصول را وارد کنید."},
            status=400,
        )

    if len(product_name) > 200:
        return JsonResponse(
            {"error": "نام محصول نباید بیشتر از ۲۰۰ نویسه باشد."},
            status=400,
        )

    existing_categories = list(
        Category.objects.filter(store=store).values(
            "id", "name", "description"
        )
    )

    normalized_product_name = product_name.strip().casefold()

    exact_matches = [
        category
        for category in existing_categories
        if category["name"].strip().casefold()
        == normalized_product_name
    ]

    if exact_matches:
        return JsonResponse(
            {
                "suggestions": [
                    {
                        "name": category["name"],
                        "description": category["description"],
                        "existing_id": category["id"],
                    }
                    for category in exact_matches
                ]
            }
        )

    try:
        business_info = BusinessInformation.objects.get(store=store)
    except BusinessInformation.DoesNotExist:
        return JsonResponse(
            {
                "error": (
                    "ابتدا اطلاعات کسب‌وکار این فروشگاه را "
                    "ثبت کنید."
                )
            },
            status=400,
        )

    ai_existing_categories = [
        {
            "name": category["name"],
            "description": category["description"],
        }
        for category in existing_categories
    ]

    try:
        suggestions = generate_category_suggestions(
            business_type=business_info.get_business_type_display(),
            target_audience=business_info.target_audience,
            business_description=business_info.additional_description,
            product_name=product_name,
            existing_categories=ai_existing_categories,
        )
    except Exception:
        return JsonResponse(
            {
                "error": (
                    "دریافت پیشنهادهای دسته‌بندی ناموفق بود. "
                    "تنظیمات API و اتصال اینترنت را بررسی کنید."
                )
            },
            status=502,
        )

    existing_ids = {
        category["name"].strip().casefold(): category["id"]
        for category in existing_categories
    }

    return JsonResponse(
        {
            "suggestions": [
                {
                    "name": category.name,
                    "description": category.description,
                    "existing_id": existing_ids.get(
                        category.name.strip().casefold()
                    ),
                }
                for category in suggestions.categories
            ]
        }
    )


@login_required
def product_ai_category_create(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "روش درخواست نامعتبر است."},
            status=405,
        )

    store_id = request.POST.get("store_id", "").strip()
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()

    if not store_id.isdigit():
        return JsonResponse(
            {"error": "فروشگاه معتبر نیست."},
            status=400,
        )

    store = get_object_or_404(
        Store,
        id=int(store_id),
        owner=request.user,
    )

    if not name or len(name) < 2 or len(name) > 100:
        return JsonResponse(
            {"error": "نام دسته‌بندی باید بین ۲ تا ۱۰۰ نویسه باشد."},
            status=400,
        )

    if len(description) > 300:
        return JsonResponse(
            {"error": "توضیحات دسته‌بندی نباید بیشتر از ۳۰۰ نویسه باشد."},
            status=400,
        )

    existing_category = Category.objects.filter(
        store=store,
        name__iexact=name,
    ).first()

    if existing_category:
        return JsonResponse(
            {
                "id": existing_category.id,
                "name": existing_category.name,
                "created": False,
                "message": "این دسته‌بندی از قبل وجود دارد و انتخاب شد.",
            }
        )

    try:
        category = Category.objects.create(
            store=store,
            name=name,
            description=description,
        )
    except IntegrityError:
        existing_category = Category.objects.filter(
            store=store,
            name__iexact=name,
        ).first()

        if existing_category:
            return JsonResponse(
                {
                    "id": existing_category.id,
                    "name": existing_category.name,
                    "created": False,
                    "message": (
                        "این دسته‌بندی قبلاً ایجاد شده و انتخاب شد."
                    ),
                }
            )

        return JsonResponse(
            {"error": "ذخیره دسته‌بندی ناموفق بود. دوباره تلاش کنید."},
            status=409,
        )

    return JsonResponse(
        {
            "id": category.id,
            "name": category.name,
            "created": True,
            "message": "دسته‌بندی ذخیره شد و آماده انتخاب است.",
        },
        status=201,
    )


@login_required
def category_list(request):
    stores = Store.objects.filter(owner=request.user)
    store_id = request.GET.get("store_id")

    if store_id:
        store = get_object_or_404(stores, id=store_id)
    else:
        store = stores.order_by("-created_at").first()

    if store is None:
        messages.info(request, "ابتدا یک فروشگاه ایجاد کنید.")
        return redirect("create_store")

    categories = Category.objects.filter(store=store).order_by("name")

    return render(
        request,
        "products/category_list.html",
        {"store": store, "categories": categories},
    )


@login_required
def category_create(request):
    store_id = request.GET.get("store_id") or request.POST.get("store_id")
    store = get_object_or_404(Store, id=store_id, owner=request.user)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "نام دسته‌بندی را وارد کنید.")
        elif len(name) > 100:
            messages.error(
                request,
                "نام دسته‌بندی نباید بیشتر از ۱۰۰ نویسه باشد.",
            )
        elif len(description) > 300:
            messages.error(
                request,
                "توضیحات دسته‌بندی نباید بیشتر از ۳۰۰ نویسه باشد.",
            )
        elif Category.objects.filter(
            store=store,
            name__iexact=name,
        ).exists():
            messages.error(request, "این دسته‌بندی قبلاً ایجاد شده است.")
        else:
            try:
                Category.objects.create(
                    store=store,
                    name=name,
                    description=description,
                )
            except IntegrityError:
                messages.error(
                    request,
                    "این دسته‌بندی قبلاً ایجاد شده است.",
                )
            else:
                messages.success(
                    request,
                    "دسته‌بندی با موفقیت ایجاد شد.",
                )
                return redirect(
                    f"/products/categories/?store_id={store.id}"
                )

    return render(
        request,
        "products/category_form.html",
        {"store": store, "page_title": "افزودن دسته‌بندی"},
    )


@login_required
def category_ai_suggestions(request):
    store_id = request.GET.get("store_id") or request.POST.get("store_id")
    store = get_object_or_404(Store, id=store_id, owner=request.user)

    if request.method == "POST":
        selected_indices = request.POST.getlist("selected_indices")

        if not selected_indices:
            messages.warning(request, "حداقل یک دسته‌بندی را انتخاب کنید.")
            return redirect(
                f"/products/categories/ai-suggestions/?store_id={store.id}"
            )

        existing_names = {
            name.strip().casefold()
            for name in Category.objects.filter(
                store=store
            ).values_list("name", flat=True)
        }
        added_count = 0

        for index in selected_indices:
            if not index.isdigit():
                continue

            name = request.POST.get(
                f"category_name_{index}", ""
            ).strip()
            description = request.POST.get(
                f"category_description_{index}", ""
            ).strip()

            if (
                name
                and 2 <= len(name) <= 100
                and len(description) <= 300
                and name.casefold() not in existing_names
            ):
                try:
                    Category.objects.create(
                        store=store,
                        name=name,
                        description=description,
                    )
                except IntegrityError:
                    continue

                existing_names.add(name.casefold())
                added_count += 1

        if added_count:
            messages.success(
                request,
                f"{added_count} دسته‌بندی با موفقیت اضافه شد.",
            )
        else:
            messages.info(
                request,
                "دسته‌بندی جدیدی برای اضافه کردن وجود نداشت.",
            )

        return redirect(f"/products/categories/?store_id={store.id}")

    try:
        business_info = BusinessInformation.objects.get(store=store)
    except BusinessInformation.DoesNotExist:
        messages.warning(
            request,
            "اطلاعات کسب‌وکار این فروشگاه ثبت نشده است.",
        )
        return redirect("/stores/my-stores/")

    existing_categories = list(
        Category.objects.filter(store=store).values(
            "name", "description"
        )
    )

    existing_names = {
        category["name"].strip().casefold()
        for category in existing_categories
    }

    try:
        suggestions = generate_category_suggestions(
            business_type=business_info.get_business_type_display(),
            target_audience=business_info.target_audience,
            business_description=business_info.additional_description,
            existing_categories=existing_categories,
        )
    except Exception:
        messages.error(
            request,
            "دریافت پیشنهادها ناموفق بود. اتصال هوش مصنوعی و تنظیمات API را بررسی کنید.",
        )
        return redirect(f"/products/categories/?store_id={store.id}")

    filtered_suggestions = [
        category
        for category in suggestions.categories
        if category.name.strip().casefold() not in existing_names
    ]

    return render(
        request,
        "products/category_ai_suggestions.html",
        {"store": store, "suggestions": filtered_suggestions},
    )


@login_required
def product_ai_analysis(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "روش درخواست نامعتبر است."},
            status=405,
        )

    store_id = request.POST.get("store_id", "").strip()
    name = request.POST.get("name", "").strip()
    category_id = request.POST.get("category", "").strip()
    features = request.POST.get("features", "").strip()

    if not store_id.isdigit():
        return JsonResponse(
            {"error": "فروشگاه معتبر نیست."},
            status=400,
        )

    store = get_object_or_404(
        Store,
        id=int(store_id),
        owner=request.user,
    )

    if not name:
        return JsonResponse(
            {"error": "ابتدا نام محصول را وارد کنید."},
            status=400,
        )

    if len(name) > 200 or len(features) > 2000:
        return JsonResponse(
            {"error": "طول نام یا ویژگی‌های محصول بیش از حد مجاز است."},
            status=400,
        )

    category_name = ""

    if category_id:
        if not category_id.isdigit():
            return JsonResponse(
                {"error": "دسته‌بندی معتبر نیست."},
                status=400,
            )

        category = get_object_or_404(
            Category,
            id=int(category_id),
            store=store,
        )
        category_name = category.name

    try:
        business_info = BusinessInformation.objects.get(store=store)
    except BusinessInformation.DoesNotExist:
        return JsonResponse(
            {
                "error": (
                    "ابتدا اطلاعات کسب‌وکار این فروشگاه را ثبت کنید."
                )
            },
            status=400,
        )

    existing_categories = list(
        Category.objects.filter(store=store).values(
            "name", "description"
        )
    )

    try:
        analysis = analyze_product(
            name=name,
            category=category_name,
            features=features,
            business_type=business_info.get_business_type_display(),
            target_audience=business_info.target_audience,
            business_description=business_info.additional_description,
            existing_categories=existing_categories,
        )
    except Exception:
        return JsonResponse(
            {
                "error": (
                    "تحلیل هوشمند محصول ناموفق بود. "
                    "تنظیمات API و اتصال اینترنت را بررسی کنید."
                )
            },
            status=502,
        )

    return JsonResponse(
        {
            "suggested_category": analysis.suggested_category,
            "description": analysis.description,
            "key_features": analysis.key_features,
            "search_keywords": analysis.search_keywords,
            "missing_information": analysis.missing_information,
            "clarification_questions": analysis.clarification_questions,
            "relevance_status": analysis.relevance_status,
            "relevance_reason": analysis.relevance_reason,
            "relevance_confidence": analysis.relevance_confidence,
        }
    )