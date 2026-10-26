import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Refbook",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.CharField(max_length=100, unique=True, verbose_name="Код")),
                ("name", models.CharField(max_length=300, verbose_name="Наименование")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
            ],
            options={
                "verbose_name": "Справочник",
                "verbose_name_plural": "Справочники",
                "ordering": ("id",),
            },
        ),
        migrations.CreateModel(
            name="RefbookVersion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("version", models.CharField(max_length=50, verbose_name="Версия")),
                ("start_date", models.DateField(verbose_name="Дата начала действия")),
                (
                    "refbook",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="refbooks.refbook",
                        verbose_name="Справочник",
                    ),
                ),
            ],
            options={
                "verbose_name": "Версия справочника",
                "verbose_name_plural": "Версии справочников",
                "ordering": ("refbook_id", "-start_date"),
            },
        ),
        migrations.CreateModel(
            name="RefbookElement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("code", models.CharField(max_length=100, verbose_name="Код элемента")),
                ("value", models.CharField(max_length=300, verbose_name="Значение элемента")),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="elements",
                        to="refbooks.refbookversion",
                        verbose_name="Версия",
                    ),
                ),
            ],
            options={
                "verbose_name": "Элемент справочника",
                "verbose_name_plural": "Элементы справочников",
                "ordering": ("code",),
            },
        ),
        migrations.AddConstraint(
            model_name="refbookversion",
            constraint=models.UniqueConstraint(
                fields=("refbook", "version"),
                name="unique_refbook_version",
                violation_error_message="У справочника уже есть версия с таким номером.",
            ),
        ),
        migrations.AddConstraint(
            model_name="refbookversion",
            constraint=models.UniqueConstraint(
                fields=("refbook", "start_date"),
                name="unique_refbook_start_date",
                violation_error_message="У справочника уже есть версия с такой датой начала.",
            ),
        ),
        migrations.AddConstraint(
            model_name="refbookelement",
            constraint=models.UniqueConstraint(
                fields=("version", "code"),
                name="unique_version_element_code",
                violation_error_message="В этой версии уже есть элемент с таким кодом.",
            ),
        ),
    ]
