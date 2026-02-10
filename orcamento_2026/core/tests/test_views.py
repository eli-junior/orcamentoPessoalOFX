import pytest
from django.test import Client

client = Client()


@pytest.mark.djangodb
def test_home():
    global client
    response = client.get("/")
    assert response.status_code == 200
