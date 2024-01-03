"""The PagerDuty integration for Home Assistant."""

import logging
from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_KEY, Platform, CONF_NAME
from homeassistant.helpers import (
    discovery,
    config_validation,
    typing,
)
from datetime import timedelta
from .const import DOMAIN
from pdpyras import APISession
from .coordinator import PagerDutyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]
CONFIG_SCHEMA = config_validation.config_entry_only_config_schema(DOMAIN)
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup(hass: HomeAssistant, config: typing.ConfigType) -> bool:
    """Set up the PagerDuty integration."""
    _LOGGER.debug("Setting up PagerDuty integration")
    _LOGGER.debug(f"Configuration data: {config}")

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
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up PagerDuty from a config entry."""

    _LOGGER.debug(f"Setting up config entry: {entry}")

    api_key = entry.data[CONF_API_KEY]
    ignored_team_ids = entry.data.get("ignored_team_ids", "")
    api_base_url = entry.data.get("api_base_url")
    session = APISession(api_key)
    session.url = api_base_url

    _LOGGER.debug(f"Ignored team IDs: {ignored_team_ids}")
    _LOGGER.debug(f"API base URL: {api_base_url}")

    coordinator = PagerDutyDataUpdateCoordinator(
        hass, session, ignored_team_ids
    )

    await coordinator.async_first_config_entry()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {
                CONF_NAME: DOMAIN,
                CONF_API_KEY: api_key,
                "api_base_url": api_base_url,
            },
            entry.data,
        )
    )

    return True
