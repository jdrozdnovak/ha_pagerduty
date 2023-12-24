"""PagerDuty Binary Sensor for Home Assistant."""

import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    DEVICE_CLASS_OCCUPANCY,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the PagerDuty binary sensor/sensor platform."""
    coordinator = hass.data[DOMAIN]["coordinator"]

    # Create entities
    entities = [PagerDutyBinarySensor(coordinator)]

    async_add_entities(entities)


class PagerDutyBinarySensor(BinarySensorEntity, CoordinatorEntity):
    def __init__(self, coordinator):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        _LOGGER.debug("Initializing PagerDuty binary sensor")
        self._coordinator = coordinator
        self._is_on_call = False
        self._name = "PagerDuty On Call Status"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

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
