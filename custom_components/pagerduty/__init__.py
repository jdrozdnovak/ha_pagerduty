"""The PagerDuty integration for Home Assistant."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN
from .coordinator import PagerDutyDataUpdateCoordinator
from pdpyras import APISession

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PagerDuty integration."""
    _LOGGER.debug("Setting up PagerDuty integration")

    if DOMAIN in hass.data:
        _LOGGER.debug("PagerDuty integration already set up")
        return True

    api_key = config[DOMAIN][CONF_API_KEY]

    # Create and initialize the DataUpdateCoordinator
    session = APISession(api_key)
    coordinator = PagerDutyDataUpdateCoordinator(hass, session)
    await coordinator.async_refresh()

    # Storing coordinator and session in hass.data
    hass.data[DOMAIN] = {
        "coordinator": coordinator,
        "session": session,
    }

    # Load binary sensor and sensor platforms
    _LOGGER.debug("Loading PagerDuty platforms")
    hass.helpers.discovery.load_platform("binary_sensor", DOMAIN, {}, config)
    # hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)

    return True
