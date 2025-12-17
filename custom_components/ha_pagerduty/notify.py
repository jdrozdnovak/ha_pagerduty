import logging
from pagerduty import RestApiV2Client, EventsApiV2Client, Error
from homeassistant.components.notify import BaseNotificationService
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_API_KEY = "api_key"


async def async_get_service(hass, config, discovery_info=None):
    """Get the PagerDuty notification service."""
    if discovery_info is None:
        return None

    api_key = discovery_info[CONF_API_KEY]
    api_base_url = discovery_info.get("api_base_url")

    session = RestApiV2Client(api_key)
    session.url = api_base_url
    return PagerDutyNotificationService(session, api_base_url)


class PagerDutyNotificationService(BaseNotificationService):
    def __init__(self, session, api_base_url):
        """Initialize the service."""
        self.session = session
        self.api_base_url = api_base_url

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
            if self.api_base_url == "https://api.pagerduty.com"
            else "https://events.eu.pagerduty.com"
        )
        event_session = EventsApiV2Client(integration_key)
        event_session.url = events_api_base_url

        source = "Home Assistant"

        try:
            event_session.trigger(message, source)
            _LOGGER.debug("Sent notification to PagerDuty")
        except Error as e:
            _LOGGER.error(f"Failed to send notification to PagerDuty: {e}")


def get_integration_key(session, service_id):
    """Retrieve or create integration key for the given service."""
    _LOGGER.debug(f"Retrieving integrations for service ID: {service_id}")
    service_details = session.rget(f"/services/{service_id}")
    _LOGGER.debug(f"Service details received: {service_details}")
    integrations = service_details.get("integrations", [])
    _LOGGER.debug(f"Integrations in service: {integrations}")

    for integration in integrations:
        if "events_api_v2_inbound_integration" in integration["type"]:
            integration_id = integration["id"]
            integration_details = session.rget(
                f"/services/{service_id}/integrations/{integration_id}"
            )
            _LOGGER.debug(f"Integration details: {integration_details}")
            return integration_details.get("integration_key")

    new_integration = {
        "type": "events_api_v2_inbound_integration",
        "name": "Home Assistant Integration",
    }
    created_integration = session.rpost(
        f"/services/{service_id}/integrations", json=new_integration
    )
    _LOGGER.debug(f"Created new integration: {created_integration}")
    return created_integration.get("integration_key")
