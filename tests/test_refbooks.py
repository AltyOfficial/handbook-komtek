import datetime

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import resolve
from django.utils import timezone
from rest_framework.test import APIClient

from apps.refbooks.models import Refbook, RefbookElement, RefbookVersion

TODAY = timezone.localdate()


def days(n):
    return TODAY + datetime.timedelta(days=n)


class BaseApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.rb = Refbook.objects.create(code="MS1", name="Специальности")
        self.v1 = RefbookVersion.objects.create(
            refbook=self.rb, version="1.0", start_date=days(-100)
        )
        self.v2 = RefbookVersion.objects.create(
            refbook=self.rb, version="2.0", start_date=days(-10)
        )
        self.v3 = RefbookVersion.objects.create(refbook=self.rb, version="3.0", start_date=days(10))
        RefbookElement.objects.create(version=self.v1, code="1", value="Терапевт (старое)")
        RefbookElement.objects.create(version=self.v2, code="1", value="Врач-терапевт")
        RefbookElement.objects.create(version=self.v2, code="2", value="Хирург")
        RefbookElement.objects.create(version=self.v3, code="1", value="Терапевт (будущее)")

        self.future_rb = Refbook.objects.create(code="FUT", name="Будущий")
        RefbookVersion.objects.create(refbook=self.future_rb, version="1.0", start_date=days(30))


class RefbookListTests(BaseApiTest):
    def test_list_without_date_returns_all(self):
        response = self.client.get("/refbooks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["refbooks"]), 2)

    def test_response_format(self):
        item = self.client.get("/refbooks/").json()["refbooks"][0]
        self.assertEqual(item, {"id": str(self.rb.id), "code": "MS1", "name": "Специальности"})

    def test_date_filter(self):
        response = self.client.get("/refbooks/", {"date": days(0).isoformat()})
        codes = [r["code"] for r in response.json()["refbooks"]]
        self.assertEqual(codes, ["MS1"])

    def test_date_is_inclusive(self):
        response = self.client.get("/refbooks/", {"date": days(30).isoformat()})
        self.assertEqual(len(response.json()["refbooks"]), 2)

    def test_date_before_any_version(self):
        response = self.client.get("/refbooks/", {"date": days(-200).isoformat()})
        self.assertEqual(response.json(), {"refbooks": []})

    def test_no_duplicates_when_several_versions_match(self):
        response = self.client.get("/refbooks/", {"date": days(100).isoformat()})
        codes = [r["code"] for r in response.json()["refbooks"]]
        self.assertEqual(sorted(codes), ["FUT", "MS1"])

    def test_invalid_date(self):
        response = self.client.get("/refbooks/", {"date": "01.10.2022"})
        self.assertEqual(response.status_code, 400)
        compact_date_response = self.client.get("/refbooks/", {"date": "20221001"})
        self.assertEqual(compact_date_response.status_code, 400)


class ElementsTests(BaseApiTest):
    def codes_values(self, response):
        return {e["code"]: e["value"] for e in response.json()["elements"]}

    def test_current_version_by_default(self):
        response = self.client.get(f"/refbooks/{self.rb.id}/elements")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.codes_values(response), {"1": "Врач-терапевт", "2": "Хирург"})

    def test_trailing_slash_supported(self):
        response = self.client.get(f"/refbooks/{self.rb.id}/elements/")
        self.assertEqual(response.status_code, 200)

    def test_explicit_version(self):
        response = self.client.get(f"/refbooks/{self.rb.id}/elements", {"version": "1.0"})
        self.assertEqual(self.codes_values(response), {"1": "Терапевт (старое)"})

    def test_explicit_future_version_is_allowed(self):
        response = self.client.get(f"/refbooks/{self.rb.id}/elements", {"version": "3.0"})
        self.assertEqual(self.codes_values(response), {"1": "Терапевт (будущее)"})

    def test_unknown_refbook(self):
        self.assertEqual(self.client.get("/refbooks/9999/elements").status_code, 404)

    def test_unknown_version(self):
        response = self.client.get(f"/refbooks/{self.rb.id}/elements", {"version": "9.9"})
        self.assertEqual(response.status_code, 404)

    def test_no_current_version(self):
        response = self.client.get(f"/refbooks/{self.future_rb.id}/elements")
        self.assertEqual(response.status_code, 404)


