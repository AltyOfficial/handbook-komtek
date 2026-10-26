from rest_framework.routers import SimpleRouter

from .views import RefbookViewSet

router = SimpleRouter()
router.trailing_slash = "/?"
router.register("refbooks", RefbookViewSet, basename="refbook")

urlpatterns = router.urls
