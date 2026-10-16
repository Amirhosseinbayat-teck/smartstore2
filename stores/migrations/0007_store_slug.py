
from django.db import migrations, models


def populate_store_slugs(apps, schema_editor):
    Store = apps.get_model("stores", "Store")
    database = schema_editor.connection.alias

    for store in Store.objects.using(database).all().order_by("id"):
        store.slug = f"store-{store.id}"
        store.save(using=database, update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("stores", "0006_storedesignhistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="store",
            name="slug",
            field=models.SlugField(
                blank=True,
                max_length=100,
                null=True,
                db_index=False,
            ),
        ),
        migrations.RunPython(
            populate_store_slugs,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="store",
            name="slug",
            field=models.SlugField(
                blank=True,
                max_length=100,
                unique=True,
                db_index=False,
            ),
        ),
    ]
