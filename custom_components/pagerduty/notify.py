import logging
from pdpyras import APISession, EventsAPISession, PDClientError
from homeassistant.components.notify import BaseNotificationService
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_API_KEY = "api_key"


async def async_get_service(hass, config, discovery_info=None):
    """Get the PagerDuty notification service."""
    if discovery_info is None:
        return None

    api_key = discovery_info["api_key"]
    api_base_url = hass.data.get("api_base_url")

    session = APISession(api_key)
    session.url = api_base_url
    return PagerDutyNotificationService(session)


class PagerDutyNotificationService(BaseNotificationService):
    def __init__(self, session):
        """Initialize the service."""
        self.session = session

    def send_message(self, message="", **kwargs):
        """Send a message to PagerDuty."""
        service_id = kwargs.get("data", {}).get("service_id")
        if not service_id:
            _LOGGER.error(
                "Service ID not provided for PagerDuty notification."
            )
            return

        integration_key = get_integration_key(self.session, service_id)
        if not integration_key:
            _LOGGER.error(
                f"Failed to retrieve PagerDuty integration key for service_id: {service_id}"
            )
            return

        events_api_base_url = (
            "https://events.pagerduty.com"
            if self.session.api_base_url == "https://api.pagerduty.com"
            else "https://events.eu.pagerduty.com"
        )
        event_session = EventsAPISession(integration_key)
        event_session.url = events_api_base_url

        source = "Home Assistant"

        try:
            event_session.trigger(message, source)
            _LOGGER.debug("Sent notification to PagerDuty")
        except PDClientError as e:
            _LOGGER.error(f"Failed to send notification to PagerDuty: {e}")


def get_integration_key(session, service_id):
    """Retrieve or create integration key for the given service."""
    _LOGGER.debug(f"Retrieving integrations for service ID: {service_id}")
    service_details = session.rget(f"/services/{service_id}")
    _LOGGER.debug(f"Service details received: {service_details}")
    integrations = service_details.get("integrations", [])
    _LOGGER.debug(f"Integrations in service: {integrations}")
    homeassistant_integration_name = "Home Assistant Integration"

    for integration in integrations:
        if (
            integration["type"] == "events_api_v2_inbound_integration"
            and integration["summary"] == homeassistant_integration_name
        ):
            integration_id = integration["id"]
            integration_details = session.rget(
                f"/services/{service_id}/integrations/{integration_id}"
            )
            _LOGGER.debug(f"Integration details: {integration_details}")
            return integration_details.get("integration_key")

    new_integration = {
        "type": "events_api_v2_inbound_integration",
        "name": homeassistant_integration_name,
    }
    created_integration = session.rpost(
        f"/services/{service_id}/integrations", json=new_integration
    )
    _LOGGER.debug(f"Created new integration: {created_integration}")
    return created_integration.get("integration_key")
