import logging
from pdpyras import APISession, EventsAPISession, PDClientError
import voluptuous as vol
from homeassistant.components.notify import (
    BaseNotificationService,
    PLATFORM_SCHEMA,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "pagerduty"
CONF_SERVICE_ID = "service_id"
CONF_API_KEY = "api_key"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SERVICE_ID): cv.string,
    }
)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> PagerDutyNotificationService | None:
    """Get the PagerDuty notification service."""
    if discovery_info is None:
        return None

    service_id = discovery_info[CONF_SERVICE_ID]
    api_key = hass.data[DOMAIN][CONF_API_KEY]  # Ensure this is stored correctly
    session = APISession(api_key)

    integration_key = await hass.async_add_executor_job(
        get_integration_key, session, service_id
    )
    if integration_key:
        return PagerDutyNotificationService(integration_key)

    _LOGGER.error("Failed to retrieve PagerDuty integration key")
    return None


def get_integration_key(session, service_id):
    """Retrieve or create integration key for the given service."""
    integrations = session.rget(f"/services/{service_id}/integrations")

    for integration in integrations:
        if integration["type"] == "events_api_v2_inbound_integration":
            integration_id = integration["id"]
            integration_details = session.rget(f"/integrations/{integration_id}")
            return integration_details.get("integration_key")

    new_integration = {
        "type": "events_api_v2_inbound_integration",
        "name": "Home Assistant Integration",
    }
    created_integration = session.rpost(
        f"/services/{service_id}/integrations", json=new_integration
    )
    return created_integration.get("integration_key")


class PagerDutyNotificationService(BaseNotificationService):
    def __init__(self, integration_key):
        """Initialize the service."""
        self.integration_key = integration_key

    def send_message(self, message="", **kwargs):
        """Send a message to PagerDuty."""
        session = EventsAPISession(self.integration_key)
        payload = {
            "summary": message,
            "source": "Home Assistant",
            "severity": "info",
        }
        try:
            session.trigger_incident(payload)
            _LOGGER.debug("Sent notification to PagerDuty")
        except PDClientError as e:
            _LOGGER.error("Failed to send notification to PagerDuty: %s", e)
