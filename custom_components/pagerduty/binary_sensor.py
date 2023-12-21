import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import STATE_ON, STATE_OFF
from .api import PagerDutyDataCoordinator
from datetime import datetime
from .const import UPDATE_INTERVAL, CONF_API_TOKEN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the PagerDuty binary sensor from a config entry."""
    api_token = config_entry.data.get(CONF_API_TOKEN)
    coordinator = PagerDutyDataCoordinator(hass, api_token, UPDATE_INTERVAL)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([PagerDutyOnCallSensor(coordinator)], False)


class PagerDutyOnCallSensor(BinarySensorEntity):
    """Representation of a PagerDuty On-Call Binary Sensor."""

    def __init__(self, coordinator):
        """Initialize the binary sensor."""
        self.coordinator = coordinator
        self._state = STATE_OFF
        self._next_on_call = None

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return "PagerDuty On-Call"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return "pagerduty_on_call_sensor"

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self._state == STATE_ON

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the binary sensor."""
        return {"next_on_call": self._next_on_call}

    async def async_update(self):
        """Update the binary sensor."""
        current_time = datetime.now()
        on_calls = self.coordinator.data.get("on_calls", [])
        self._state = STATE_OFF
        self._next_on_call = None
        for on_call in on_calls:
            start = on_call["start"]
            end = on_call["end"]
            if start <= current_time <= end:
                self._state = STATE_ON
                break
            elif start > current_time and (
                self._next_on_call is None or start < self._next_on_call
            ):
                self._next_on_call = start
