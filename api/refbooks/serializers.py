from rest_framework import serializers

from apps.refbooks.models import Refbook, RefbookElement


class RefbookSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Refbook
        fields = ("id", "code", "name")


class RefbookListResponseSerializer(serializers.Serializer):
    refbooks = RefbookSerializer(many=True)


class ElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefbookElement
        fields = ("code", "value")


class ElementsResponseSerializer(serializers.Serializer):
    elements = ElementSerializer(many=True)


class CheckElementResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()
