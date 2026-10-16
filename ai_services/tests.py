from unittest.mock import patch, call

from django.test import SimpleTestCase
from pydantic import ValidationError

from ai_services.schemas import StoreDesign, ProductAnalysis
from ai_services.product_analysis_service import analyze_product
from ai_services.store_design_service import (
    generate_store_design,
    normalize_text,
)


class StoreDesignSchemaTests(SimpleTestCase):
    def setUp(self):
        self.valid_data = {
            "store_name": "فروشگاه آزمایشی",
            "store_description": (
                "فروشگاه آنلاین پوشاک و لباس روزمره."
            ),
            "hero_title": "سبک خودت را انتخاب کن",
            "footer_tagline": "همیشه متفاوت باش",
            "primary_color": "#3366FF",
            "secondary_color": "#FFFFFF",
            "style": "مدرن و مینیمال",
        }

    def test_valid_store_design_is_accepted(self):
        design = StoreDesign.model_validate(self.valid_data)

        self.assertEqual(design.store_name, "فروشگاه آزمایشی")
        self.assertEqual(design.primary_color, "#3366FF")

    def test_invalid_color_is_rejected(self):
        data = self.valid_data.copy()
        data["primary_color"] = "blue"

        with self.assertRaises(ValidationError):
            StoreDesign.model_validate(data)

    def test_too_short_store_name_is_rejected(self):
        data = self.valid_data.copy()
        data["store_name"] = "A"

        with self.assertRaises(ValidationError):
            StoreDesign.model_validate(data)

    def test_missing_required_field_is_rejected(self):
        data = self.valid_data.copy()
        del data["hero_title"]

        with self.assertRaises(ValidationError):
            StoreDesign.model_validate(data)


class ProductAnalysisSchemaTests(SimpleTestCase):
    def setUp(self):
        self.valid_data = {
            "suggested_category": "پوشاک",
            "description": (
                "این محصول برای استفاده روزمره معرفی شده است."
            ),
            "key_features": ["استفاده روزمره"],
            "search_keywords": ["پوشاک", "لباس روزمره"],
            "missing_information": ["جنس محصول"],
            "clarification_questions": ["جنس محصول چیست؟"],
            "relevance_status": "relevant",
            "relevance_reason": (
                "محصول با حوزه فعالیت فروشگاه پوشاک تناسب دارد."
            ),
            "relevance_confidence": "high",
        }

    def test_valid_product_analysis_is_accepted(self):
        analysis = ProductAnalysis.model_validate(self.valid_data)

        self.assertEqual(analysis.suggested_category, "پوشاک")
        self.assertEqual(
            analysis.search_keywords,
            ["پوشاک", "لباس روزمره"],
        )
        self.assertEqual(analysis.relevance_status, "relevant")
        self.assertEqual(analysis.relevance_confidence, "high")

    def test_too_many_search_keywords_are_rejected(self):
        data = self.valid_data.copy()
        data["search_keywords"] = [
            f"کلمه {i}" for i in range(16)
        ]

        with self.assertRaises(ValidationError):
            ProductAnalysis.model_validate(data)

    def test_invalid_relevance_status_is_rejected(self):
        data = self.valid_data.copy()
        data["relevance_status"] = "unknown"

        with self.assertRaises(ValidationError):
            ProductAnalysis.model_validate(data)

    def test_invalid_relevance_confidence_is_rejected(self):
        data = self.valid_data.copy()
        data["relevance_confidence"] = "very_high"

        with self.assertRaises(ValidationError):
            ProductAnalysis.model_validate(data)

    def test_missing_required_field_is_rejected(self):
        data = self.valid_data.copy()
        del data["description"]

        with self.assertRaises(ValidationError):
            ProductAnalysis.model_validate(data)


