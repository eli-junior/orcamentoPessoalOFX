from django.urls import path
from bolt import BoltRouter
from .api import app

router = BoltRouter()
router.register(app)

urlpatterns = [
    path("", router.urls),
]
