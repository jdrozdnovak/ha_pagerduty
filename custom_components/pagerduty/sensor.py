import requests
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import async_add_executor_job
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_API_TOKEN
from .const import UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the PagerDuty sensor from a config entry."""
    api_token = config_entry.data.get(CONF_API_TOKEN)
    team_id = config_entry.data.get("team_id")

    coordinator = PagerDutyDataCoordinator(hass, api_token, team_id)
    await coordinator.async_refresh()

    sensors = [PagerDutyServiceSensor(coordinator)]
    async_add_entities(sensors, False)


class PagerDutyDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, api_token, team_id):
        """Initialize the data coordinator."""
        self.api_token = api_token
        self.team_id = team_id
        self.hass = hass

        super().__init__(
            hass,
            _LOGGER,
            name="PagerDuty",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from the PagerDuty API."""

        def fetch():
            url = "https://api.pagerduty.com/services"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Token token={self.api_token}",
            }
            params = {"team_ids[]": self.team_id}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch services: {response.reason}")
            return response.json()

        try:
            return await self.hass.async_add_executor_job(fetch)
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch services: {e}")

        # Fetching services data
        services_response = requests.get(url, headers=headers, params=params)
        if services_response.status_code != 200:
            raise UpdateFailed(f"Failed to fetch services: {services_response.reason}")

        services_data = services_response.json().get("services", [])

        # Structure to hold our parsed data
        parsed_data = {}

        # For each service, fetch incidents and aggregate data
        for service in services_data:
            service_id = service.get("id")
            service_name = service.get("name")
            incidents_url = f"https://api.pagerduty.com/incidents?service_ids[]={service_id}&statuses[]=triggered&statuses[]=acknowledged"

            incidents_response = requests.get(incidents_url, headers=headers)
            if incidents_response.status_code != 200:
                raise UpdateFailed(
                    f"Failed to fetch incidents for service {service_name}: {incidents_response.reason}"
                )

            incidents_data = incidents_response.json().get("incidents", [])
            triggered_count = sum(
                1 for incident in incidents_data if incident["status"] == "triggered"
            )
            acknowledged_count = sum(
                1 for incident in incidents_data if incident["status"] == "acknowledged"
            )

            parsed_data[service_name] = {
                "triggered_incidents": triggered_count,
                "acknowledged_incidents": acknowledged_count,
            }

        return parsed_data


class PagerDutyServiceSensor(SensorEntity):
    """Representation of a PagerDuty Sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return "PagerDuty Sensor"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return "pagerduty_unique_sensor_id"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def should_poll(self):
        """If entity should be polled."""
        return False

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        # You can add extra state attributes here
        return {}
