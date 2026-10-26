from django.db import models
from django.utils import timezone


class Refbook(models.Model):
    code = models.CharField("Код", max_length=100, unique=True)
    name = models.CharField("Наименование", max_length=300)
    description = models.TextField("Описание", blank=True)

    class Meta:
        ordering = ("id",)
        verbose_name = "Справочник"
        verbose_name_plural = "Справочники"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def get_current_version(self, on_date=None):
        effective_date = on_date or timezone.localdate()
        return self.versions.filter(start_date__lte=effective_date).order_by("-start_date").first()

    def get_version(self, version=None):
        if version:
            return self.versions.filter(version=version).first()
        return self.get_current_version()


class RefbookVersion(models.Model):
    refbook = models.ForeignKey(
        Refbook,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name="Справочник",
    )
    version = models.CharField("Версия", max_length=50)
    start_date = models.DateField("Дата начала действия")

    class Meta:
        ordering = ("refbook_id", "-start_date")
        verbose_name = "Версия справочника"
        verbose_name_plural = "Версии справочников"
        constraints = [
            models.UniqueConstraint(
                fields=("refbook", "version"),
                name="unique_refbook_version",
            ),
            models.UniqueConstraint(
                fields=("refbook", "start_date"),
                name="unique_refbook_start_date",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.refbook.code} — {self.version}"


class RefbookElement(models.Model):
    version = models.ForeignKey(
        RefbookVersion,
        on_delete=models.CASCADE,
        related_name="elements",
        verbose_name="Версия",
    )
    code = models.CharField("Код элемента", max_length=100)
    value = models.CharField("Значение элемента", max_length=300)

    class Meta:
        ordering = ("code",)
        verbose_name = "Элемент справочника"
        verbose_name_plural = "Элементы справочников"
        constraints = [
            models.UniqueConstraint(
                fields=("version", "code"),
                name="unique_version_element_code",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.value}"
