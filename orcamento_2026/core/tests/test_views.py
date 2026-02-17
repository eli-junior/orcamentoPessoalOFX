import pytest
from django.test import Client

client = Client()


@pytest.mark.django_db
def test_home():
    global client
    response = client.get("/")
    assert response.status_code == 200
