
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from stores.models import Store, BusinessInformation, StoreDesign
from ai_services.schemas import StoreDesign as StoreDesignSchema


class CreateStoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="store_test_user",
            password="TestPassword123!",
        )
        self.client.force_login(self.user)

    @patch("stores.views.generate_store_design")
    def test_create_store_saves_store_business_and_design(
        self,
        mock_generate_design,
    ):
        mock_generate_design.return_value = StoreDesignSchema(
            store_name="فروشگاه آزمایشی",
            store_description=(
                "فروشگاه پوشاک روزمره برای جوانان."
            ),
            hero_title="ساده بپوش، متفاوت باش",
            footer_tagline="سبک خودت را انتخاب کن",
            primary_color="#3366FF",
            secondary_color="#FFFFFF",
            style="مدرن و مینیمال",
        )

        response = self.client.post(
            reverse("create_store"),
            {
                "business_type": "clothing",
                "target_audience": "جوانان ۱۸ تا ۳۰ سال",
                "style": "مدرن و مینیمال",
                "additional_description": (
                    "فروشگاه لباس روزمره و اسپرت"
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Store.objects.count(), 1)
        self.assertEqual(BusinessInformation.objects.count(), 1)
        self.assertEqual(StoreDesign.objects.count(), 1)

        store = Store.objects.get(owner=self.user)

        self.assertEqual(store.name, "فروشگاه آزمایشی")
        self.assertEqual(
            store.business_information.business_type,
            "clothing",
        )
        self.assertEqual(
            store.design.hero_title,
            "ساده بپوش، متفاوت باش",
        )

        mock_generate_design.assert_called_once()

    @patch(
        "stores.views.generate_store_design",
        side_effect=Exception("AI service unavailable"),
    )
    def test_create_store_does_not_save_data_when_ai_fails(
        self,
        mock_generate_design,
    ):
        response = self.client.post(
            reverse("create_store"),
            {
                "business_type": "clothing",
                "target_audience": "جوانان",
                "style": "مدرن",
                "additional_description": "فروشگاه لباس",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Store.objects.count(), 0)
        self.assertEqual(BusinessInformation.objects.count(), 0)
        self.assertEqual(StoreDesign.objects.count(), 0)

        mock_generate_design.assert_called_once()
