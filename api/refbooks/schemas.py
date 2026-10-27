from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter

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

NOT_FOUND_VERSION_EXAMPLE = OpenApiExample(
    "Версия не найдена",
    value={"detail": "Версия «9.9» справочника не найдена."},
    response_only=True,
    status_codes=["404"],
)
NOT_FOUND_REFBOOK_EXAMPLE = OpenApiExample(
    "Справочник не найден",
    value={"detail": "Не найдено."},
    response_only=True,
    status_codes=["404"],
)

list_schema = {
    "tags": [TAG],
    "summary": "Получение списка справочников",
    "description": (
        "Возвращает список справочников.\n\n"
        "Если указан параметр `date`, возвращаются только те справочники, "
        "в которых есть версия с датой начала действия раньше или равной указанной дате. "
        "Без параметра возвращаются все справочники."
    ),
    "parameters": [
        OpenApiParameter(
            "date",
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=False,
            description="Дата в формате ГГГГ-ММ-ДД",
            examples=[OpenApiExample("Дата", value="2022-10-01")],
        )
    ],
    "responses": {
        200: RefbookListResponseSerializer,
        400: ErrorSerializer,
    },
    "examples": [
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
        ),
        OpenApiExample(
            "Неверный формат даты",
            value={"date": "Неверный формат даты, ожидается ГГГГ-ММ-ДД."},
            response_only=True,
            status_codes=["400"],
        ),
    ],
}

elements_schema = {
    "tags": [TAG],
    "summary": "Получение элементов справочника",
    "description": (
        "Возвращает элементы заданного справочника.\n\n"
        "Если параметр `version` не указан, возвращаются элементы текущей версии: "
        "той, дата начала действия которой позже всех остальных версий справочника, "
        "но не позже текущей даты."
    ),
    "parameters": [ID_PARAM, VERSION_PARAM],
    "responses": {
        200: ElementsResponseSerializer,
        404: ErrorSerializer,
    },
    "examples": [
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
        ),
        NOT_FOUND_REFBOOK_EXAMPLE,
        NOT_FOUND_VERSION_EXAMPLE,
    ],
}

check_element_schema = {
    "tags": [TAG],
    "summary": "Валидация элемента справочника",
    "description": (
        "Проверяет, что элемент с данным кодом и значением присутствует "
        "в указанной версии справочника.\n\n"
        "Если параметр `version` не указан, проверка выполняется в текущей версии. "
        "В ответе поле `valid` равно `true`, если элемент найден, и `false`, если нет."
    ),
    "parameters": [
        ID_PARAM,
        OpenApiParameter(
            "code",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            description="Код элемента справочника",
            examples=[OpenApiExample("Код", value="J00")],
        ),
        OpenApiParameter(
            "value",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            required=True,
            description="Значение элемента справочника",
            examples=[OpenApiExample("Значение", value="Острый назофарингит (насморк)")],
        ),
        VERSION_PARAM,
    ],
    "responses": {
        200: CheckElementResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    },
    "examples": [
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
        OpenApiExample(
            "Не указан обязательный параметр",
            value={"code": "Обязательный параметр."},
            response_only=True,
            status_codes=["400"],
        ),
        NOT_FOUND_REFBOOK_EXAMPLE,
        NOT_FOUND_VERSION_EXAMPLE,
    ],
}
