from datetime import date

from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.refbooks.models import Refbook, RefbookElement

from .schemas import check_element_schema, elements_schema, list_schema 
from .serializers import (
    ElementsResponseSerializer,
    RefbookListResponseSerializer,
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

    @extend_schema(**list_schema)
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        if "date" in request.query_params:
            effective_date = _parse_date(request.query_params["date"])
            queryset = queryset.filter(versions__start_date__lte=effective_date).distinct()
        data = RefbookListResponseSerializer({"refbooks": queryset}).data
        return Response(data)

    @extend_schema(**elements_schema)
    @action(detail=True, methods=["get"], url_path="elements", url_name="elements")
    def elements(self, request, refbook_id=None):
        refbook = self.get_object()
        version = _resolve_version(refbook, request.query_params.get("version"))
        data = ElementsResponseSerializer({"elements": version.elements.all()}).data
        return Response(data)

    @extend_schema(**check_element_schema)
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
