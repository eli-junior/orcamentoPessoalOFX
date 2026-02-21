import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_login_redirect_behavior():
    client = Client()
    # Access a protected view (dashboard)
    response = client.get(reverse("dashboard"))

    # Should redirect to login page, not 404
    assert response.status_code == 302

    # Check the redirect location
    # Expecting /login/?next=/dashboard/
    # If LOGIN_URL is not set, it defaults to /accounts/login/ which is 404 in this project
    assert "/login/?next=/dashboard/" in response.url
    assert "/accounts/login/" not in response.url
