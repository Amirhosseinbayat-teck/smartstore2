import json

from pydantic import ValidationError

from .gapgpt_service import generate_text
from .schemas import ProductAnalysis


def analyze_product(
    name,
    category="",
    features="",
    business_type="",
    target_audience="",
    business_description="",
    existing_categories=None,
):
    name = name.strip()
    category = category.strip()
    features = features.strip()

    existing_categories = existing_categories or []
    category_names = [
        item["name"] if isinstance(item, dict) else str(item)
        for item in existing_categories
    ]

    prompt = f"""
تو دستیار هوشمند تحلیل محصول برای یک فروشگاه اینترنتی فارسی‌زبان هستی.

اطلاعات محصول:
نام: {name}
دسته‌بندی انتخاب‌شده: {category or "انتخاب نشده"}
ویژگی‌های اعلام‌شده توسط مدیر: {features or "اعلام نشده"}

اطلاعات کسب‌وکار:
نوع کسب‌وکار: {business_type or "نامشخص"}
مخاطبان هدف: {target_audience or "نامشخص"}
توضیحات کسب‌وکار: {business_description or "نامشخص"}

دسته‌بندی‌های موجود فروشگاه:
{json.dumps(category_names, ensure_ascii=False)}

وظیفه:
محصول را از نظر تناسب با حوزه فعالیت فروشگاه بررسی کن.
صرفاً بر اساس شباهت واژگان تصمیم نگیر؛ معنای محصول و نوع کسب‌وکار را در نظر بگیر.

مقادیر مجاز relevance_status:
- relevant: محصول با حوزه فعالیت فروشگاه تناسب دارد.
- irrelevant: محصول به‌وضوح با حوزه فعالیت فروشگاه ناسازگار است.
- needs_review: اطلاعات کافی برای تصمیم مطمئن وجود ندارد.

مقادیر مجاز relevance_confidence:
- high
- medium
- low

قوانین تشخیص تناسب:
- نوع کسب‌وکار، توضیحات کسب‌وکار و مخاطبان هدف را در نظر بگیر.
- اگر نوع کسب‌وکار نامشخص است یا نام محصول مبهم است، در صورت نبود شواهد کافی از needs_review استفاده کن.
- محصولی را فقط به دلیل اینکه دسته‌بندی مشابهی دارد، مرتبط اعلام نکن.
- اگر محصول به‌وضوح خارج از حوزه فروشگاه است، irrelevant را انتخاب کن.
- دلیل تصمیم را کوتاه، روشن و به زبان فارسی بنویس.
- میزان اطمینان باید با اطلاعات موجود متناسب باشد.
- وضعیت تناسب، پیشنهاد دسته‌بندی و توضیحات محصول باید با یکدیگر سازگار باشند.

یک تحلیل دقیق تولید کن و فقط یک شیء JSON معتبر برگردان
که دقیقاً این کلیدها را داشته باشد:
suggested_category
description
key_features
search_keywords
missing_information
clarification_questions
relevance_status
relevance_reason
relevance_confidence

قوانین تولید محتوا:
- فقط از اطلاعات تأییدشده استفاده کن.
- ویژگی، برند، جنس، گارانتی، قیمت، موجودی یا قابلیت ساختگی نساز.
- key_features فقط شامل ویژگی‌هایی باشد که مدیر اعلام کرده است.
- اگر ویژگی مشخصی اعلام نشده، key_features را خالی برگردان.
- description متن فارسی مناسب فروشگاه اینترنتی باشد.
- search_keywords عبارت‌های مرتبط با نام واقعی محصول باشند.
- missing_information شامل اطلاعات مفیدی باشد که هنوز اعلام نشده‌اند.
- clarification_questions فقط سؤال‌های ضروری برای تکمیل اطلاعات باشند.
- suggested_category را در صورت امکان از دسته‌بندی‌های موجود انتخاب کن.
- اگر هیچ دسته‌بندی مناسبی وجود ندارد، یک نام پیشنهادی کوتاه ارائه کن.
- خروجی باید JSON معتبر باشد و هیچ متن اضافه‌ای بیرون JSON نداشته باشد.
"""

    raw_result = generate_text(prompt)

    if not raw_result or not raw_result.strip():
        raise ValueError("AI returned an empty product analysis.")

    result_text = raw_result.strip()

    if result_text.startswith("```"):
        result_text = result_text.split("\n", 1)[-1]
        if result_text.endswith("```"):
            result_text = result_text[:-3].strip()

    try:
        data = json.loads(result_text)
        analysis = ProductAnalysis.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(
            "AI returned an invalid product analysis."
        ) from exc

    return analysis
