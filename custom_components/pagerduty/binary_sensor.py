"""PagerDuty Binary Sensor for Home Assistant."""

import logging
from datetime import timedelta
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    DEVICE_CLASS_OCCUPANCY
)
from homeassistant.const import CONF_API_KEY
from pdpyras import APISession
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)  # Update every 5 minutes

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the PagerDuty binary sensor."""
    _LOGGER.debug("Setting up PagerDuty binary sensor platform")

    api_key = hass.data[DOMAIN][CONF_API_KEY]
    session = APISession(api_key)
    add_entities([PagerDutyBinarySensor(session)], True)

class PagerDutyBinarySensor(BinarySensorEntity):
    """Representation of a PagerDuty Binary Sensor."""

    def __init__(self, session):
        """Initialize the sensor."""
        _LOGGER.debug("Initializing PagerDuty binary sensor")
        self.session = session
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

        try:
            user = self.session.rget('/users/me')
            user_id = user.get('id', None)
            if user_id:
                on_calls = self.session.rget(f'/oncalls?user_ids[]={user_id}')
                self._is_on_call = bool(on_calls.get('oncalls'))
            else:
                self._is_on_call = False
            _LOGGER.debug(f"PagerDuty binary sensor state updated: {self._is_on_call}")
        except Exception as e:
            _LOGGER.error(f"Error updating PagerDuty sensor: {e}")
            self._is_on_call = False
