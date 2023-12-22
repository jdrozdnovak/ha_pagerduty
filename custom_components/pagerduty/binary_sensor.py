"""PagerDuty Binary Sensor for Home Assistant."""

import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    DEVICE_CLASS_OCCUPANCY,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the PagerDuty binary sensor."""
    _LOGGER.debug("Setting up PagerDuty binary sensor platform")

    coordinator = hass.data[DOMAIN]["coordinator"]
    add_entities([PagerDutyBinarySensor(coordinator)], True)


class PagerDutyBinarySensor(BinarySensorEntity, CoordinatorEntity):
    """Representation of a PagerDuty Binary Sensor."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        _LOGGER.debug("Initializing PagerDuty binary sensor")
        super().__init__(coordinator)
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

    @property
    def device_class(self):
        """Return the class of this device."""
        return DEVICE_CLASS_OCCUPANCY

    def update(self):
        """Fetch new state data for the sensor."""
        _LOGGER.debug("Updating PagerDuty binary sensor state")

        on_calls = self.coordinator.data.get("on_calls", [])
        self._is_on_call = bool(on_calls)
        _LOGGER.debug(f"Binary sensor on-call status: {self._is_on_call}")
