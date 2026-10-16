
from .gapgpt_service import generate_text


def generate_product_description(name, category="", features=""):
    name = name.strip()
    category = category.strip()
    features = features.strip()

    prompt = f"""
تو دستیار تولید محتوای یک فروشگاه اینترنتی فارسی‌زبان هستی.

برای محصول زیر، یک توضیح محصول روان، دقیق و مناسب فروشگاه اینترنتی بنویس.

نام محصول:
{name}

دسته‌بندی:
{category or "مشخص نشده"}

ویژگی‌های اعلام‌شده توسط مدیر فروشگاه:
{features or "ویژگی دیگری اعلام نشده است"}

قوانین:
- فقط از اطلاعات ارائه‌شده استفاده کن.
- هیچ مشخصه، برند، جنس، گارانتی، قابلیت یا ویژگی تأییدنشده‌ای نساز.
- اگر اطلاعات کم است، توضیحی عمومی و کوتاه بر اساس نام محصول بنویس.
- متن فارسی، خوانا و مناسب مشتری باشد.
- توضیح بین ۲ تا ۴ جمله باشد.
- از ادعاهای اغراق‌آمیز و اطلاعات ساختگی خودداری کن.
- فقط متن نهایی توضیحات را برگردان؛ مقدمه و عنوان اضافه نکن.
"""

    description = generate_text(prompt)

    if not description or not description.strip():
        raise ValueError("AI returned an empty product description.")

    return description.strip()
