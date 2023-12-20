import logging
import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_API_TOKEN
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    api_token = config_entry.data.get(CONF_API_TOKEN)
    team_id = config_entry.data.get("team_id")

    session = aiohttp.ClientSession()
    coordinator = PagerDutyDataCoordinator(
        hass, session, api_token, team_id, UPDATE_INTERVAL
    )
    await coordinator.async_refresh()

    sensors = [PagerDutyServiceSensor(coordinator)]
    async_add_entities(sensors, False)


class PagerDutyDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, session, api_token, team_id, update_interval):
        self.api_token = api_token
        self.team_id = team_id
        self.session = session
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        url = "https://api.pagerduty.com/services"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Token token={self.api_token}",
        }
        params = {"team_ids[]": self.team_id}

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                raise UpdateFailed(f"Failed to fetch services: {response.reason}")
            return await response.json()


class PagerDutyServiceSensor(SensorEntity):
    def __init__(self, coordinator):
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
