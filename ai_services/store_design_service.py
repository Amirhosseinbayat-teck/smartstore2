
import json
import re

from django.db import transaction

from ai_services.gapgpt_service import generate_text
from ai_services.schemas import StoreDesign as StoreDesignSchema
from stores.models import (
    Store,
    StoreDesign as StoreDesignModel,
    StoreDesignHistory,
)


MAX_GENERATION_ATTEMPTS = 3


def normalize_text(value):
    """
    نرمال‌سازی متن برای تشخیص خروجی‌های تکراری.
    فاصله‌ها، علائم نگارشی و برخی تفاوت‌های حروف
    فارسی و عربی در مقایسه نادیده گرفته می‌شوند.
    """
    value = (value or "").casefold()

    value = value.translate(
        str.maketrans({
            "ي": "ی",
            "ى": "ی",
            "ك": "ک",
            "ة": "ه",
            "ۀ": "ه",
            "ؤ": "و",
            "إ": "ا",
            "أ": "ا",
            "ٱ": "ا",
        })
    )

    value = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", value)
    value = re.sub(r"[\W_]+", "", value, flags=re.UNICODE)

    return value


def generate_store_design(
    business_description,
    previous_titles=None,
    previous_taglines=None,
):
    used_titles = list(previous_titles or [])
    used_taglines = list(previous_taglines or [])

    for attempt in range(MAX_GENERATION_ATTEMPTS):
        titles_text = (
            "\n".join(f"- {title}" for title in used_titles)
            or "- No previous titles"
        )

        taglines_text = (
            "\n".join(f"- {tagline}" for tagline in used_taglines)
            or "- No previous taglines"
        )

        prompt = f"""
        Create a creative e-commerce store design based on
        this business description:

        {business_description}

        Previously used homepage titles:
        {titles_text}

        Previously used footer taglines:
        {taglines_text}

        IMPORTANT:
        - Generate a genuinely new hero_title.
        - Generate a genuinely new footer_tagline.
        - Never repeat any previous title or tagline.
        - Avoid minor rewordings of previous suggestions.
        - Use a different creative angle and wording.
        - Write in the same language as the business description.
        - Keep the store name and description suitable for the business.

        Return only a valid JSON object with these fields:
        store_name: a suitable store name
        store_description: a description of the store
        hero_title: a short, catchy homepage headline
        footer_tagline: a short, memorable footer slogan
        primary_color: hex color code such as #3366FF
        secondary_color: hex color code such as #FFFFFF
        style: short design style

        Do not include Markdown or explanations.
        """

        response_text = generate_text(prompt)
        data = json.loads(response_text)
        design = StoreDesignSchema.model_validate(data)

        title_key = normalize_text(design.hero_title)
        tagline_key = normalize_text(design.footer_tagline)

        used_title_keys = {
            normalize_text(title)
            for title in used_titles
        }

        used_tagline_keys = {
            normalize_text(tagline)
            for tagline in used_taglines
        }

        title_is_duplicate = (
            not title_key or title_key in used_title_keys
        )

        tagline_is_duplicate = (
            not tagline_key
            or tagline_key in used_tagline_keys
        )

        if not title_is_duplicate and not tagline_is_duplicate:
            return design

        # خروجی ردشده را هم به فهرست اضافه می‌کنیم
        # تا تلاش بعدی دوباره همان پیشنهاد را دریافت نکند.
        used_titles.append(design.hero_title)
        used_taglines.append(design.footer_tagline)

    raise ValueError(
        "AI could not generate a unique title and tagline "
        f"after {MAX_GENERATION_ATTEMPTS} attempts."
    )


@transaction.atomic
def save_store_design(store, design):
    store.name = design.store_name
    store.description = design.store_description
    store.save(update_fields=["name", "description"])

    StoreDesignModel.objects.update_or_create(
        store=store,
        defaults={
            "hero_title": design.hero_title,
            "footer_tagline": design.footer_tagline,
            "primary_color": design.primary_color,
            "secondary_color": design.secondary_color,
            "style": design.style,
        },
    )

    StoreDesignHistory.objects.create(
        store=store,
        hero_title=design.hero_title,
        footer_tagline=design.footer_tagline,
    )

    return store