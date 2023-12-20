import logging
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_API_TOKEN
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the PagerDuty sensor from a config entry."""
    api_token = config_entry.data.get(CONF_API_TOKEN)
    team_id = config_entry.data.get("team_id")

    session = aiohttp.ClientSession()
    coordinator = PagerDutyDataCoordinator(
        hass, session, api_token, team_id, UPDATE_INTERVAL
    )
    await coordinator.async_refresh()

    sensors = []
    for service_id in coordinator.data:
        sensors.append(PagerDutyServiceSensor(coordinator, service_id))

    async_add_entities(sensors, False)


class PagerDutyDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, session, api_token, team_id, update_interval):
        """Initialize the data coordinator."""
        self.api_token = api_token
        self.team_id = team_id
        self.session = session
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        _LOGGER.debug("Fetching data from PagerDuty API")
        """Fetch data from the PagerDuty API."""
        url = "https://api.pagerduty.com/services"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Token token={self.api_token}",
        }

        # Ensure that api_token and team_id are not None
        if self.api_token is None or self.team_id is None:
            _LOGGER.error("API token or team ID is not set.")
            raise UpdateFailed("API token or team ID is not set.")

        params = {"team_ids[]": self.team_id}

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                raise UpdateFailed(f"Failed to fetch services: {response.reason}")
            services_data = await response.json()

        parsed_data = {}
        # Process the services_data here and populate parsed_data
        # ...
        for service in services_data.get("services", []):
            service_id = service.get("id")
            service_name = service.get("name")

            # URL to fetch incidents for this service
            _LOGGER.debug("Processing service: %s", service)
            incidents_url = f"https://api.pagerduty.com/incidents?service_ids[]={service_id}&statuses[]=triggered&statuses[]=acknowledged"

            async with self.session.get(
                incidents_url, headers=headers
            ) as incidents_response:
                if incidents_response.status != 200:
                    _LOGGER.error(
                        f"Failed to fetch incidents for service {service_name}"
                    )
                    continue
                incidents_data = await incidents_response.json()

            # Count the incidents by status
            triggered_count = sum(
                1
                for incident in incidents_data.get("incidents", [])
                if incident["status"] == "triggered"
            )
            acknowledged_count = sum(
                1
                for incident in incidents_data.get("incidents", [])
                if incident["status"] == "acknowledged"
            )

            # Add the counts to the parsed data
            parsed_data[service_id] = {
                "service_name": service_name,
                "triggered_count": triggered_count,
                "acknowledged_count": acknowledged_count,
            }

        _LOGGER.debug("Parsed data: %s", parsed_data)
        return parsed_data


class PagerDutyServiceSensor(SensorEntity):
    """Representation of a PagerDuty Sensor."""

    def __init__(self, coordinator, service_id):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.service_id = service_id
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
        service_data = self.coordinator.data.get(self.service_id)
        if service_data:
            return {
                "service_name": service_data.get("service_name"),
                "acknowledged_count": service_data.get("acknowledged_count"),
            }
        return {}

    @property
    def native_value(self):
        """Return the state of the sensor."""
        service_data = self.coordinator.data.get(self.service_id, {})
        return service_data.get("triggered_count", "Unavailable")
