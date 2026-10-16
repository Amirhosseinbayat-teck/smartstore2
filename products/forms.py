
from django import forms
from .models import Product, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "description",
            "price",
            "stock",
            "is_active",
        ]

        labels = {
            "category": "دسته‌بندی",
            "name": "نام محصول",
            "description": "توضیحات محصول",
            "price": "قیمت",
            "stock": "موجودی",
            "is_active": "محصول فعال باشد",
        }

        widgets = {
            "category": forms.Select(
                attrs={"class": "form-control"}
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "مثلاً تی‌شرت اسپرت",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "توضیحات محصول را وارد کنید",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "stock": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "1",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        store = kwargs.pop("store", None)
        super().__init__(*args, **kwargs)

        self.fields["category"].required = False
        self.fields["category"].empty_label = "بدون دسته‌بندی"

        if store is not None:
            self.fields["category"].queryset = Category.objects.filter(
                store=store
            )
        else:
            self.fields["category"].queryset = Category.objects.none()
