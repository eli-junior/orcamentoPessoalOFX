import pytest
from django.test import Client


@pytest.mark.django_db
def test_home_redirects_to_login_if_not_authenticated():
    client = Client()
    response = client.get("/")
    assert response.status_code == 302
    assert response.url == "/login/?next=/"
