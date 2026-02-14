from django_bolt import BoltAPI
from orcamento_2026.core.api import api as core_api

api = BoltAPI()
api.mount("/api/v1", core_api)
