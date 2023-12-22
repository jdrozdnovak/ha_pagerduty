"""The PagerDuty integration for Home Assistant."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PagerDuty integration."""
    _LOGGER.debug("Setting up PagerDuty integration")

    if DOMAIN in hass.data:
        _LOGGER.debug("PagerDuty integration already set up")
        return True

    api_key = config[DOMAIN][CONF_API_KEY]

    _LOGGER.debug("Storing API key for PagerDuty integration")
    hass.data[DOMAIN] = {CONF_API_KEY: api_key}

    _LOGGER.debug("Loading PagerDuty binary sensor platform")
    hass.helpers.discovery.load_platform("binary_sensor", DOMAIN, {}, config)

    return True
