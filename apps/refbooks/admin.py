from django.contrib import admin

from .models import Refbook, RefbookElement, RefbookVersion

admin.site.site_header = "Сервис терминологии"
admin.site.site_title = "Сервис терминологии"
admin.site.index_title = "Администрирование"


class RefbookVersionInline(admin.TabularInline):
    model = RefbookVersion
    extra = 0
    fields = ("version", "start_date")
    show_change_link = True


class RefbookElementInline(admin.TabularInline):
    model = RefbookElement
    extra = 0
    fields = ("code", "value")


@admin.register(Refbook)
class RefbookAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "current_version", "current_version_start_date")
    search_fields = ("code", "name")
    inlines = (RefbookVersionInline,)

    @admin.display(description="Текущая версия")
    def current_version(self, obj):
        version = obj.get_current_version()
        return version.version if version else "—"

    @admin.display(description="Дата начала действия версии")
    def current_version_start_date(self, obj):
        version = obj.get_current_version()
        return version.start_date if version else "—"


@admin.register(RefbookVersion)
class RefbookVersionAdmin(admin.ModelAdmin):
    list_display = ("refbook_code", "refbook_name", "version", "start_date")
    list_select_related = ("refbook",)
    list_filter = ("refbook",)
    search_fields = ("refbook__code", "refbook__name", "version")
    inlines = (RefbookElementInline,)

    @admin.display(description="Код справочника", ordering="refbook__code")
    def refbook_code(self, obj):
        return obj.refbook.code

    @admin.display(description="Наименование справочника", ordering="refbook__name")
    def refbook_name(self, obj):
        return obj.refbook.name


@admin.register(RefbookElement)
class RefbookElementAdmin(admin.ModelAdmin):
    list_display = ("code", "value", "version")
    list_select_related = ("version__refbook",)
    list_filter = ("version__refbook",)
    search_fields = ("code", "value")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["version"].queryset = RefbookVersion.objects.select_related("refbook")
        return form