class CheckElementTests(BaseApiTest):
    def check(self, **params):
        return self.client.get(f"/refbooks/{self.rb.id}/check_element", params)

    def test_valid_element_in_current_version(self):
        response = self.check(code="1", value="Врач-терапевт")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"valid": True})

    def test_wrong_value(self):
        self.assertEqual(self.check(code="1", value="Другое").json(), {"valid": False})

    def test_wrong_code(self):
        self.assertEqual(self.check(code="77", value="Врач-терапевт").json(), {"valid": False})

    def test_current_version_is_used_by_default(self):
        # значение из старой версии в текущей не существует
        self.assertEqual(self.check(code="1", value="Терапевт (старое)").json(), {"valid": False})

    def test_explicit_version(self):
        response = self.check(code="1", value="Терапевт (старое)", version="1.0")
        self.assertEqual(response.json(), {"valid": True})

    def test_missing_params(self):
        self.assertEqual(self.check(code="1").status_code, 400)
        self.assertEqual(self.check(value="x").status_code, 400)

    def test_unknown_refbook(self):
        response = self.client.get("/refbooks/9999/check_element", {"code": "1", "value": "x"})
        self.assertEqual(response.status_code, 404)

    def test_unknown_version(self):
        self.assertEqual(self.check(code="1", value="x", version="9.9").status_code, 404)


class ModelConstraintTests(TestCase):
    def setUp(self):
        self.rb = Refbook.objects.create(code="A", name="A")
        self.version = RefbookVersion.objects.create(
            refbook=self.rb, version="1.0", start_date=days(0)
        )

    def assert_integrity_error(self, func, **kwargs):
        with self.assertRaises(IntegrityError), transaction.atomic():
            func(**kwargs)

    def test_refbook_code_unique(self):
        self.assert_integrity_error(Refbook.objects.create, code="A", name="Другой")

    def test_version_unique_per_refbook(self):
        self.assert_integrity_error(
            RefbookVersion.objects.create, refbook=self.rb, version="1.0", start_date=days(5)
        )

    def test_start_date_unique_per_refbook(self):
        self.assert_integrity_error(
            RefbookVersion.objects.create, refbook=self.rb, version="2.0", start_date=days(0)
        )

    def test_same_version_allowed_in_other_refbook(self):
        other = Refbook.objects.create(code="B", name="B")
        RefbookVersion.objects.create(refbook=other, version="1.0", start_date=days(0))

    def test_element_code_unique_per_version(self):
        RefbookElement.objects.create(version=self.version, code="1", value="x")
        self.assert_integrity_error(
            RefbookElement.objects.create, version=self.version, code="1", value="y"
        )


class SwaggerTests(TestCase):
    def test_schema_and_docs_available(self):
        self.assertEqual(self.client.get("/api/schema/").status_code, 200)
        self.assertEqual(self.client.get("/api/docs/").status_code, 200)


class RouterTests(TestCase):
    def test_router_names_resolve_to_refbook_endpoints(self):
        self.assertEqual(resolve("/refbooks/").url_name, "refbook-list")
        self.assertEqual(resolve("/refbooks/1/elements/").url_name, "refbook-elements")
        self.assertEqual(
            resolve("/refbooks/1/check_element/").url_name,
            "refbook-check-element",
        )

    def test_refbook_endpoints_are_read_only(self):
        self.assertEqual(self.client.post("/refbooks/").status_code, 405)


class AdminTests(TestCase):
    def test_admin_login_uses_russian_site_title(self):
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сервис терминологии")
