
import json

from pydantic import ValidationError

from ai_services.category_schemas import CategorySuggestions
from ai_services.gapgpt_service import generate_text


def generate_category_suggestions(
    business_type,
    target_audience,
    business_description="",
    product_name="",
    existing_categories=None,
):
    existing_categories = existing_categories or []

    existing_categories_text = (
        json.dumps(existing_categories, ensure_ascii=False, indent=2)
        if existing_categories
        else "هنوز دسته‌بندی‌ای برای این فروشگاه ثبت نشده است."
    )

    product_context = ""
    if product_name:
        product_context = f"""
نام محصول موردنظر:
{product_name}

دسته‌بندی پیشنهادی باید با این محصول مرتبط باشد.
"""

    prompt = f"""
تو یک مشاور متخصص دسته‌بندی محصولات فروشگاه اینترنتی هستی.

اطلاعات فروشگاه:
- نوع کسب‌وکار: {business_type}
- مخاطبان هدف: {target_audience}
- توضیحات کسب‌وکار: {business_description}

دسته‌بندی‌های موجود فروشگاه به همراه توضیحات:
{existing_categories_text}

{product_context}

وظایف:
1. دسته‌بندی‌های موجود را با توجه به نام و توضیحاتشان بررسی کن.
2. دسته‌بندی‌ای با نام یکسان یا تفاوت جزئی در نوشتار پیشنهاد نده.
3. اگر دسته‌بندی موجود از نظر معنایی همان کاربرد را پوشش می‌دهد، دسته‌بندی جدید مشابه آن نساز.
4. دسته‌بندی‌های نزدیک اما واقعاً متفاوت را فقط در صورت نیاز پیشنهاد بده.
5. پیشنهادها باید با نوع کسب‌وکار و محصولات فروشگاه مرتبط باشند.
6. نام‌ها و توضیحات را به فارسی روان بنویس.
7. حداکثر 5 دسته‌بندی پیشنهاد بده.
8. فقط JSON معتبر و بدون Markdown برگردان.

قالب پاسخ:
{{
    "categories": [
        {{
            "name": "نام دسته‌بندی",
            "description": "توضیح کوتاه دسته‌بندی"
        }}
    ]
}}

اگر دسته‌بندی جدید مناسبی وجود ندارد، آرایه categories را خالی برگردان.
"""

    response_text = generate_text(prompt)

    try:
        data = json.loads(response_text)
        suggestions = CategorySuggestions.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(
            "The AI returned an invalid category response."
        ) from exc

    existing_names = {
        item["name"].strip().casefold()
        for item in existing_categories
        if item.get("name")
    }

    unique_suggestions = []
    seen_names = set()

    for category in suggestions.categories:
        normalized_name = category.name.strip().casefold()

        if normalized_name in existing_names:
            continue

        if normalized_name in seen_names:
            continue

        seen_names.add(normalized_name)
        unique_suggestions.append(category)

    suggestions.categories = unique_suggestions
    return suggestions