class ProductAnalysisServiceTests(SimpleTestCase):
    def setUp(self):
        self.valid_response = (
            '{"suggested_category":"پوشاک",'
            '"description":"لباس مناسب استفاده روزمره است.",'
            '"key_features":["استفاده روزمره"],'
            '"search_keywords":["پوشاک","لباس روزمره"],'
            '"missing_information":["جنس محصول"],'
            '"clarification_questions":["جنس محصول چیست؟"],'
            '"relevance_status":"relevant",'
            '"relevance_reason":"با حوزه فعالیت فروشگاه پوشاک تناسب دارد.",'
            '"relevance_confidence":"high"}'
        )

    @patch(
        "ai_services.product_analysis_service.generate_text"
    )
    def test_valid_ai_response_is_parsed(self, mock_generate_text):
        mock_generate_text.return_value = self.valid_response

        result = analyze_product(
            name="تی‌شرت",
            features="مناسب استفاده روزمره",
        )

        self.assertEqual(result.suggested_category, "پوشاک")
        self.assertEqual(
            result.search_keywords,
            ["پوشاک", "لباس روزمره"],
        )
        self.assertEqual(result.relevance_status, "relevant")
        self.assertEqual(
            result.relevance_reason,
            "با حوزه فعالیت فروشگاه پوشاک تناسب دارد.",
        )
        self.assertEqual(result.relevance_confidence, "high")
        mock_generate_text.assert_called_once()

    @patch(
        "ai_services.product_analysis_service.generate_text"
    )
    def test_invalid_ai_response_raises_value_error(
        self,
        mock_generate_text,
    ):
        mock_generate_text.return_value = (
            "این پاسخ JSON معتبر نیست"
        )

        with self.assertRaises(ValueError):
            analyze_product(name="تی‌شرت")


class StoreDesignGenerationTests(SimpleTestCase):
    def setUp(self):
        self.valid_data = {
            "store_name": "فروشگاه آزمایشی",
            "store_description": "فروشگاه آنلاین پوشاک.",
            "hero_title": "استایلی تازه برای هر روز",
            "footer_tagline": "متفاوت بمان",
            "primary_color": "#3366FF",
            "secondary_color": "#FFFFFF",
            "style": "مدرن",
        }

    def response_for(self, title, tagline):
        data = self.valid_data.copy()
        data["hero_title"] = title
        data["footer_tagline"] = tagline
        return __import__("json").dumps(
            data,
            ensure_ascii=False,
        )

    def test_normalize_text_ignores_common_formatting(self):
        self.assertEqual(
            normalize_text("يک فروشگاه!"),
            normalize_text("یک فروشگاه"),
        )

    @patch("ai_services.store_design_service.generate_text")
    def test_duplicate_title_is_rejected_and_retried(
        self,
        mock_generate_text,
    ):
        mock_generate_text.side_effect = [
            self.response_for(
                "استایلی تازه برای هر روز",
                "شعاری کاملاً متفاوت",
            ),
            self.response_for(
                "انتخابی نو برای استایل تو",
                "متفاوت بمان",
            ),
        ]

        result = generate_store_design(
            "فروشگاه پوشاک",
            previous_titles=["استایلی تازه برای هر روز"],
            previous_taglines=["شعار قدیمی"],
        )

        self.assertEqual(
            result.hero_title,
            "انتخابی نو برای استایل تو",
        )
        self.assertEqual(mock_generate_text.call_count, 2)

    @patch("ai_services.store_design_service.generate_text")
    def test_duplicate_tagline_is_rejected_and_retried(
        self,
        mock_generate_text,
    ):
        mock_generate_text.side_effect = [
            self.response_for(
                "عنوان جدید فروشگاه",
                "شعار قدیمی",
            ),
            self.response_for(
                "عنوانی کاملاً متفاوت",
                "با سلیقه خودت بدرخش",
            ),
        ]

        result = generate_store_design(
            "فروشگاه پوشاک",
            previous_titles=["عنوان قبلی"],
            previous_taglines=["شعار قدیمی"],
        )

        self.assertEqual(
            result.footer_tagline,
            "با سلیقه خودت بدرخش",
        )
        self.assertEqual(mock_generate_text.call_count, 2)

    @patch("ai_services.store_design_service.generate_text")
    def test_repeated_results_raise_value_error_after_three_attempts(
        self,
        mock_generate_text,
    ):
        repeated_response = self.response_for(
            "عنوان تکراری",
            "شعار تکراری",
        )
        mock_generate_text.return_value = repeated_response

        with self.assertRaises(ValueError):
            generate_store_design(
                "فروشگاه پوشاک",
                previous_titles=["عنوان تکراری"],
                previous_taglines=["شعار تکراری"],
            )

        self.assertEqual(mock_generate_text.call_count, 3)

    @patch("ai_services.store_design_service.generate_text")
    def test_prompt_includes_previous_suggestions(
        self,
        mock_generate_text,
    ):
        mock_generate_text.return_value = self.response_for(
            "عنوان جدید",
            "شعار جدید",
        )

        generate_store_design(
            "فروشگاه پوشاک",
            previous_titles=["عنوان قبلی"],
            previous_taglines=["شعار قبلی"],
        )

        prompt = mock_generate_text.call_args.args[0]

        self.assertIn("عنوان قبلی", prompt)
        self.assertIn("شعار قبلی", prompt)