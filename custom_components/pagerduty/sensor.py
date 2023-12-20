import logging
from pdpyras import APISession, PDClientError
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, UPDATE_INTERVAL, CONF_API_TOKEN, CONF_TEAM_ID

_LOGGER = logging.getLogger(__name__)


class PagerDutyDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the PagerDuty API."""

    def __init__(self, hass, api_token, update_interval, team_id):
        """Initialize the data coordinator."""
        _LOGGER.debug("Initializing PagerDuty Data Coordinator")
        self.session = APISession(api_token)
        self.team_id = team_id
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Fetch data from the PagerDuty API."""

        def fetch_data():
            """Fetch the data synchronously."""
            try:
                services = self.session.rget(
                    "services", params={"team_ids[]": self.team_id}
                )
                parsed_data = {}
                for service in services:
                    service_id = service["id"]
                    service_name = service["name"]
                    incidents = self.session.rget(
                        f"incidents",
                        params={
                            "service_ids[]": service_id,
                            "statuses[]": ["triggered", "acknowledged"],
                        },
                    )

                    triggered_count = sum(
                        1 for incident in incidents if incident["status"] == "triggered"
                    )
                    acknowledged_count = sum(
                        1
                        for incident in incidents
                        if incident["status"] == "acknowledged"
                    )

                    parsed_data[service_id] = {
                        "service_name": service_name,
                        "triggered_count": triggered_count,
                        "acknowledged_count": acknowledged_count,
                    }
                return parsed_data
            except PDClientError as e:
                _LOGGER.error("Error fetching data from PagerDuty: %s", e)
                raise UpdateFailed(f"Error fetching data from PagerDuty: {e}")

        return await self.hass.async_add_executor_job(fetch_data)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the PagerDuty sensor from a config entry."""
    api_token = config_entry.data.get(CONF_API_TOKEN)
    team_id = config_entry.data.get(CONF_TEAM_ID)

    coordinator = PagerDutyDataCoordinator(hass, api_token, team_id, UPDATE_INTERVAL)
    await coordinator.async_config_entry_first_refresh()

    sensors = []
    for service_id, data in coordinator.data.items():
        sensors.append(
            PagerDutyServiceSensor(coordinator, service_id, data["service_name"])
        )

    async_add_entities(sensors, False)


class PagerDutyServiceSensor(SensorEntity):
    """Representation of a PagerDuty Sensor."""

    def __init__(self, coordinator, service_id, name):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.service_id = service_id
        self._name = name

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"PagerDuty Service: {self._name}"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return f"pagerduty_{self.service_id}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        service_data = self.coordinator.data.get(self.service_id, {})
        return service_data.get("triggered_count", "Unavailable")

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        service_data = self.coordinator.data.get(self.service_id, {})
        return {
            "acknowledged_count": service_data.get("acknowledged_count", 0),
            "triggered_count": service_data.get("triggered_count", 0),
        }
