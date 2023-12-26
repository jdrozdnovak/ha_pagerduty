"""The PagerDuty integration for Home Assistant."""

import logging
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN, UPDATE_INTERVAL
from pdpyras import APISession
from .coordinator import PagerDutyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PagerDuty integration."""
    _LOGGER.debug("Setting up PagerDuty integration")

    if DOMAIN not in config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )

    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up PagerDuty from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    update_interval = entry.options.get("update_interval", UPDATE_INTERVAL)

    session = APISession(api_key)
    coordinator = PagerDutyDataUpdateCoordinator(hass, session, update_interval)

    # Perform the first update with custom handling for initial setup
    await coordinator.async_first_config_entry()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_setup(entry, platform)

    return True
