"""PagerDuty Binary Sensor for Home Assistant."""

import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the PagerDuty binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    user_id = coordinator.data.get("user_id", "")

    async_add_entities([PagerDutyBinarySensor(coordinator, user_id)])


class PagerDutyBinarySensor(BinarySensorEntity, CoordinatorEntity):
    def __init__(self, coordinator, user_id):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        _LOGGER.debug("Initializing PagerDuty binary sensor")
        self._coordinator = coordinator
        self._is_on_call = None
        self._attr_name = "PagerDuty On Call Status"
        self._attr_unique_id = f"pd_oncall_{user_id}"

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        last_state = await self.async_get_last_state()
        if last_state:
            self._is_on_call = last_state.state == "on"

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._is_on_call

    def _handle_coordinator_update(self):
        """Fetch new state data for the sensor."""
        _LOGGER.debug("Updating PagerDuty binary sensor state")

        on_calls = self._coordinator.data.get("on_calls", [])
        self._is_on_call = bool(on_calls)

        _LOGGER.debug(f"Binary sensor on-call status: {self._is_on_call}")

        super()._handle_coordinator_update()
