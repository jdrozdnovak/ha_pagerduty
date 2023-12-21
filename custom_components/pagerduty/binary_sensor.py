import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import STATE_ON, STATE_OFF
from .api import PagerDutyDataCoordinator
from datetime import datetime
from .const import UPDATE_INTERVAL, CONF_API_TOKEN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the PagerDuty binary sensor from a config entry."""
    _LOGGER.debug("Setting up PagerDuty binary sensor")
    api_token = config_entry.data.get(CONF_API_TOKEN)
    coordinator = PagerDutyDataCoordinator(hass, api_token, UPDATE_INTERVAL)
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([PagerDutyOnCallSensor(coordinator)], False)
    _LOGGER.debug("PagerDuty binary sensor setup complete")


class PagerDutyOnCallSensor(BinarySensorEntity):
    """Representation of a PagerDuty On-Call Binary Sensor."""

    def __init__(self, coordinator):
        """Initialize the binary sensor."""
        _LOGGER.debug("Initializing PagerDuty On-Call Binary Sensor")
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

    async def async_update(self):
        """Update the binary sensor."""
        _LOGGER.debug("Updating PagerDuty On-Call Binary Sensor")
        self._state = STATE_ON if self.coordinator.data else STATE_OFF
        _LOGGER.debug(
            f"PagerDuty On-Call Binary Sensor state updated to: {'ON' if self._state == STATE_ON else 'OFF'}"
        )
