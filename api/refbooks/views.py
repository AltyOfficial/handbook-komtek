from datetime import date

from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.refbooks.models import Refbook, RefbookElement

from .serializers import (
    CheckElementResponseSerializer,
    ElementsResponseSerializer,
    ErrorSerializer,
    RefbookListResponseSerializer,
)

TAG = "Справочники"

ID_PARAM = OpenApiParameter(
    "refbook_id",
    OpenApiTypes.INT,
    OpenApiParameter.PATH,
    description="Идентификатор справочника",
)
VERSION_PARAM = OpenApiParameter(
    "version",
    OpenApiTypes.STR,
    OpenApiParameter.QUERY,
    required=False,
    description=(
        "Версия справочника. Если не указана, используется текущая версия: "
        "версия с самой поздней датой начала действия, не позже текущей даты."
    ),
    examples=[OpenApiExample("Версия", value="1.0")],
)


def _parse_date(value: str) -> date:
    parsed_date = parse_date(value)
    if parsed_date is None or parsed_date.isoformat() != value:
        raise ValidationError({"date": "Неверный формат даты, ожидается ГГГГ-ММ-ДД."})
    return parsed_date


def _resolve_version(refbook: Refbook, version: str | None):
    resolved_version = refbook.get_version(version)
    if resolved_version is None:
        if version:
            raise NotFound(f"Версия «{version}» справочника не найдена.")
        raise NotFound("У справочника нет текущей версии.")
    return resolved_version


class RefbookViewSet(viewsets.GenericViewSet):
    queryset = Refbook.objects.all()
    lookup_url_kwarg = "refbook_id"

    @extend_schema(
        tags=[TAG],
        summary="Список справочников",
        description=(
            "Возвращает список справочников. Если указан параметр `date`, возвращаются "
            "справочники хотя бы с одной версией, действующей на указанную дату."
        ),
        parameters=[
            OpenApiParameter(
                "date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=False,
                description="Дата в формате ГГГГ-ММ-ДД",
                examples=[OpenApiExample("Дата", value="2022-10-01")],
            )
        ],
        responses={200: RefbookListResponseSerializer, 400: ErrorSerializer},
        examples=[
            OpenApiExample(
                "Пример ответа",
                value={
                    "refbooks": [
                        {"id": "1", "code": "MS1", "name": "Специальности медицинских работников"},
                        {"id": "2", "code": "ICD-10", "name": "МКБ-10"},
                    ]
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        if "date" in request.query_params:
            effective_date = _parse_date(request.query_params["date"])
            queryset = queryset.filter(versions__start_date__lte=effective_date).distinct()
        data = RefbookListResponseSerializer({"refbooks": queryset}).data
        return Response(data)

    @extend_schema(
        tags=[TAG],
        summary="Элементы справочника",
        description="Возвращает элементы указанной версии справочника (по умолчанию — текущей).",
        parameters=[ID_PARAM, VERSION_PARAM],
        responses={200: ElementsResponseSerializer, 404: ErrorSerializer},
        examples=[
            OpenApiExample(
                "Пример ответа",
                value={
                    "elements": [
                        {"code": "J00", "value": "Острый назофарингит (насморк)"},
                        {"code": "J01", "value": "Острый синусит"},
                    ]
                },
                response_only=True,
                status_codes=["200"],
            )
        ],
    )
    @action(detail=True, methods=["get"], url_path="elements", url_name="elements")
    def elements(self, request, refbook_id=None):
        refbook = self.get_object()
        version = _resolve_version(refbook, request.query_params.get("version"))
        data = ElementsResponseSerializer({"elements": version.elements.all()}).data
        return Response(data)

    @extend_schema(
        tags=[TAG],
        summary="Валидация элемента справочника",
        description=(
            "Проверяет, что элемент с данным кодом и значением присутствует в указанной "
            "версии справочника (по умолчанию — в текущей)."
        ),
        parameters=[
            ID_PARAM,
            OpenApiParameter(
                "code",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Код элемента",
                examples=[OpenApiExample("Код", value="J00")],
            ),
            OpenApiParameter(
                "value",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                description="Значение элемента",
                examples=[OpenApiExample("Значение", value="Острый назофарингит (насморк)")],
            ),
            VERSION_PARAM,
        ],
        responses={
            200: CheckElementResponseSerializer,
            400: ErrorSerializer,
            404: ErrorSerializer,
        },
        examples=[
            OpenApiExample(
                "Элемент найден",
                value={"valid": True},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Элемент не найден",
                value={"valid": False},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    @action(detail=True, methods=["get"], url_path="check_element", url_name="check-element")
    def check_element(self, request, refbook_id=None):
        code = request.query_params.get("code")
        value = request.query_params.get("value")
        errors = {
            name: "Обязательный параметр."
            for name, param_value in (("code", code), ("value", value))
            if param_value is None
        }
        if errors:
            raise ValidationError(errors)

        refbook = self.get_object()
        version = _resolve_version(refbook, request.query_params.get("version"))
        is_valid = RefbookElement.objects.filter(
            version=version,
            code=code,
            value=value,
        ).exists()
        return Response({"valid": is_valid})
