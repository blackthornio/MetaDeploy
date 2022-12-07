from unittest import mock

import pytest
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from sfdo_template_helpers.oauth2.salesforce.views import SalesforcePermissionsError

from ..views import custom_500_view, custom_permission_denied_view


@pytest.mark.django_db
@mock.patch("metadeploy.views.render")
def test_custom_permission_denied_view__sf_permissions(render):
    request = RequestFactory().get("path")
    exc = SalesforcePermissionsError("I'm sorry Dave.")
    custom_permission_denied_view(request, exc)

    assert (
        render.call_args[1]["context"]["JS_CONTEXT"]["error_message"]
        == "I'm sorry Dave."
    )


@pytest.mark.django_db
@mock.patch("metadeploy.views.render")
def test_custom_permission_denied_view__unknown_error(render):
    request = RequestFactory().get("path")
    exc = Exception("I'm sorry Dave.")
    custom_permission_denied_view(request, exc)

    assert (
        render.call_args[1]["context"]["JS_CONTEXT"]["error_message"]
        == "An internal error occurred while processing your request."
    )


@pytest.mark.django_db
@mock.patch("metadeploy.views.render")
def test_custom_500_view__ip_restricted_error(render):
    try:
        # raise this to populate info for
        # call to sys.exec_info() in the view
        raise OAuth2Error(
            'Error retrieving access token: b\'{"error":"invalid_grant","error_description":"ip restricted"}\''
        )
    except OAuth2Error:
        allow_list = "0.0.0.1, 0.0.0.2, 0.0.0.3"
        with mock.patch("metadeploy.views.IP_RESTRICTED_MESSAGE", allow_list):
            factory = RequestFactory()
            request = factory.get("/accounts/salesforce/login/callback/")
            request.user = AnonymousUser()
            custom_500_view(request)

    assert allow_list == render.call_args[1]["context"]["JS_CONTEXT"]["error_message"]
